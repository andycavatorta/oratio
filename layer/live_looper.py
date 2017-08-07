from pyo import *

# Global constants
TABLE_SWAP_TIME = 0.04 # Ramp time in seconds when clearing a table
MAX_LOOP_LENGTH = 10 # Longest the loop can possibly be, in seconds

def resetTable(table):
	table.reset()

class LiveLooper():
	def __init__(self):
		self.audioServer = Server(nchnls=1, sr=44100, duplex=1).boot()

		# Retrieves the mono input, write the dry signal directly to the output
		self.input = Input().out()

		# Create tables A and B, so that we can clear the table without causing a click
		self.tableA = NewTable(length=MAX_LOOP_LENGTH, chnls=1, feedback=0.0)
		self.tableB = NewTable(length=MAX_LOOP_LENGTH, chnls=1, feedback=0.0)

		self.recording = False
		self.playing = False
		self.isTableAActive = False

		# This CallAfter resets a table after a delay
		self.delayedTableResetter = None

		# Store the loop length, as well as a signal version of the same
		self.loopLen = 2
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

		# Create a mixer to mix between the output from the two loopers
		self.readmixr = Mixer(outs=1, time=0.25, chnls=1)
		self.readmixr.addInput(0, self.readA)
		self.readmixr.addInput(1, self.readB)
		self.readmixr.setAmp(0, 0, 1)
		self.readmixr.setAmp(1, 0, 1)

		# Create another mixer, for silencing the output from the mixer
		self.readOutput = Mixer(outs=1, time=0.04, chnls=1)
		self.readOutput.addInput(0, self.readmixr[0])
		self.readOutput.setAmp(0, 0, 0)

		# # Wrap the loop length signal in a sample and hold
		# self.sigLoopLenSynced = SampHold(self.sigLoopLen, self.readA["trig"], value=1)

		# # Mix the input with the output from the looper. In the first,
		# # the loop is recording, in which case we write directly from the
		# # input into the table. In the second, the table is playing back,
		# # in which case we write from the table back into the table.
		# self.inmixr = Mixer(outs=1, time=0.04, chnls=1)
		# self.inmixr.addInput(0, self.input) # On the left you've got your mic input
		# self.inmixr.addInput(1, self.readmixr[0]) # On the right there's the table values
		# self.inmixr.setAmp(0, 0, 0)
		# self.inmixr.setAmp(1, 0, 0)

		# # Make a mixer to feed input to the two tables, and set it to write to tableA
		# self.tmixr = Mixer(outs=2, time=0.04, chnls=1)
		# self.tmixr.addInput(0, self.inmixr[0])
		# self.tmixr.setAmp(0, 0, 1)
		# self.tmixr.setAmp(0, 1, 0)

		# # Use the output of that mixer to fill the tables with their own contents
		# self.fillA = TableWrite(
		# 	self.tmixr[0],
		# 	self.readA['time'] * (self.sigLoopLenSynced / MAX_LOOP_LENGTH),
		# 	self.tableA
		# )
		# self.fillB = TableWrite(
		# 	self.tmixr[1],
		# 	self.readB['time'] * (self.sigLoopLenSynced / MAX_LOOP_LENGTH),
		# 	self.tableB
		# )

		# # Finally, add a master output, which the long pedal mutes
		# self.masterLoopOutput = Mixer(chnls=1, time=0.04, outs=1)
		# self.masterLoopOutput.addInput(0, self.readOutput[0])
		# self.masterLoopOutput.setAmp(0, 0, 0)
		# self.masterLoopOutput.out()

	def isPlaying(self):
		return self.playing

	def isRecording(self):
		return self.recording

	def start(self):
		self.audioServer.start()

	def stop(self):
		self.audioServer.stop()

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

	def setLoopLength(self, len):
		self.sigLoopLen.setValue(len)
