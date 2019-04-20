#!/usr/bin/python3
import os
import subprocess
import re

from enum import Enum, auto

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
		for i in range(1, len(_halfTimes) -1):
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
		assert instantanceof(imageType, ImageTypes), 'use ImageType enum to assign images'
		self.imageType = imageType

	def __eq__(self, other):
		return self.name == other.name and self.imageType == other.imageType


def endRun(wheelHalfTimes, image, rotation_intervals):
	rotation_intervals.append(RotationInterval(wheelHalfTimes, image)) #add this interval to list
	del wheelHalfTimes[:] #reset halftimes

def endPoke(doorStates, doorTimes, pumpTimes, pumpStates, image, poke_events):
	poke_events.append(PokeEvent(doorStates, doorTimes, pumpTimes, pumpStates, image))
	del doorStates[:]
	del doorTimes[:]
	del pumpStates[:]
	del pumpTimes[:]
	del poke_events[:]
	

with open(filename, 'r') as resultFile:
	allInput = resultFile.readlines()
	currentImg = None
	images = set() #similar to a list, prevents duplication
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
		if 'Control image set:' in line:
			for img in line[line.find('[')+1:line.rfind(']')].split(','):
				images.add(Image(img.strip(), ImageTypes.Control))
		elif 'Reward image set:' in line:
			for img in line[line.find('[')+1:line.rfind(']')].split(','):
				images.add(Image(img.strip(), ImageTypes.Reward))
		elif 'Image' in line and 'Name:' in line:
			curImgName = line[line.find('Name:') + 5: line.find(',')].strip()
			currentImg = next((img for img in images if img.name == curImgName), None)
			assert currentImg is not None, 'Unrecognized image: {0}'.format(curImgName)
		elif 'Wheel' in line:
			if currentState is Activity.Poking:
				endPoke()
				currentState = Activity.Running
			if 'State:' in line:
				wheelHalfTimes.append(float(findFloat.search(line).group(0))) #appends times
		elif 'Pump' in line:
			if currentState is Activity.Running:
				endRun(wheelHalfTimes, currentImg, rotation_intervals)
				currentState = Activity.Poking
			pump_state = PumpState.On if re.search("State: (.*), Time", line) == 'On' else PumpState.Off
			pumpStates.append(pump_state) 
			pumpTimes.append(float(findFloat.search(line).group(0)))
		elif 'Door' in line:
			if currentState is Activity.Running:
				endRun(wheelHalfTimes, currentImg, rotation_intervals)
				currentState = Activity.Poking
			door_state = DoorStates.High if re.search("State: (.*), Time", line) == 'High' else DoorStates.Low
			doorStates.append(door_state)
			doorTimes.append(float(findFloat.search(line).group(0)))




			




