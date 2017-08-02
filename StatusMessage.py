

class StatusMessage:


	def __init__(self, agentID, iterationCounter, value, acceptedIterationNum, certificate):
		self.agentID = agentID
		self.iterationCounter = iterationCounter
		self.acceptedIterationNum = acceptedIterationNum
		self.value = value
		self.summarySignature = 0 # no signature
		self.messageSignature = 0
		self.certificate = certificate
		self.messageSummary = {'ID' : self.agentID, 'iterationCounter' : self.iterationCounter, 'type' : "status", 'value' : self.value, 'acceptedIterationNum' : self.acceptedIterationNum}











	def signNonByzantineMessage(self):
		self.summarySignature = 2 # valid signature
		self.messageSignature = 2
		

	
	def signByzantineMessage(self):
		self.summarySignature = 1 # invalid signature
		self.messageSignature = 1

	
	
	def verify(self):
		if(self.summarySignature == 2 and self.messageSignature == 2):
			return True
		return False


	


