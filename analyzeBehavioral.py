#!/usr/bin/env python3
import os
import subprocess
import re
import matplotlib.pyplot as plt
from enum import Enum, auto
from itertools import groupby
import seaborn
import math

class ImageTypes(Enum):
    Reward = "Reward"
    Control = "Control"

class DoorStates(Enum):
    High, Low = auto(), auto()

class PumpStates(Enum):
    On, Off = auto(), auto()

class Activity(Enum):
    Running, Poking = auto(), auto()

class Mouse:

    def __init__(self, cageNum, rotation_intervals, poke_events):
        self._cageNum = cageNum
        self._rotation_intervals = rotation_intervals
        self._poke_events = poke_events

    @property
    def rotation_intervals(self):
        return self._rotation_intervals
    
    @property
    def poke_events(self):
        return self._poke_events
    

class RotationInterval:
    #continguous series of wheel spins

    def __init__(self, halfTimes, image):
        self._halfTimes = []
        self._image = image
        self.viable = True
        self._rpms = [] #instantaneous speeds in rotations per minute
        raw_rpms = [] #prone to error, will be refined
        for i in range(1, len(halfTimes) -1):
            raw_rpms.append(60 /  (halfTimes[i+1] - halfTimes[i-1])) 
        #instantaneous speeds at beginning and end of rotation event
        raw_rpms.insert(0, 30 /  (halfTimes[1] - halfTimes[0]))
        raw_rpms.append(30 /  (halfTimes[-1] - halfTimes[-2])) #instantaneous speeds at beginning and end of rotation event 
        erratic = []
        for i in range(1, len(halfTimes) -1):
            if raw_rpms[i] > 200:
                erratic.append(i)
        for i in range(1, len(halfTimes) -1):
            if i not in erratic:
                self._rpms.append(raw_rpms[i])
                self._halfTimes.append(halfTimes[i])
        if len(self._halfTimes) < 2:
            self.viable = False


    def numRotations(self):
        return len(self._halfTimes) // 2

    def avgSpeed(self):
        #average speed in RPM
        return self.numRotations() * 60 / (self._halfTimes[-1] - self._halfTimes[0])

    @property
    def speeds(self):
        return self._rpms

    @property
    def startTime(self):
        return self._halfTimes[0]

    @property
    def midTime(self):
        return (self._halfTimes[-1] + self.halfTimes[0]) / 2

    @property
    def halfTimes(self):
        return self._halfTimes

    @property
    def image(self):
        return self._image

class PokeEvent:
    #series of repeated pokes

    def __init__(self, doorStates, doorTimes, pumpTimes, pumpStates, image):
        self._doorStates = doorStates
        self._doorTimes = doorTimes
        self._pumpTimes = pumpTimes
        self._pumpStates = pumpStates
        self._image = image

    def isSuccess(self):
        successful = False
        for p in self._pumpStates:
            if p is PumpStates.On:
                successful = True
        return successful

    def successfulPokes(self):
        num = 0
        for p in self._pumpStates:
            if p is PumpStates.On:
                num += 1
        if num > 0:
            if self.image.imageType == ImageTypes.Control:
                print("wtf is happening? ", self._pumpTimes)
        return num

    def totalPokes(self):
        return int(math.ceil(len(self._doorStates) / 2))
        #two door states constitute a full poke
        ##ceil necessary because only door opening documented before poke

    def totalPokesNoTimeout(self, grace=30):
        #returns total number of pokes EXCLUDING those that are failed due to image timeout
        ##i.e. after pump success
        critical_time = None
        for p, t in zip(self._pumpStates, self._pumpTimes):
            if p is PumpStates.On:
                critical_time = t 
        if critical_time is None or self.successfulPokes() > 1:
            return self.totalPokes()
        else:
            beforeSuccessful = 0
            for dt in self._doorTimes:
                if dt <= critical_time or dt > critical_time + grace: #30 seconds grace period
                    beforeSuccessful += 1
            return int(math.ceil(beforeSuccessful / 2)) 
            #two door states constitute a full poke
            ##ceil necessary because only door opening documented before poke

    def drinkTimes(self):
        drinkStart = 0
        drinkTimes = []
        for p, t in zip(self._pumpStates, self._pumpTimes):
            if p is PumpStates.On:
                drinkStart = t
            else:
                drinkTimes.append(t - drinkStart)
        return drinkTimes

    @property
    def startTime(self):
        return self._doorTimes[0]

    @property
    def image(self):
        return self._image

    @property
    def doorTimes(self):
        return self._doorTimes

    @staticmethod
    def missedRewards(poke_events, rewardImgs):
        misses = {}
        for ri in rewardImgs:
            hits = 0
            for pe in poke_events:
                if pe.image == ri:
                    hits += 1 #poke events that occured in the presence of the reward image
            print(ri.appearances, ' << reward image appearances')
            print(hits, ' << hits')
            misses[ri] = ri.appearances - hits
        print(len(poke_events), ' << total poke_events')
        return misses
    
class Image:

    def __init__(self, name, imageType):
        self.name = name
        assert isinstance(imageType, ImageTypes), 'use ImageType enum to assign images'
        self.imageType = imageType
        self._appearances = 0

    def __eq__(self, other):
        return self.name == other.name and self.imageType == other.imageType

    def __hash__(self):
        return hash(self.name)

    def incrementAppearances(self):
        self._appearances += 1

    @property
    def appearances(self):
        return self._appearances
    

def cumulativeSuccess(poke_events):
    outcomes = [int(pe.isSuccess()) for pe in poke_events]
    print("Successful Poke Events: {0}".format(sum(outcomes)))
    #times = [pe.startTime for pe in poke_events]
    cumulative_success = 0
    total = 0
    cumulative_probabilities = []
    for outcome in outcomes:
        cumulative_success += outcome
        total += 1
        cumulative_probabilities.append(cumulative_success / total)
    plt.plot(cumulative_probabilities, marker='.')
    plt.ylabel('Cumulative Probability')
    plt.xlabel('Poke Events')
    plt.title('Poke Success Rate')
    plt.show()


def rpmTimeLapse(rotation_intervals, hour=None):
    if hour is not None:
        secondCutOffs = (hour-1) * 60**2, hour * 60**2
    else:
        secondCutOffs = 0, math.inf
    rot_intervals_subset = list(filter(lambda pe: pe.startTime >= secondCutOffs[0] and pe.startTime < secondCutOffs[1], rotation_intervals))
    #these are rotation intervals that occured within specified hour
    rot_ints_byImage = [list(g[1]) for g in groupby(sorted(rot_intervals_subset, key=lambda ri: ri.image.name), key=lambda ri: ri.image.name)]
    #groups rotation intervals by image
    data = []
    for rot_ints_eachImage in rot_ints_byImage:
        allSpeeds, allTimes = [], []
        for rot_int in rot_ints_eachImage:
            # allSpeeds += rot_int.speeds
            # allTimes += rot_int.halfTimes
            allSpeeds.append(rot_int.avgSpeed())
            allTimes.append(rot_int.midTime)
        img = rot_ints_eachImage[0].image
        datum, = plt.plot(allTimes, allSpeeds, marker='.', linestyle='None', label='{0} ({1})'.format(img.name, img.imageType.value))
        data.append(datum)
    plt.xlabel('Time')
    plt.ylabel('Speed in RPM')
    # plt.xlim(0, 500)
    plt.legend(handles=data)
    plt.show()

def numPokes(poke_events):
    totalPokes = [pe.totalPokes() for pe in poke_events]
    plt.hist(totalPokes)
    plt.xlabel("Number of pokes per poke event")
    plt.ylabel("Frequency")
    plt.show()

def drinkLengths(poke_events):
    lengths = []
    for pe in poke_events:
        lengths.extend(pe.drinkTimes())
    plt.hist(lengths)
    plt.xlabel("Time (sec) drinking sugar water")
    plt.ylabel("Frequency")
    plt.show()

def endRun(wheelHalfTimes, image, rotation_intervals):
    if len(wheelHalfTimes) < 3:
        return
    rotation_intervals.append(RotationInterval(wheelHalfTimes, image)) #add this interval to list

def endPoke(doorStates, doorTimes, pumpTimes, pumpStates, image, poke_events):
    poke_events.append(PokeEvent(doorStates, doorTimes, pumpTimes, pumpStates, image))

def pruneRotationIntervals(rotation_intervals):
    erratic = []
    for ri in rotation_intervals:
        if not ri.viable:
            erratic.append(ri)
    for ri in erratic:
        rotation_intervals.remove(ri)

def pokeStatistics(poke_events, images):
    successful = 0
    total = 0
    i=0
    for pe in poke_events:
        i += 1
        successful += pe.successfulPokes()
        total += pe.totalPokesNoTimeout()
    rewardImgs = list(filter(lambda im: im.imageType is ImageTypes.Reward, images))
    misses = PokeEvent.missedRewards(poke_events, rewardImgs)
    print("Successful Pokes {0}".format(successful))
    print("Unsuccesfull Pokes {0}".format(total - successful))
    print("Total {0}".format(total))
    for ri in rewardImgs:
        print("Missed Reward Pokes for image: {0} are {1}".format(ri.name, misses[ri]))
    
def getFileNames(location):
    prefixes = []
    fileNames = []
    def recursiveDirectories(loc):
        nonlocal fileNames
        try:
            for d in next(os.walk(loc))[1]:
                recursiveDirectories(loc + d + '/')
            for f in next(os.walk(loc))[2]:
                if 'Results' in f and '.txt' in f:
                    fileNames.append(loc + f)
        except StopIteration:
            pass
    recursiveDirectories(location)
    return fileNames

def initializeImages(allInput, filename):
    images = []
    for line in allInput:
        if 'USB drive ID: ' in line:
            print("***********************************")
            print(filename, line)
        elif 'Control image set:' in line:
            for img in line[line.find('[')+1:line.rfind(']')].split(','):
                images.append(Image(img.strip(), ImageTypes.Control))
        elif 'Reward image set:' in line:
            for img in line[line.find('[')+1:line.rfind(']')].split(','):
                images.append(Image(img.strip(), ImageTypes.Reward))
        elif "Start of experiment" in line:
            return images


for filename in getFileNames('Data/'):  #['Results-TEST.txt']: #
    with open(filename, 'r') as resultFile:
        allInput = resultFile.readlines()
        currentImg = None
        pokeImg = None
        runImg = None
        currentState = None
        findFloat = re.compile("[+-]?([0-9]*[.])?[0-9]+") #regex to search for a number (float)
        wheelHalfTimes = []
        doorStates = []
        doorTimes = []
        pumpStates = []
        pumpTimes = []
        poke_events = []
        rotation_intervals = []
        skipLine = False
        images = set(initializeImages(allInput, filename)) #convert to set to avoid accidental duplication
        for line in allInput:
            if 'starting' in line:
                continue
            elif 'Image' in line and 'Name:' in line:
                curImgName = line[line.find('Name:') + 5: line.find(',')].strip()
                currentImg = next((img for img in images if img.name == curImgName), None)
                assert currentImg is not None, 'Unrecognized image: {0}'.format(curImgName)
                currentImg.incrementAppearances()
            elif 'Wheel' in line:
                if skipLine:
                    skipLine = False
                    continue
                if currentState is Activity.Poking:
                    endPoke(doorStates, doorTimes, pumpTimes, pumpStates, pokeImg, poke_events)
                    doorStates, doorTimes, pumpTimes, pumpStates = [], [], [], []
                currentState = Activity.Running
                if 'State:' in line:
                    wheelHalfTimes.append(float(findFloat.search(line).group(0))) #appends times
                if 'revolution' in line:
                    #need to skip next data point because wheel state does not actually change; it appears to be a bug
                    skipLine = True
                    continue #do NOT reset skipLine boolean
            elif 'Pump' in line:
                if currentState is Activity.Running:
                    endRun(wheelHalfTimes, currentImg, rotation_intervals)
                    wheelHalfTimes = []
                    currentState = Activity.Poking
                if re.search("State: (.*), Time", line).group(1) == 'On':
                    pump_state = PumpStates.On 
                    pokeImg = currentImg #the poke event's image should be the image when the pump is on (ie reward image)
                else:
                    pump_state = PumpStates.Off
                pumpStates.append(pump_state) 
                pumpTimes.append(float(findFloat.search(line).group(0)))
            elif 'Door' in line:
                if currentState is Activity.Running:
                    endRun(wheelHalfTimes, currentImg, rotation_intervals)
                    wheelHalfTimes = []
                if currentState is not Activity.Poking:
                    pokeImg = currentImg #record image when poke event starts
                currentState = Activity.Poking
                door_state = DoorStates.High if re.search("State: (.*), Time", line).group(1) == 'High' else DoorStates.Low
                doorStates.append(door_state)
                doorTimes.append(float(findFloat.search(line).group(0)))
            skipLine = False
        if currentState is Activity.Poking:
            endPoke(doorStates, doorTimes, pumpTimes, pumpStates, pokeImg, poke_events)
        else:
            endRun(wheelHalfTimes, currentImg, rotation_intervals)

    pruneRotationIntervals(rotation_intervals)
    ######### ANALYSIS PART BEGINS; DO NOT EDIT ABOVE FOR ANALYSIS MODES ONLY##############
    # cumulativeSuccess(poke_events)
    # rpmTimeLapse(rotation_intervals)
    # numPokes(poke_events)
    # drinkLengths(poke_events)
    #print(len(poke_events))
    pokeStatistics(poke_events, images)
    for pe in poke_events:
        try:
            print(pe.startTime)
        except IndexError:
            print(pe.doorTimes)












