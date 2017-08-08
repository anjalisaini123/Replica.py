import zmq
import time
import sys
import StatusMessage
import CommitMessage
import ProposeMessage




class Replica:


	def __init__(self, isLeader, agentID, isByzantine, portNums, numReplicas):
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
		self.receivingSocket.bind("tcp://127.0.0.1:" + str(portNums[self.agentID]))
		self.iterationCounter = 0
		self.roundTime = 5000 # each round lasts for 5 seconds (for now)
		
		self.numOfResponses = 0
		
		



	def startTimer(self):
		return time.time()

	def endTimer(self):
		return time.time()

	def elapsedTime(self, end, start):
		return end - start



	def start(self):
		leaderID = self.getLeaderID()
		startTime = self.startTimer()
		
		while(True):
			
			self.sendStatus(leaderID)
			highestIterationStatusMessage = self.receiveStatus(startTime)
						
			
			self.sendProposal(highestIterationStatusMessage, startTime)
			proposalMessage = self.receiveProposal(startTime)
		

			self.sendCommit(proposalMessage)
			self.receiveCommit(startTime)
			
			break

	
	
	


	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)




	def getLeaderID(self):
		if(self.isLeader == True):
			return self.agentID


	def sendStatus(self, leaderID):
		messageSummary = StatusMessage.StatusMessageSummary(self.agentID, self.iterationCounter, self.committedValue, self.acceptedIterationNum)
		self.signMessage(messageSummary)
		statusMessage = StatusMessage.StatusMessage(messageSummary, self.certificate)
		self.signMessage(statusMessage)
		self.sendingSocket[leaderID].send_pyobj(statusMessage)
		

	
	def signMessage(self, message):
		if(self.isByzantine == 2 or self.isByzantine == 0): # isByzantine = 2 implies non byzantine and will sign with the valid signature. 0 implies byzantine and will sign its message with a valid signature
			message.signNonByzantineMessage()
		elif(self.isByzantine == 1): # isByzantine = 1 implies byzantine and will sign with the invalid signature
			message.signByzantineMessage()
		


	def receiveStatus(self, startTime):
		tempSafeValProof = []
		if(self.isLeader == True):
			while(len(tempSafeValProof) < (self.numReplicas/2) + 1):
				currTime = time.time()
				roundNum = (currTime - startTime)/self.roundTime
				timeConsumed = (currTime - startTime) - (roundNum * self.roundTime)

				if(self.receivingSocket.poll(self.roundTime - timeConsumed) != 0): # messages are being received
					receivedStatusMessage = self.receivingSocket.recv_pyobj()
					
					if(receivedStatusMessage.verify() == True and receivedStatusMessage.messageSummary.verify() == True and self.verifyCertificate(receivedStatusMessage) == True):
		
						if(receivedStatusMessage in tempSafeValProof): # find the element that matches the ID of this current receivedStatusMessage and remove it from tempSafeValProof
							for i in range(len(tempSafeValProof)):
								if(receivedStatusMessage.messageSummary.agentID == tempSafeValProof[i].agentID):
									tempSafeValProof.pop(i)

						elif(receivedStatusMessage not in tempSafeValProof):
							tempSafeValProof.append(receivedStatusMessage)

				else: # there are no messages to be received in the socket

					highestIterationStatusMessage = self.createSafeValProof(tempSafeValProof)
					return highestIterationStatusMessage

			if(len(tempSafeValProof) >= (self.numReplicas/2) + 1):
				highestIterationStatusMessage = self.createSafeValProof(tempSafeValProof)
				print("HighestIterationStatusMessage in receiveStatus: " + str(highestIterationStatusMessage))
				return highestIterationStatusMessage
					
			
				


	def createSafeValProof(self, tempSafeValProof):
		maxIterationNum = self.getMaxIterationNum(tempSafeValProof)
		for i in range(len(tempSafeValProof)):
			if(maxIterationNum != tempSafeValProof[i].messageSummary.acceptedIterationNum): # only appending the message summaries of the status messages that do not have the most recent iteration
				self.safeValProof.append(tempSafeValProof[i].messageSummary)
				print("Inside if statement")
			else:
				self.safeValProof.append(tempSafeValProof[i])
				print("Outside if statement, inside else statement")
				highestIterationStatusMessage = tempSafeValProof[i]
				return highestIterationStatusMessage
	
	

	def resetSafeValProof(self):
		self.safeValProof = []


	def getMaxIterationNum(self, arr): # returns the most recent iteration number
		maxIterationNum = -1
		for i in range(len(arr)):
			if(arr[i].messageSummary.acceptedIterationNum >= maxIterationNum):
				maxIterationNum = arr[i].messageSummary.acceptedIterationNum
		return maxIterationNum
		
	

	
	def sendProposal(self, highestIterationStatusMessage, startTime):
		if(self.isLeader == True):
			if(highestIterationStatusMessage.value == None):
				self.proposalValue = 5 # random value
			else:
				self.proposalValue = highestIterationStatusMessage.messageSummary.value
		
			messageSummary = ProposeMessage.ProposeMessageSummary(self.agentID, self.iterationCounter, self.proposalValue, None)
			proposeMessage = ProposeMessage.ProposeMessage(self.agentID, self.iterationCounter, self.proposalValue, self.safeValProof)
			self.signMessage(proposeMessage)
			self.broadCast(proposeMessage)
			
			
			"""
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

			"""




	def receiveProposal(self, startTime):  
		while(True):
			currTime = time.time()
			roundNum = (currTime - startTime)/self.roundTime
			timeConsumed = (currTime - startTime) - (roundNum * self.roundTime)

			if(self.receivingSocket.poll(self.roundTime - timeConsumed) != 0): # messages are being received
				receivedProposeMessage = self.receivingSocket.recv_pyobj() 
				if(receivedProposeMessage.verify() == True and receivedProposeMessage.messageSummary.verify() == True and self.verifySafeValProof(receivedProposeMessage) == True):
					self.proposalValue = receivedProposeMessage.value
					return receivedProposeMessage
				else:
					self.proposalValue = None
					return receivedProposeMessage

			else: # messages are not being received
				return None



	
	
	




	def sendCommit(self, receivedProposeMessage):
		if(self.proposalValue != None):
			commitMessage = CommitMessage.CommitMessage(self.agentID, self.iterationCounter, self.proposalValue)
			forwardedMessage = {'proposal' : receivedProposeMessage.messageSummary, 'commitMessage' : commitMessage}
			self.broadcast(forwardedMessage)
			



	
	
	def receiveCommit(self, startTime):
		self.resetNumOfResponses()
		tempCertificate = []
		while(True):
			currTime = time.time()
			roundNum = (currTime - startTime)/self.roundTime
			timeConsumed = (currTime - startTime) - (roundNum * self.roundTime)

			if(self.receivingSocket.poll(self.roundTime - timeConsumed) != 0): # messages are being received
				receivedMessage = self.receivingSocket.recv_pyobj()
				if(receivedMessage['proposal'].verify() == True and receivedMessage['proposal'].value == self.proposalValue):
					
					if(receivedMessage['commitMessage'] in tempCertificate):
						for i in range(len(tempCertificate)):
							if(tempCertificate[i].agentID == receivedMessage['commitMessage'].agentID):
								tempCertificate.pop(i)
					elif(receivedMessage['commitMessage'] not in tempCertificate and receivedMessage['commitMessage'].value == self.proposalValue):
						tempCertificate.append(receivedMessage['commitMessage'])

				if(len(tempCertificate) >= (self.numReplicas/2) + 1):
					self.committedValue = self.proposalValue # replica has commited
					break
			else: # messages are not being received
				break






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
		if(temp == 0):
			start = 0
		for i in range(start, len(self.certificate)):
			if(receivedMessage.value == receivedMessage.certificate[i].value):
				self.numOfResponses += 1
		
		if(self.numOfResponses == len(self.certificate) - start):
			self.resetNumOfResponses()
			return True
		else:
			self.resetNumOfResponses()
			return False






	def byzantineBroadcast2(self, message): #    sends to other half of replicas
		for i in range(self.numReplicas/2, self.numReplicas):
			self.sendingSocket[i].send_pyobj(message)


	def byzantineBroadcast1(self, message): # sends to half of replicas
		for i in range(self.numReplicas/2):
			self.sendingSocket[i].send_pyobj(message)
	
		
		"""	
		for i in range(self.numReplicas):
			if(self.totalReplicas[i].isByzantine == 0 or self.totalReplicas[i].isByzantine == 1):
				self.sendingSocket[i].send_json(message)
		"""

	def broadCast(self, message):
		for i in range(self.numReplicas):
			self.sendingSocket[i].send_pyobj(message)


	def nonByzantineBroadcast(self, message): # sends to honest replicas only
		for i in range(self.numReplicas):
			if(self.totalReplicas[i].isByzantine == 2):
				self.sendingSocket[i].send_pyobj(message)




	



	def resetNumOfResponses(self):
		self.numOfResponses = 0

	
	"""

	def sendNotify(self):


	def receiveNotify(self):
		while(True):
			receivedNotifyMessage = self.receivingSocket.recv_json()
			

	"""























numReplicas = int(sys.argv[1])
replica_id = int(sys.argv[2])
replica_isLeader = int(sys.argv[3])



replica = Replica(replica_isLeader == 1, replica_id, 2, [5877, 5878, 5879], numReplicas)
replica.start()


