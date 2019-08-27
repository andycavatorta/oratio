import time
from pyo import *

# Global Constants
MIN_DURATION_FOR_TAP = 0.05 # ignore tap events that are faster than this, since they were probably an accident
MAX_DURATION_FOR_TAP = 0.3 # duration in seconds of a pedal event, for it to count as a tap
MAX_INTERVAL_FOR_DOUBLE_TAP = 0.4 # interval in seconds between taps, for it to count as a double tap

class LooperController():
	def __init__(self, looper):
		self.looper = looper
		self.lastPlayPedalDownTime = -1
		self.lastRecordPedalDownTime = -1
		self.lastRecordPedalUpTime = -1
		self.lastRecordPedalTapTime = -1
		self.RecordPedalTapCount = 0
		self.PlayPedalDown = False
		self.RecordPedalDown = False

		# These CallAfters will do something after the pedals are held down
		# for longer than MAX_DURATION_FOR_TAP
		self.delayedPlayPedalChecker = None
		self.delayedRecordPedalChecker = None

	def startPlayingIfNotTap(self, tapTimestamp):
		print "looper_control startPlayingIfNotTap" 
		print("Checking to see whether you should start playing")
		print("Function arg timestamp: %f" % tapTimestamp)
		print("Last tap timestamp: %f" % self.lastPlayPedalDownTime)
		if not self.PlayPedalDown:
			return
		if (self.lastPlayPedalDownTime is tapTimestamp):
			print("Starting play")
			self.looper.setPlaying(True)

	def startRecordingIfNotTap(self, tapTimestamp):
		print "looper_control startRecordingIfNotTap" 
		print("Checking to see whether you should start recording")
		print("Function arg timestamp: %f" % tapTimestamp)
		print("Last tap timestamp: %f" % self.lastRecordPedalDownTime)
		if not self.RecordPedalDown:
			return
		if (self.lastRecordPedalDownTime is tapTimestamp):
			print("Starting recording")
			self.looper.setRecording(True)

	def handlePlayPedalDown(self):
		print "looper_control handlePlayPedalDown" 
		# If the short pedal is already down (somehow) then ignore this event
		if self.PlayPedalDown:
			print("Long pedal down event, but the long pedal is already down")
			return

		ts = time.time()
		self.lastPlayPedalDownTime = ts
		self.PlayPedalDown = True

		self.delayedPlayPedalChecker = CallAfter(self.startPlayingIfNotTap, MAX_DURATION_FOR_TAP, ts)
		print("Long pedal down")

	def handlePlayPedalUp(self):
		print "looper_control handlePlayPedalUp" 
		# If the short pedal is already up (somehow) then ignore this event
		if not self.PlayPedalDown:
			print("Long pedal up event, but the long pedal is already up")
			return

		ts = time.time()
		self.PlayPedalDown = False

		# This would mean that you just tapped the pedal for a second
		# Treat it either as a single or double tap
		downtime = ts - self.lastPlayPedalDownTime
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

	def handleRecordPedalDown(self):
		print "looper_control handleRecordPedalDown" 
		# If the short pedal is already down (somehow) then ignore this event
		if self.RecordPedalDown:
			print("Short pedal down event, but the short pedal is already down")
			return

		ts = time.time()
		self.lastRecordPedalDownTime = ts
		self.RecordPedalDown = True

		# If it's been too long since the last time this pedal was down for this
		# to count as the first part of a double tap, then clear the tap count
		if ts - self.lastRecordPedalTapTime > MAX_INTERVAL_FOR_DOUBLE_TAP:
			self.RecordPedalTapCount = 0

		self.delayedRecordPedalChecker = CallAfter(self.startRecordingIfNotTap, MAX_DURATION_FOR_TAP, ts)
		print("Short pedal down")

	def handleRecordPedalUp(self):
		print "looper_control handleRecordPedalUp" 
		# If the short pedal is already up (somehow) then ignore this event
		if not self.RecordPedalDown:
			print("Short pedal up event, but the short pedal is already up")
			return

		ts = time.time()
		self.RecordPedalDown = False

		# This would mean that you just tapped the pedal for a second
		# Treat it either as a single or double tap
		downtime = ts - self.lastRecordPedalDownTime
		if downtime <= MAX_DURATION_FOR_TAP and downtime > MIN_DURATION_FOR_TAP:
			print("Just tapped the pedal, toggle recording")
			self.lastRecordPedalTapTime = ts
			self.RecordPedalTapCount = self.RecordPedalTapCount + 1
			if self.RecordPedalTapCount == 1:
				toggledRecording = not self.looper.isRecording()
				self.looper.setRecording(toggledRecording)
			elif self.RecordPedalTapCount == 2:
				self.looper.setRecording(False)
				self.looper.clear()
			else:
				print("No action for short pedal tap count %d" % self.RecordPedalTapCount)

		# This means that you're lifting the pedal after having held it down to start recording
		# So stop recording, if you are recording
		elif downtime > MIN_DURATION_FOR_TAP:
			print("Releasing the short pedal, stop recording")
			self.lastRecordPedalTapTime = -1
			self.RecordPedalTapCount = 0
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