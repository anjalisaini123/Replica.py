

class StatusMessage:


	def __init__(self, messageSummary, certificate):
		self.messageSummary = messageSummary
		self.messageSignature = 0
		self.certificate = certificate
		

	def signNonByzantineMessage(self):
		self.messageSignature = 2 # valid signature
		
		
	def signByzantineMessage(self):
		self.messageSignature = 1 # invalid signature
		

	
	
	def verify(self):
		if(self.messageSignature == 2):
			return True
		return False



class StatusMessageSummary:

	def __init__(self, agentID, iterationCounter, value, acceptedIterationNum):
		self.agentID = agentID
		self.iterationCounter = iterationCounter
		self.acceptedIterationNum = acceptedIterationNum
		self.value = value
		self.summarySignature = 0 # no signature


	def signNonByzantineMessage(self):
		self.summarySignature = 2

	
	def signByzantineMessage(self):
		self.summarySignature = 2


	def verify(self):
		if(self.summarySignature == 2):
			return True
		return False







