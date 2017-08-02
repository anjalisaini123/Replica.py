

class NotifyMessage:

	def __init__(self):



















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


