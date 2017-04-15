import zmq

class Replica: 
	

	
	def __init__(self, isLeader, agentID): 
		numReplicas = 3
		self.port = [5885, 5886, 5887] # port numbers of each of the replicas
		self.ID = agentID # the number of each replica
		context = zmq.Context()
		socket = context.socket(zmq.PUSH) 
		self.isLeader = isLeader # determines if a replica is the leader, either 0 or 1
		self.agentVal = 0 # the value that the replica holds 
		self.proposalNum = 0 # the number that keeps track of the leaders

		


	def start(self):
		status()

		



	def status(self):
		context = zmq.Context()
		if self.isLeader == 1: # leaders
			self.prepare(self, agentVal, proposalNum) # leader requests for information
			numOfResponses = 0
			leader_receiver = context.socket(zmq.PULL)
    		leader_receiver.bind("tcp://127.0.0.1:5557")# unsure about port connections
			while numOfResponses < ((numReplicas/2) + 1):
				receivedPrepareRequest = leader_receiver.recv_json() # prepare response received by the acceptors
				if receivedPrepareRequest['promise'] == True:
					numOfResponses++
			self.accept()


		else: # non leaders
			self.prepare()
			acceptor_receiver = context.socket(zmq.PULL)
			acceptor_receiver.connect("tcp://127.0.0.1:5887") # unsure about port connections
			prepareResponse = acceptor_receiver.recv_json()


	
		


	# prepare request made by the leader and the acceptor's response to this prepare request
	def prepare(self):
		context = zmq.Context()
		if self.isLeader == 1: # leaders
			# create the socket
			leader_socket = context.socket(zmq.PUSH)
			# binding to two ports
			leader_socket.bind("tcp://127.0.0.1:5885") # unsure about port connections
			leader_socket.bind("tcp://127.0.0.1:5886")
			""" prepare request asks for a promise and the proposal 
			 with the highest number less than the current leader's proposal num """
			prepareRequest = {'promise' : None, 'proposalNum' : None, 'agentVal' : None} 
			leader_socket.send_json(prepareRequest)
			

		else: # non leaders

			"""this if statement is meant to check if the proposal number of 
			the current leader is less than the proposal number of any other 
			leader the acceptor has accepted so far"""
			if self.proposalNum < proposalNum: # compare the proposal number of the current leader with the proposal number of a previous leader that has been accepted by the acceptor
				prepareResponse['promise'] = True # if the proposal number of the current leader is greater than the proposal number of any other leader the acceptor has accepted so far, then make the promise "True"
				prepareRepsonse['proposalNum'] = self.proposalNum
				prepareRepsonse['agentVal'] = self.agentVal
			




	def accept(self):
		context = zmq.Context()
		if self.isLeader == 1: # leaders
			if # acceptors have not accepted a value from another leader, this current leader can propose a new value
			else # if the acceptors have accepted a value from another leader, this current has to propose the same value
		else: # non leaders
			







