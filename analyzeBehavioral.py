#!/usr/bin/env python3
import os
import subprocess
import re
import matplotlib.pyplot as plt
from enum import Enum, auto
from itertools import groupby
import seaborn

filename = 'Results - 2019-04-18 9c907df8daad9f581330d99873708e27.txt'

class ImageTypes(Enum):
	Reward = "Reward"
	Control = "Control"

class DoorStates(Enum):
	High, Low = auto(), auto()

class PumpStates(Enum):
	On, Off = auto(), auto()

class Activity(Enum):
	Running, Poking = auto(), auto()

class RotationInterval:
	#continguous series of wheel spins

	def __init__(self, halfTimes, image):
		self._halfTimes = []
		self._image = image
		self._rpms = [] #instantaneous speeds in rotations per minute
		raw_rpms = [] #prone to error
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


	def numRotations(self):
		return len(self._halfTimes) // 2

	def avgSpeed(self):
		#average speed in RPM
		return self.numRotations * 60 / (self._halfTimes[-1] - self._halfTimes[0])

	@property
	def speeds(self):
		return self._rpms

	@property
	def startTime(self):
		return self._halfTimes[0]

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

	@property
	def startTime(self):
		return self._doorTimes[0]

	@property
	def image(self):
		return self._image
	
	

class Image:

	def __init__(self, name, imageType):
		self.name = name
		assert isinstance(imageType, ImageTypes), 'use ImageType enum to assign images'
		self.imageType = imageType

	def __eq__(self, other):
		return self.name == other.name and self.imageType == other.imageType

def cumulativeSuccess(poke_events):
	outcomes = [int(pe.isSuccess()) for pe in poke_events]
	times = [pe.startTime for pe in poke_events]
	cumulative_success = 0
	total = 0
	cumulative_probabilities = []
	for outcome in outcomes:
		cumulative_success += outcome
		total += 1
		cumulative_probabilities.append(cumulative_success / total)
	plt.plot(times, cumulative_probabilities)
	plt.ylabel('Cumulative Probability')
	plt.xlabel('Time')
	plt.title('Poke Success Rate')
	plt.show()


def rpmTimeLapse(rotation_intervals, hour=1):
	secondCutOffs = (hour-1) * 60**2, hour * 60**2
	rot_intervals_subset = list(filter(lambda pe: pe.startTime >= secondCutOffs[0] and pe.startTime < secondCutOffs[1], rotation_intervals))
	#these are rotation intervals that occured within specified hour
	rot_ints_byImage = [list(g[1]) for g in groupby(sorted(rot_intervals_subset, key=lambda ri: ri.image.name), key=lambda ri: ri.image.name)]
	#groups rotation intervals by image
	data = []
	for rot_ints_eachImage in rot_ints_byImage:
		allSpeeds, allTimes = [], []
		for rot_int in rot_ints_eachImage:
			allSpeeds += rot_int.speeds
			allTimes += rot_int.halfTimes
		img = rot_ints_eachImage[0].image
		datum, = plt.plot(allTimes, allSpeeds, marker='.', linestyle='None', label='{0} ({1})'.format(img.name, img.imageType.value))
		data.append(datum)
		# print('***', rot_int.halfTimes)
	plt.xlabel('Time')
	plt.ylabel('Speed in RPM')
	plt.legend(handles=data)
	plt.show()


def endRun(wheelHalfTimes, image, rotation_intervals):
	if len(wheelHalfTimes) < 3:
		return
	rotation_intervals.append(RotationInterval(wheelHalfTimes, image)) #add this interval to list

def endPoke(doorStates, doorTimes, pumpTimes, pumpStates, image, poke_events):
	poke_events.append(PokeEvent(doorStates, doorTimes, pumpTimes, pumpStates, image))
	
with open(filename, 'r') as resultFile:
	allInput = resultFile.readlines()
	currentImg = None
	images = []
	currentState = None
	findFloat = re.compile("[+-]?([0-9]*[.])?[0-9]+") #regex to search for a number
	wheelHalfTimes = []
	doorStates = []
	doorTimes = []
	pumpStates = []
	pumpTimes = []
	poke_events = []
	rotation_intervals = []
	skipLine = False
	for line in allInput:
		if 'starting' in line:
			continue
		if 'Control image set:' in line:
			for img in line[line.find('[')+1:line.rfind(']')].split(','):
				images.append(Image(img.strip(), ImageTypes.Control))
		elif 'Reward image set:' in line:
			for img in line[line.find('[')+1:line.rfind(']')].split(','):
				images.append(Image(img.strip(), ImageTypes.Reward))
		elif 'Image' in line and 'Name:' in line:
			curImgName = line[line.find('Name:') + 5: line.find(',')].strip()
			currentImg = next((img for img in images if img.name == curImgName), None)
			assert currentImg is not None, 'Unrecognized image: {0}'.format(curImgName)
		elif 'Wheel' in line:
			if skipLine:
				#print('Skipping', line)
				skipLine = False
				continue
			if currentState is Activity.Poking:
				endPoke(doorStates, doorTimes, pumpTimes, pumpStates, currentImg, poke_events)
				doorStates, doorTimes, pumpTimes, pumpStates = [], [], [], []
			currentState = Activity.Running
			if 'State:' in line:
				wheelHalfTimes.append(float(findFloat.search(line).group(0))) #appends times
			if 'revolution' in line:
				#need to skip next data point because wheel state does not actually change
				skipLine = True
				continue #do NOT reset skipLine boolean
		elif 'Pump' in line:
			if currentState is Activity.Running:
				endRun(wheelHalfTimes, currentImg, rotation_intervals)
				wheelHalfTimes = []
				currentState = Activity.Poking
			pump_state = PumpStates.On if re.search("State: (.*), Time", line).group(1) == 'On' else PumpStates.Off
			pumpStates.append(pump_state) 
			pumpTimes.append(float(findFloat.search(line).group(0)))
		elif 'Door' in line:
			if currentState is Activity.Running:
				endRun(wheelHalfTimes, currentImg, rotation_intervals)
				wheelHalfTimes = []
			currentState = Activity.Poking
			door_state = DoorStates.High if re.search("State: (.*), Time", line).group(1) == 'High' else DoorStates.Low
			doorStates.append(door_state)
			doorTimes.append(float(findFloat.search(line).group(0)))
		skipLine = False
	cumulativeSuccess(poke_events)
	rpmTimeLapse(rotation_intervals, 1)




			




