import OSC

class OSCServerWrapper():
	def __init__(self, hostname, port):
		self.receive_address = hostname, port
		self.server = OSC.OSCServer(self.receive_address)

		# this registers a 'default' handler (for unmatched messages),
		# an /'error' handler, an '/info' handler.
		# And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
		self.server.addDefaultHandlers()

	def addOSCHandler(self, msg, handler):
		self.server.addMsgHandler(msg, handler)

	# Careful, because this will run serve_forever, so hopefully you
	# weren't going to be doing anything else with this thread
	def startOSCSServer(self):
		print "Registered Callback-functions are :"
		for addr in self.server.getOSCAddressSpace():
			print addr

		# Start OSCServer
		print "\nStarting OSCServer. Use ctrl-C to quit."
		self.server.serve_forever()
