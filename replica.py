import zmq
import sys
import random

class Replica: 
	

	
	def __init__(self, isLeader, agentID, totalPortNums, numReplicas): 
		self.totalPortNums = totalPortNums # port numbers of each of the replicas
		self.numReplicas = numReplicas # total number of replicas
		self.ID = agentID # the number of each replica
		print("ID number " + str(agentID))
		self.socketSender = [] # 
		for i in range(numReplicas):
			self.socketSender.append(zmq.Context().socket(zmq.PUSH))
			self.socketSender[i].connect("tcp://127.0.0.1:" + str(totalPortNums[i]))
		
		self.socketReceiver = zmq.Context().socket(zmq.PULL)
		self.socketReceiver.bind("tcp://127.0.0.1:" + str(totalPortNums[agentID]))
		self.isLeader = isLeader # determines if a replica is the leader, either 0 or 1
		self.acceptedProposalVal = None # the value that the replica holds 
		self.acceptedProposalNum = 0 
		self.leaderProposalNum = 1
		self.promise = 0

	


	def start(self):
		self.sendStatus()
		numOfResponses = 0
		maxRank = -1
		value = None
		while(True):
			receivedMessage = self.socketReceiver.recv_json() 
			if(receivedMessage['type'] == "statusRequest"):
				print(" ")
				print("In status request")
				self.receiveStatus(receivedMessage)

			if(receivedMessage['type'] == "statusResponse"):
				print(" ")
				print("In status response")
				for i in range(numReplicas):
					if(receivedMessage['rank'] > maxRank):
						maxRank = receivedMessage['rank']
						value = receivedMessage['value']
						

				if(receivedMessage['promise'] == self.leaderProposalNum):
					print("Inside promise if statement")
					numOfResponses += 1
				
				print("numOfResponses: " + str(numOfResponses))
				if(numOfResponses >= ((numReplicas/2) + 1)):
					self.sendPropose(value)
					numOfResponses = 0 # reset the number of responses to 0

			if(receivedMessage['type'] == "proposalRequest"):
				print("In proposal request")
				self.accept(receivedMessage)

			if(receivedMessage['type'] == "commitRequest"):
				print("In commit request")
				if(receivedMessage['value'] == self.acceptedProposalVal and receivedMessage['proposalNum'] >= self.acceptedProposalNum):
					numOfResponses += 1
				if(numOfResponses >= ((numReplicas/2) + 1)): # commit after receive f+1 commit requests
					print("replica " + str(self.ID) + " has committed to " + str(self.acceptedProposalVal)) # commit to the value

		

	def broadCast(self, message):
		for i in range(self.numReplicas):
			self.socketSender[i].send_json(message)


	def sendStatus(self):
		if self.isLeader == 1: # leaders
			statusRequest = {'type' : "statusRequest", 'proposalNum' : self.leaderProposalNum, 'leaderID' : self.ID}
			print("Broadcast status request " + str(self.ID) + " : " + str(statusRequest))
			self.broadCast(statusRequest)

		
	def receiveStatus(self, receivedMessage):
		statusResponse = {'type' : "statusResponse", 'promise' : receivedMessage['proposalNum'], 'value' : self.acceptedProposalVal, 'rank' : self.acceptedProposalNum, 'ID' : self.ID}
		if(self.acceptedProposalNum < receivedMessage['proposalNum']):		
			self.socketSender[receivedMessage['leaderID']].send_json(statusResponse)



	def sendPropose(self, value):
			#if self.isLeader == 1: 
			""" prepare request asks for a promise and the proposal 
			 with the highest number less than the current leader's proposal num """
			if(value == None): # the replicas have not yet accepted anything from any other leader
				proposalRequest = {'type' : "proposalRequest", 'value' : random.randint(1,101), 'proposalNum' : self.leaderProposalNum}
				self.broadCast(proposalRequest)

			else: 
				proposalRequest = {'type' : "proposalRequest", 'value' : value, 'proposalNum' : self.leaderProposalNum}
				self.broadCast(proposalRequest)


	def accept(self, receivedMessage): # change name from receiveProposal() to accept() because when you receive a value, you just accept it under certain conditions
		if(receivedMessage['proposalNum'] >= self.promise): # checks to make sure that the replica has not made a promise with another leader that has a higher proposalNum
			self.acceptedProposalVal = receivedMessage['value']
			self.acceptedProposalNum = receivedMessage['proposalNum']
			commitRequest = {'type' : "commitRequest", 'proposalNum' : self.acceptedProposalNum, 'value' : self.acceptedProposalVal}
			self.broadCast(commitRequest)






	def test(self):
		for i in range(numReplicas):
			a = "message from " + str(self.ID) + " to " + str(i)
			self.socketSender[i].send_json(a)
			receivedMessage = self.socketReceiver.recv_json()
			print(receivedMessage)

	def testSend(self):
		for i in range(numReplicas):
			sendMessage = "message from " + str(self.ID) + " to " + str(i)
			print(sendMessage)
			self.socketSender[i].send_json(sendMessage)

	"""def testReceive(self):
		for i in range(numReplicas):
			receivedMessage = self.socketReceiver.recv_json()
			print("received message " + str(self.ID) + " : " + str(receivedMessage)) """
		


numReplicas = int(sys.argv[1])
replica_id = int(sys.argv[2])

"""for i in range(numReplicas):
	replicas.append(Replica(0, i, [5885, 5886, 5887], numReplicas))

for i in range(numReplicas):
	replicas[i].testSend()
for i in range(numReplicas):
	replicas[i].testReceive()"""

"""replicas.append(Replica(1, 0, [5885, 5886, 5887], numReplicas))
replicas.append(Replica(0, 1, [5885, 5886, 5887], numReplicas))
replicas.append(Replica(0, 2, [5885, 5886, 5887], numReplicas))"""

#for i in range(numReplicas):
#	replicas[i].status()

replica = Replica(replica_id == 0, replica_id, [5885, 5886, 5887], numReplicas)
replica.start()













