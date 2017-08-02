

class ProposeMessage:

	def __init__(self, agentID, iterationCounter, value, safeValProof):
		self.agentID = agentID
		self.iterationCounter = iterationCounter
		self.value = value
		self.safeValProof = safeValProof
		self.summarySignature = 0
		self.messageSignature = 0

		self.messageSummary = {'ID' : self.agentID, 'iterationCounter' : self.iterationCounter, 'type' : "propose", 'value' : self.value}










	def signNonByzantineMessage(self):
		self.summarySignature = 2
		self.messageSignature = 2
		

	
	def signByzantineMessage(self):
		self.summarySignature = 1
		self.messageSignature = 1

	
	def verify(self, receivedMessage):
		if(self.summarySignature == 2 and self.messageSignature == 2):
			return True
		return False