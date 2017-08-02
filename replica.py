import zmq
import time





class Replica:


	def __init__(self, isLeader, agentID, isByzantine, portNums, numReplicas, totalReplicas):
		self.isLeader = isLeader
		self.isByzantine = isByzantine
		self.agentID = agentID
		self.portNums = portNums
		self.numReplicas = numReplicas
		self.committedValue = None # the replica's own value
		self.proposalValue = None # value sent by the leader
		self.acceptedIterationNum = 0 # the replica's own iteration number
		self.certificate = []
		self.safeValProof = []

		self.sendingSocket = []
		for i in range(numReplicas):
			self.sendingSocket.append(zmq.Context().socket(zmq.PUSH))
			self.sendingSocket[i].connect("tcp://127.0.0.1:" + str(portNums[i]))
		
		self.receivingSocket = zmq.Context().socket(zmq.PULL)
		receivingSocket.bind("tcp://127.0.0.1:" + str(portNums[self.agentID]))
		self.iterationCounter = 0
		self.timer = 5000 # each round lasts for 5 seconds (for now)
		
		self.numOfResponses = 0
		self.totalReplicas = totalReplicas
		



	def startTimer(self):
		return start = time.time()

	def endTimer(self):
		return end = time.time()

	def elapsedTime(self):
		return self.endTimer() - self.startTimer()



	def start(self):
		leaderID = self.getLeaderID()
		
		self.startTimer()
		
		self.sendStatus(leaderID)
		self.receiveStatus()
	
		self.endTimer()
	

	
	


	def getLeaderID(self):
		if(self.isLeader == True):
			return self.agentID


	def sendStatus(self, leaderID):
		statusMessage = StatusMessage(self.agentID, self.iterationCounter, self.committedValue, self.acceptedIterationNum, self.certificate)
		self.signMessage(statusMessage)
		self.socketSender[leaderID].send_json(statusMessage)

	
	def signMessage(self, message):
		if(self.isByzantine == 2 or self.isByzantine == 0): # isByzantine = 2 implies non byzantine and will sign with the valid signature. 0 implies byzantine and will sign its message with a valid signature
			message.signNonByzantineMessage()
		elif(self.isByzantine == 1): # isByzantine = 1 implies byzantine and will sign with the invalid signature
			message.signByzantineMessage()
		


	def receiveStatus(self):
		tempSafeValProof = []
		if(self.isLeader == True):

			while(len(tempSafeValProof) < (self.numReplicas/2) + 1):
				
				if(self.receivingSocket.poll(self.timer) != 0): # messages are being received
					receivedStatusMessage = self.receivingSocket.recv_json()
					
					if(receivedStatusMessage.verify() == True and verifyCertificate(receivedStatusMessage) == True):
		
						if(receivedStatusMessage in tempSafeValProof): # find the element that matches the ID of this current receivedStatusMessage and remove it from tempSafeValProof
							for i in range(len(tempSafeValProof)):
								if(receivedStatusMessage.agentID == tempSafeValProof[i].agentID):
									tempSafeValProof.pop(i)

						elif(receivedStatusMessage not in tempSafeValProof):
							tempSafeValProof.append(receivedStatusMessage)

				else: # there are no messages to be received in the socket
					highestIterationMessage = self.createSafeValProof(tempSafeValProof)
					self.sendProposal(highestIterationMessage)

			if(len(tempSafeValProof) >= (self.numReplicas/2) + 1):
				highestIterationMessage = self.createSafeValProof(tempSafeValProof)
				self.sendProposal(highestIterationMessage)
					
			
				


	def createSafeValProof(self, tempSafeValProof):
		maxIterationNum = getMaxIterationNum(tempSafeValProof)
		for i in range(len(tempSafeValProof)):
			if(maxIterationNum != tempSafeValProof[i].acceptedIterationNum): # only appending the message summaries of the status messages that do not have the most recent iteration
				self.safeValProof.append(tempSafeValProof[i].messageSummary)
			else:
				self.safeValProof.append(tempSafeValProof[i])
				highestIterationMessage = tempSafeValProof[i]
		return highestIterationMessage
	
	

	def resetSafeValProof(self):
		self.safeValProof = []


	def getMaxIterationNum(self, arr): # returns the most recent iteration number
		maxIterationNum = -1
		for i in range(len(arr)):
			if(arr[i].acceptedIterationNum >= maxIterationNum):
				maxIterationNum = arr[i].acceptedIterationNum
		return maxIterationNum
		
	

	
	def sendProposal(self, highestIterationMessage):
		if(self.isLeader == True):
			if(self.isByzantine == 2):
				if(highestIterationMessage.value == None):
					self.proposalValue = 5 # random value
				else:
					self.proposalValue = highestIterationMessage.value
		
				proposeMessage = ProposeMessage(self.agentID, self.iterationCounter, self.proposalValue, self.safeValProof)
				self.signMessage(proposeMessage)
				self.broadCast(proposeMessage)
			
			if(self.isByzantine == 0 or self.isByzantine == 1): # Byzantine but signs with a valid signature
				if(highestIterationMessage.value == None):
					self.proposalValue = 5 # random value
				else:
					self.proposalValue = highestIterationMessage.value
				
				proposeMessage = ProposeMessage(self.agentID, self.iterationCounter, self.proposalValue, self.safeValProof)
				self.signMessage(proposeMessage)
				self.byzantineBroadcast1(proposeMessage) # sends to one half of replicas

				self.proposalValue = 2 # faulty value
				proposeMessage = ProposeMessage(self.agentID, self.iterationCounter, self.proposalValue, self.safeValProof)
				self.signMessage(proposeMessage)
				self.byzantineBroadcast2(proposeMessage) # sends to other half of replicas






	def receiveProposal(self):  
		while(True):
			if(self.receivingSocket.poll(self.timer) != 0): # messages are being received
				receivedProposeMessage = self.receivingSocket.recv_json() 
				if(receivedProposeMessage.verify() == True and verifySafeValProof(receivedProposeMessage) == True):
					self.proposalValue = receivedProposeMessage.value
					self.sendCommit(receivedProposeMessage)
				else:
					self.proposalValue = None
					self.sendCommit(receivedProposeMessage)

			else: # messages are not being received
				
				self.sendCommit()



	
	
	def verifySafeValProof(self, receivedMessage): # checks if the leader's proposal mathces the most recently accepted value in the safeValProof
		maxIterationNum = self.getMaxIterationNum(receivedMessage.safeValProof)
		for i in range(len(receivedMessage.safeValProof)):
			if(maxIterationNum == receivedMessage.safeValProof[i].acceptedIterationNum):
				if(receivedMessage.safeValProof[i].value == receivedMessage.value):
					return True
		return False



	def verifyCertificate(self, receivedMessage): # checks if the values in the certificate match the value that the replica has accepted in its status message
		if(receivedMessage.certificate == None):
			return True
		temp = len(self.certificate)/(self.numReplicas/2 + 1)
		start = (temp - 1) * (self.numReplicas/2 + 1)
		
		for i in range(start, len(self.certificate)):
			if(receivedMessage.value == receivedMessage.certificate[i].value):
				self.numOfResponses += 1
		
		if(self.numOfResponses == len(self.certificate) - start):
			self.resetNumOfResponses()
			return True
		else:
			self.resetNumOfResponses()
			return False





	def sendCommit(self, receivedProposeMessage):
		if(self.proposalValue != None):
			self.broadcast(receivedProposeMessage.messageSummary)
			commitMessage = CommitMessage(self.agentID, self.iterationCounter, self.proposalValue)
			self.broadcast(commitMessage)





	def receiveCommit(self):
		while(True):
			if(self.receivingSocket.poll(self.timer) != 0): # messages are being received
				receivedMessage = self.receivingSocket.recv_json()
				if(!(isinstance(receivedMessage, CommitMessage()))):
					receivedMessage['value'] == self.proposalValue





			else: # messages are not being received







	def byzantineBroadcast2(self, message): #    sends to other half of replicas
		for i in range(self.numReplicas/2, self.numReplicas):
			self.socketSender[i].send_json(message)


	def byzantineBroadcast1(self, message): # sends to half of replicas
		for i in range(self.numReplicas/2):
			self.socketSender[i].send_json(message)
	
		
		"""	
		for i in range(self.numReplicas):
			if(self.totalReplicas[i].isByzantine == 0 or self.totalReplicas[i].isByzantine == 1):
				self.socketSender[i].send_json(message)
		"""

	def broadCast(self, message):
		for i in range(self.numReplicas):
			self.socketSender[i].send_json(message)


	def nonByzantineBroadcast(self, message): # sends to honest replicas only
		for in range(self.numReplicas):
			if(self.totalReplicas[i].isByzantine == 2):
				self.socketSender[i].send_json(message)




	



	def resetNumOfResponses():
		self.numOfResponses = 0

	

	def sendNotify(self):


	def receiveNotify(self):
		while(True):
			receivedNotifyMessage = self.receivingSocket.recv_json()
