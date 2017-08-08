

class ProposeMessage:

	def __init__(self, messageSummary, safeValProof):
		self.messageSummary = messageSummary
		self.messageSignature = 0
		self.safeValProof = safeValProof


	

	def signNonByzantineMessage(self):
		self.summarySignature = 2
		self.messageSignature = 2
		

	
	def signByzantineMessage(self):
		self.summarySignature = 1
		self.messageSignature = 1

	
	def verify(self):
		if(self.messageSignature == 2):
			return True
		return False





class ProposeMessageSummary:

	def __init__(self, agentID, iterationCounter, value):
		self.agentID = agentID
		self.iterationCounter = iterationCounter
		self.value = value
		self.summarySignature = 0




	def signNonByzantineMessage(self):
		self.summarySignature = 2

	

	def signByzantineMessage(self):
		self.summarySignature = 2



	def verify(self):
		if(self.summarySignature == 2):
			return True
		return False

