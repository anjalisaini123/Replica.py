import zmq
import sys


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
		sendStatus()
		while(True):# this is the loop that receives messages. I'll finish this and implement receive and send functions later
			recievedMessage = self.socketReceiver.recv_json() 
			if(recievedMessage['type'] == "statusRequest"):
				self.receiveStatus(recievedMessage)

			if(recievedMessage['type'] == "proposalRequest"):
				self.receivePropose(recievedMessage)

			if(recievedMessage['type'] == "commitRequest"):
				self.receiveAccept(recievedMessage)

		

	def broadCast(self, message):
		for i in range(self.numReplicas):
			self.socketSender[i].send_json(message)


	def status(self):
		if self.isLeader == 1: # leaders
			statusRequest = {'type' : "statusRequest", 'proposalNum' : self.leaderProposalNum, 'leaderID' : self.ID}
			print("Broadcast status request " + str(self.ID) + " : " + str(statusRequest))
			self.broadCast(statusRequest)

			
		statusRequest = self.socketReceiver.recv_json()
		print("statusRequestMessage message: " + str(statusRequest))
		print("self.acceptedProposalNum = " + str(self.acceptedProposalNum))
		print("statusRequestMessage['proposalNum'] = " + str(statusRequest['proposalNum']))

		statusResponse = {'type' : "statusResponse", 'promise' : statusRequest['proposalNum'], 'value' : self.agentVal, 'rank' : self.acceptedProposalNum}
		if(self.acceptedProposalNum < statusRequest['proposalNum']):		
			self.socketSender[statusRequest['leaderID']].send_json(statusResponse)

			

		if self.isLeader == 1:
			numOfResponses = 0
			maxRank = 0
			value = None
			while numOfResponses < ((numReplicas/2) + 1):
				print("Top of while loop receiver")
				statusResponse = self.socketReceiver.recv_json() 
				#print("received message from replica " + str(statusResponse['replicaID']) + " : " + str(statusResponse))
				for i in range(numReplicas):
					if(statusResponse['rank'] > maxRank):
						maxRank = statusResponse['rank']
						value = statusResponse['agentVal']

				if statusResponse['promise'] == self.leaderProposalNum:
					numOfResponses += 1
					
			if numOfResponses >= ((numReplicas/2) + 1):
				self.propose(value)


	
	# prepare request made by the leader and the acceptor's response to this prepare request

	def propose(self, value):
		if self.isLeader == 1: 
			#prepare request asks for a promise and the proposal 
			 #with the highest number less than the current leader's proposal num 
			if(value == None): # the replicas have not yet accepted anything from any other leader
				proposalRequest = {'type' : "proposalRequest", 'value' : random.randint(1,101), 'proposalNum' : self.leaderProposalNum}
				self.broadCast(proposalRequest)

			else: 
				proposalRequest = {'type' : "proposalRequest", 'value' : value, 'proposalNum' : self.leaderProposalNum}
				self.broadCast(proposalRequest) 


	def accept(self):
		#proposalRequest = self.socketReceiver.recv_json()
		if(proposalRequest['proposalNum'] >= self.promise): # checks to make sure that the replica has not made a promise with another leader that has a higher proposalNum
			self.acceptedProposalVal = proposalRequest['value']
			self.acceptedProposalNum = proposalRequest['proposalNum']
			commitRequest = {'type' : "commitRequest", 'proposalNum' : self.acceptedProposalNum, 'value' : self.acceptedProposalVal}
			self.broadCast(commitRequest) 


	


	def test(self):
		for i in range(numReplicas):
			a = "message from " + str(self.ID) + " to " + str(i)
			self.socketSender[i].send_json(a)
			recievedMessage = self.socketReceiver.recv_json()
			print(recievedMessage)

	def testSend(self):
		for i in range(numReplicas):
			sendMessage = "message from " + str(self.ID) + " to " + str(i)
			print(sendMessage)
			self.socketSender[i].send_json(sendMessage)

	"""def testReceive(self):
		for i in range(numReplicas):
			recievedMessage = self.socketReceiver.recv_json()
			print("received message " + str(self.ID) + " : " + str(recievedMessage)) """
		


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
replica.status()













