

class CommitMessage:

	def __init__(self, agentID, iterationCounter, value):
		self.agentID = agentID
		self.iterationCounter = iterationCounter
		self.value = value
		self.messageSignature = 0






	def signNonByzantineMessage(self):
		self.summarySignature = 2
		self.messageSignature = 2
		

	
	def signByzantineMessage(self):
		self.summarySignature = 1
		self.messageSignature = 1

	
	def verify(self):
		if(self.messageSignature == 2 and self.summarySignature == 2):
			return True
		elif(self.summarySignature == 2):
			return True
		return False
