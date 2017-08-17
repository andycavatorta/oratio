from pyo import *
from math import trunc

# Global constants
TABLE_SWAP_TIME = 0.04 # Ramp time in seconds when clearing a table
MAX_LOOP_LENGTH = 10 # Longest the loop can possibly be, in seconds
DEFAULT_LOOP_LENGTH = 5
SAMPLE_RATE = 44100

def resetTable(table):
	table.reset()

class LiveLooper():
	def __init__(self):

		# This will be a function to call whenever the layer loops back around to the beginning
		self.loopCallback = None

		# When this flag is up, the layer will clear extra audio from the end of the buffer
		# as soon as the layer comes back around to the first sample
		self.needsClear = False

		self.audioServer = Server(nchnls=1, sr=SAMPLE_RATE, duplex=1, buffersize=1024)

		# Set the input offset to 1, since all these boards want right channel
		self.audioServer.setInputOffset(1)
		self.audioServer.boot()

		# Retrieves the mono input, write the dry signal directly to the output
		self.input = Input().out()

		# Create tables A and B, so that we can clear the table without causing a click
		self.tableA = NewTable(length=MAX_LOOP_LENGTH, chnls=1, feedback=0.0)
		self.tableB = NewTable(length=MAX_LOOP_LENGTH, chnls=1, feedback=0.0)
		self.scratchTable = NewTable(length=MAX_LOOP_LENGTH, chnls=1, feedback=0.0)

		self.recording = False
		self.playing = False
		self.isTableAActive = True

		# This CallAfter resets a table after a delay
		self.delayedTableResetter = None

		# Store the loop length, as well as a signal version of the same
		self.loopLen = DEFAULT_LOOP_LENGTH
		self.sigLoopLen = Sig(self.loopLen)

		# Create loopers for each table
		self.readA = Looper(
			table=self.tableA,
			pitch=1.0,
			start=0,
			dur=self.sigLoopLen,
			startfromloop=True,
			mul=1.0,
			xfade=0
		).play()
		self.readB = Looper(
			table=self.tableB,
			pitch=1.0,
			start=0,
			dur=self.sigLoopLen,
			startfromloop=True,
			mul=1.0,
			xfade=0
		).play()

		# Wrap the loop length signal in a sample and hold
		self.sigLoopLenSynced = SampHold(self.sigLoopLen, self.readA["trig"], value=1)

		# Make a counting indexer bound to the loops
		self.loopIndexCounter = Count(self.readA["trig"], max=0)

		# Create nonfading readers for each table
		self.indexA = TableIndex(
			table=self.tableA,
			index=self.loopIndexCounter
		)
		self.indexB = TableIndex(
			table=self.tableB,
			index=self.loopIndexCounter
		)

		# Add the looper trigger
		self.trigger = TrigFunc(self.readA['trig'], self.triggerLoopCallback)

		# Create a mixer to mix between the output from the two loopers
		self.readmixr = Mixer(outs=1, time=0.25, chnls=1)
		self.readmixr.addInput(0, self.readA)
		self.readmixr.addInput(1, self.readB)
		self.readmixr.setAmp(0, 0, 1)
		self.readmixr.setAmp(1, 0, 1)

		# Create a mixer to mix between the output from the two indexers
		self.indexMixer = Mixer(outs=1, time=0.25, chnls=1)
		self.indexMixer.addInput(0, self.indexA)
		self.indexMixer.addInput(1, self.indexB)
		self.indexMixer.setAmp(0, 0, 1)
		self.indexMixer.setAmp(1, 0, 1)

		# Create another mixer, for silencing the output from the mixer
		self.readOutput = Mixer(outs=1, time=0.04, chnls=1)
		self.readOutput.addInput(0, self.readmixr[0])
		self.readOutput.setAmp(0, 0, 0)

		# Mix the input with the output from the looper. In the first,
		# the loop is recording, in which case we write directly from the
		# input into the table. In the second, the table is playing back,
		# in which case we write from the table back into the table.
		self.inmixr = Mixer(outs=1, time=0.04, chnls=1)
		self.inmixr.addInput(0, self.input) # On the left you've got your mic input
		self.inmixr.addInput(1, self.indexMixer[0]) # On the right there's the table values
		self.inmixr.setAmp(0, 0, 0)
		self.inmixr.setAmp(1, 0, 0)

		# Make a mixer to feed input to the two tables, and set it to write to tableA
		self.tmixr = Mixer(outs=2, time=0.04, chnls=1)
		self.tmixr.addInput(0, self.inmixr[0])
		self.tmixr.setAmp(0, 0, 1)
		self.tmixr.setAmp(0, 1, 0)

		# Use the output of that mixer to fill the tables with their own contents
		self.fillA = TableWrite(
			self.tmixr[0],
			self.readA['time'] * (self.sigLoopLenSynced / MAX_LOOP_LENGTH),
			self.tableA
		)
		self.fillB = TableWrite(
			self.tmixr[1],
			self.readB['time'] * (self.sigLoopLenSynced / MAX_LOOP_LENGTH),
			self.tableB
		)

		# Add a master output, which the long pedal mutes
		self.masterLoopOutput = Mixer(chnls=1, time=0.04, outs=1)
		self.masterLoopOutput.addInput(0, self.readOutput[0])
		self.masterLoopOutput.setAmp(0, 0, 0)

		# And finally, multiply that output by an overall output
		self.sigVolume = SigTo(1, time=0.025, init=1)
		(self.sigVolume * self.masterLoopOutput[0]).out()

	def isPlaying(self):
		return self.playing

	def isRecording(self):
		return self.recording

	def start(self):
		self.audioServer.start()

	def stop(self):
		self.audioServer.stop()

	def setLoopCallback(self, cb):
		self.loopCallback = cb

	def setIsTableAActive(self, isA):
		print("Clearing table %s" % ("tableB" if isA else "tableA"))
		tableToClear = self.tableB if isA else self.tableA
		self.delayedTableResetter = CallAfter(resetTable, TABLE_SWAP_TIME, tableToClear)
		self.isTableAActive = isA
		self.tmixr.setAmp(0, 0, 1 if isA else 0)
		self.tmixr.setAmp(0, 1, 0 if isA else 1)

	def clear(self):
		self.setIsTableAActive(not self.isTableAActive)

	def setPlaying(self, isPlaying):
		self.playing = isPlaying
		if isPlaying:
			print("Start playing")
		else:
			print("Stop playing")
		self.masterLoopOutput.setAmp(0, 0, 1 if isPlaying else 0)

	def setRecording(self, isRecording):
		self.recording = isRecording
		if isRecording:
			print("Start recording")
			self.needsClear = True
		else:
			print("Stop recording")

		# Enable microphone input -> table, disable table -> table
		if isRecording:
			self.inmixr.setAmp(0, 0, 1)
			self.inmixr.setAmp(1, 0, 0)
			self.readOutput.setAmp(0, 0, 0)

		# Disable microphone input -> table, enable table -> table
		else:
			self.inmixr.setAmp(0, 0, 0)
			self.inmixr.setAmp(1, 0, 1)
			self.readOutput.setAmp(0, 0, 1)

	def setLoopLength(self, l):
		self.loopLen = l
		self.sigLoopLen.setValue(l)

	def setVolume(self, vol):
		self.sigVolume.setValue(vol)

	def triggerLoopCallback(self):
		if self.loopCallback is not None:
			self.loopCallback()
