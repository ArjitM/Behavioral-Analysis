#!/usr/bin/python3
import os
import subprocess

from enum import Enum, auto

imageNames = set()

class ImageTypes(Enum):

	Reward = auto()
	Control = auto()
	Black = auto()

class DoorStates(Enum):
	High, Low = auto(), auto()

class PumpStates(Enum):
	On, Off = auto(), auto()


class RotationInterval:

	def __init__(self, halfTimes, images):
		self._halfTimes = halfTimes
		self._images = images
		self._rpms = [] #instantaneous speeds in rotations per minute
		for i in range(1, len(_halfTimes) -1):
			self._rpms.append(60 /  (self._halfTimes[i+1] - self._halfTimes[i-1])) 
		#instantaneous speeds at beginning and end of rotation event
		self._rpms.insert(0, 30 /  (self._halfTimes[1] - self._halfTimes[0]))
		self._rpms.append(30 /  (self._halfTimes[-1] - self._halfTimes[-1])) #instantaneous speeds at beginning and end of rotation event 

	def numRotations(self):
		return len(self._halfTimes) // 2


class PokeEvent:

	def __init__(self, doorStates, doorTimes, pumpTimes, pumpStates, images):
		self._doorStates = doorStates
		self._doorTimes = doorTimes
		self._pumpTimes = pumpTimes
		self._pumpStates = pumpStates
		self._images = images

	@property
	def successRate(self):
		successful, total = 0, 0
		for d, p in zip(self._doorStates, self._pumpStates):
			if d == DoorStates.Low:
				if p == PumpStates.On:
					successful = successful +1
				total = total +1
		return successful / total
	

class Image:

	def __init__(self, name, imageType):
		self.name = name
		assert instantanceof(imageType, ImageTypes), 'use ImageType enum to assign images'
		self.imageType = imageType


with open(filename, 'r') as resultFile:
	allInput = resultFile.readlines()
	currentImg = None
	for line in allInput:
		if 'Image' in line and 'Name' in line:
			




