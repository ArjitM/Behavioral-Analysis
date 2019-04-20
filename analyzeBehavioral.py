#!/usr/bin/python3
import os
import subprocess
import re
import matplotlib.pyplot as plt
from enum import Enum, auto
import seaborn

filename = 'Results - 2019-04-18 9c907df8daad9f581330d99873708e27.txt'

class ImageTypes(Enum):
	Reward = auto()
	Control = auto()

class DoorStates(Enum):
	High, Low = auto(), auto()

class PumpStates(Enum):
	On, Off = auto(), auto()

class Activity(Enum):
	Running, Poking = auto(), auto()

class RotationInterval:
	#continguous series of wheel spins

	def __init__(self, halfTimes, image):
		self._halfTimes = halfTimes
		self._image = image
		self._rpms = [] #instantaneous speeds in rotations per minute
		for i in range(1, len(halfTimes) -1):
			self._rpms.append(60 /  (self._halfTimes[i+1] - self._halfTimes[i-1])) 
		#instantaneous speeds at beginning and end of rotation event
		self._rpms.insert(0, 30 /  (self._halfTimes[1] - self._halfTimes[0]))
		self._rpms.append(30 /  (self._halfTimes[-1] - self._halfTimes[-2])) #instantaneous speeds at beginning and end of rotation event 

	def numRotations(self):
		return len(self._halfTimes) // 2

	def avgSpeed(self):
		#average speed in RPM
		return self.numRotations * 60 / (self._halfTimes[-1] - self._halfTimes[0])

	@property
	def speeds(self):
		return self._rpms
	

class PokeEvent:
	#series of repeated pokes

	def __init__(self, doorStates, doorTimes, pumpTimes, pumpStates, image):
		self._doorStates = doorStates
		self._doorTimes = doorTimes
		self._pumpTimes = pumpTimes
		self._pumpStates = pumpStates
		self._image = image

	def isSuccess(self):
		print(self._pumpStates)
		successful = False
		for p in self._pumpStates:
			if p is PumpStates.On:
				successful = True
		return successful

	@property
	def startTime(self):
		return self._doorTimes[0]
	

class Image:

	def __init__(self, name, imageType):
		self.name = name
		assert isinstance(imageType, ImageTypes), 'use ImageType enum to assign images'
		self.imageType = imageType

	def __eq__(self, other):
		return self.name == other.name and self.imageType == other.imageType

def cumulativeSuccess(poke_events):
	outcomes = [int(pe.isSuccess()) for pe in poke_events]
	print(outcomes)
	cumulative_success = 0
	total = 0
	cumulative_probabilities = []
	for outcome in outcomes:
		cumulative_success += outcome
		total += 1
		cumulative_probabilities.append(cumulative_success / total)
	plt.plot(cumulative_probabilities)
	plt.ylabel('Cumulative Probability')
	plt.xlabel('Time')
	plt.title('Poke Success Rate')
	plt.show()


def rpmTimeLapse():
	pass


def endRun(wheelHalfTimes, image, rotation_intervals):
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
			if currentState is Activity.Poking:
				endPoke(doorStates, doorTimes, pumpTimes, pumpStates, currentImg, poke_events)
				doorStates, doorTimes, pumpTimes, pumpStates = [], [], [], []
			currentState = Activity.Running
			if 'State:' in line:
				wheelHalfTimes.append(float(findFloat.search(line).group(0))) #appends times
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
	print(len(poke_events), len(rotation_intervals))
	cumulativeSuccess(poke_events)




			




