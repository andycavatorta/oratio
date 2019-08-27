import time
from pyo import *

# Global Constants
MIN_DURATION_FOR_TAP = 0.05 # ignore tap events that are faster than this, since they were probably an accident
MAX_DURATION_FOR_TAP = 0.3 # duration in seconds of a pedal event, for it to count as a tap
MAX_INTERVAL_FOR_DOUBLE_TAP = 0.4 # interval in seconds between taps, for it to count as a double tap

class LooperController():
	def __init__(self, looper):
		self.looper = looper
		self.lastLongPedalDownTime = -1
		self.lastShortPedalDownTime = -1
		self.lastShortPedalUpTime = -1
		self.lastShortPedalTapTime = -1
		self.shortPedalTapCount = 0
		self.longPedalDown = False
		self.shortPedalDown = False

		# These CallAfters will do something after the pedals are held down
		# for longer than MAX_DURATION_FOR_TAP
		self.delayedLongPedalChecker = None
		self.delayedShortPedalChecker = None

	def startPlayingIfNotTap(self, tapTimestamp):
		print "looper_control startPlayingIfNotTap" 
		print("Checking to see whether you should start playing")
		print("Function arg timestamp: %f" % tapTimestamp)
		print("Last tap timestamp: %f" % self.lastLongPedalDownTime)
		if not self.longPedalDown:
			return
		if (self.lastLongPedalDownTime is tapTimestamp):
			print("Starting play")
			self.looper.setPlaying(True)

	def startRecordingIfNotTap(self, tapTimestamp):
		print "looper_control startRecordingIfNotTap" 
		print("Checking to see whether you should start recording")
		print("Function arg timestamp: %f" % tapTimestamp)
		print("Last tap timestamp: %f" % self.lastShortPedalDownTime)
		if not self.shortPedalDown:
			return
		if (self.lastShortPedalDownTime is tapTimestamp):
			print("Starting recording")
			self.looper.setRecording(True)

	def handleLongPedalDown(self):
		print "looper_control handleLongPedalDown" 
		# If the short pedal is already down (somehow) then ignore this event
		if self.longPedalDown:
			print("Long pedal down event, but the long pedal is already down")
			return

		ts = time.time()
		self.lastLongPedalDownTime = ts
		self.longPedalDown = True

		self.delayedLongPedalChecker = CallAfter(self.startPlayingIfNotTap, MAX_DURATION_FOR_TAP, ts)
		print("Long pedal down")

	def handleLongPedalUp(self):
		print "looper_control handleLongPedalUp" 
		# If the short pedal is already up (somehow) then ignore this event
		if not self.longPedalDown:
			print("Long pedal up event, but the long pedal is already up")
			return

		ts = time.time()
		self.longPedalDown = False

		# This would mean that you just tapped the pedal for a second
		# Treat it either as a single or double tap
		downtime = ts - self.lastLongPedalDownTime
		if downtime <= MAX_DURATION_FOR_TAP and downtime > MIN_DURATION_FOR_TAP:
			print("Just tapped the pedal, toggle play")
			toggledPlay = not self.looper.isPlaying()
			self.looper.setPlaying(toggledPlay)

		# This means that you're lifting the pedal after having held it down to start playing
		# So stop playing, if you are playing
		elif downtime > MAX_DURATION_FOR_TAP:
			print("Releasing the long pedal, stop playing")
			self.looper.setPlaying(False)

		# This was a super short tap, so probably you should ignore it
		else:
			print("Ignoring a super short long pedal tap")

	def handleShortPedalDown(self):
		print "looper_control handleShortPedalDown" 
		# If the short pedal is already down (somehow) then ignore this event
		if self.shortPedalDown:
			print("Short pedal down event, but the short pedal is already down")
			return

		ts = time.time()
		self.lastShortPedalDownTime = ts
		self.shortPedalDown = True

		# If it's been too long since the last time this pedal was down for this
		# to count as the first part of a double tap, then clear the tap count
		if ts - self.lastShortPedalTapTime > MAX_INTERVAL_FOR_DOUBLE_TAP:
			self.shortPedalTapCount = 0

		self.delayedShortPedalChecker = CallAfter(self.startRecordingIfNotTap, MAX_DURATION_FOR_TAP, ts)
		print("Short pedal down")

	def handleShortPedalUp(self):
		print "looper_control handleShortPedalUp" 
		# If the short pedal is already up (somehow) then ignore this event
		if not self.shortPedalDown:
			print("Short pedal up event, but the short pedal is already up")
			return

		ts = time.time()
		self.shortPedalDown = False

		# This would mean that you just tapped the pedal for a second
		# Treat it either as a single or double tap
		downtime = ts - self.lastShortPedalDownTime
		if downtime <= MAX_DURATION_FOR_TAP and downtime > MIN_DURATION_FOR_TAP:
			print("Just tapped the pedal, toggle recording")
			self.lastShortPedalTapTime = ts
			self.shortPedalTapCount = self.shortPedalTapCount + 1
			if self.shortPedalTapCount == 1:
				toggledRecording = not self.looper.isRecording()
				self.looper.setRecording(toggledRecording)
			elif self.shortPedalTapCount == 2:
				self.looper.setRecording(False)
				self.looper.clear()
			else:
				print("No action for short pedal tap count %d" % self.shortPedalTapCount)

		# This means that you're lifting the pedal after having held it down to start recording
		# So stop recording, if you are recording
		elif downtime > MIN_DURATION_FOR_TAP:
			print("Releasing the short pedal, stop recording")
			self.lastShortPedalTapTime = -1
			self.shortPedalTapCount = 0
			self.looper.setRecording(False)

		# This was a super short tap, so probably you should ignore it
		else:
			print("Ignoring a super short tap")

	def clear(self):
		self.looper.clear()

	def setLoopLength(self, length):
		print "looper_control setLoopLength", length
		self.looper.setLoopLength(length)

	def setVolume(self, vol):
		self.looper.setVolume(vol)