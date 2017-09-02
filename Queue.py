import StatusMessage
import ProposeMessage
import CommitMessage
#import NotifyMessage
class Queue:

	def __init__(self):
		self.queue = []



	def checkMessage(self, agentID, roundNum, receivedMessage): # checks if the received message is in the current round time. If not, it is placed in the queue
		messageRoundNum = self.assign(receivedMessage)
	
		if(roundNum == messageRoundNum):
			#print("inside if statement")
			return True
		
		elif((roundNum + 1) % 4 == messageRoundNum):
			#print("inside elif statement")
			self.queue.append(receivedMessage)

		else:
			
			print("Replica " + str(agentID) + " inside checkMessage() with roundNum = " + str(roundNum) + " and messageRoundNum = " + str(messageRoundNum))
			
			assert False


	def checkQueue(self, roundNum):
		count = 0
		if(len(self.queue) == 0):
			return False
		
		for i in range(len(self.queue)):
			if(self.assign(self.queue[i]) == roundNum):
				count += 1
				return i
		
		if(count == 0): # there are no messages in the queue that match the given roundNum
			return False


	
	def deQueue(self, index):
		return self.queue.pop(index)

	

	def assign(self, receivedMessage):
		if(isinstance(receivedMessage, StatusMessage.StatusMessage)):
			return 0
		elif(isinstance(receivedMessage, ProposeMessage.ProposeMessage)):
			return 1
		elif(isinstance(receivedMessage, dict)):
			return 2
		else:
			return 3

	def getQueueElement(self, index):
		return self.queue[index]


	def getLength(self):
		return len(self.queue)

