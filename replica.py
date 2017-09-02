import zmq
import time
import sys
import StatusMessage
import CommitMessage
import ProposeMessage
import Queue



class Replica():


    def __init__(self, isLeader, agentID, leaderID, isByzantine, portNums, numReplicas):
        self.isLeader = isLeader
        self.isByzantine = isByzantine
        self.agentID = agentID
        self.portNums = portNums
        self.numReplicas = numReplicas
        self.committedValue = None # the replica's own value
        self.receivedProposalValue = None
        self.leaderProposalValue = None # value sent by the leader
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
        self.roundTime = 5 # each round lasts for 5 seconds (for now)
        self.leaderID = leaderID
        self.numOfResponses = 0
        self.roundNum = 4 * self.iterationCounter
        self.receivedProposeMessage = None
        self.queue = Queue.Queue()
        self.tempSafeValProof = []
        self.tempCertificate = []


    def startTimer(self):
        return time.time()

    
    def elapsedTime(self, end, start):
        return end - start


    
    def start(self):
        print("Replica " + str(self.agentID))
    

        startTime = self.startTimer()
        while(True):    
            
            self.sendStatus()
            self.receiveStatus(startTime)
            self.roundNum += 1
        
            self.sendProposal(startTime)            
            self.receiveProposal(startTime)
            self.roundNum += 1
            
            self.sendCommit()
            self.receiveCommit(startTime)
            self.roundNum += 1
            print("Replica " + str(self.agentID) + " committed on " + str(self.committedValue)) 
            self.iterationCounter += 1
            print("Iteration number: " + str(self.iterationCounter))
            break

    
    
    


    


    def getTimeConsumed(self, startTime):
        currTime = time.time()
        #roundNum = int((currTime - startTime)/self.roundTime)
        timeConsumed = (currTime - startTime) - (self.roundNum * self.roundTime)
        return timeConsumed







    def sendStatus(self):
        print("Replica " + str(self.agentID) + " is in sendStatus()")
        messageSummary = StatusMessage.StatusMessageSummary(self.agentID, self.iterationCounter, self.committedValue, self.acceptedIterationNum)
        self.signMessage(messageSummary)
        statusMessage = StatusMessage.StatusMessage(messageSummary, self.certificate)
        self.signMessage(statusMessage)
        self.sendingSocket[self.leaderID].send_pyobj(statusMessage)
        return True

    
    def signMessage(self, message):
        if(self.isByzantine == 2 or self.isByzantine == 0): # isByzantine = 2 implies non byzantine and will sign with the valid signature. 0 implies byzantine and will sign its message with a valid signature
            message.signNonByzantineMessage()
        elif(self.isByzantine == 1): # isByzantine = 1 implies byzantine and will sign with the invalid signature
            message.signByzantineMessage()
        

    def processStatus(self, receivedMessage):
        receivedStatusMessage = receivedMessage
        if(self.isLeader == True):  
            if(receivedStatusMessage.verify() == True and receivedStatusMessage.messageSummary.verify() == True and self.verifyCertificate(receivedStatusMessage) == True):
                if(receivedStatusMessage not in self.tempSafeValProof): # find the element that matches the ID of this current receivedStatusMessage and remove it from tempSafeValProof
                    self.tempSafeValProof.append(receivedStatusMessage)
        

    

    def receiveStatus(self, startTime):
        print("Replica " + str(self.agentID) + " is in receiveStatus()")
        tempSafeValProof = []
        while(True):
            timeConsumed = self.getTimeConsumed(startTime)
            if(self.queue.checkQueue(self.roundNum) == False):

                if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0): # messages are being received
                    receivedStatusMessage = self.receivingSocket.recv_pyobj()
                        
                    if(self.queue.checkMessage(self.agentID, self.roundNum, receivedStatusMessage) == True):
                        self.processStatus(receivedStatusMessage)
                            
                        print("Replica " + str(self.agentID) + " received Status Message from Replica " + str(receivedStatusMessage.messageSummary.agentID) + " in receiveStatus()")
                           

                else: # there are no messages to be received in the socket
                    print("Replica " + str(self.agentID) + " has passed round time in receiveStatus()")
                    self.createSafeValProof()
                    return 
            else:
                print("Replica " + str(agentID) + " is processing messages in the queue in receiveStatus()")
                self.processStatus(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum)) # remove the processed message from the queue
                return 



                


    def createSafeValProof(self):
        maxIterationNum = self.getMaxIterationNum(self.tempSafeValProof)
        for i in range(len(self.tempSafeValProof)):
            if(maxIterationNum != self.tempSafeValProof[i].messageSummary.acceptedIterationNum): # only appending the message summaries of the status messages that do not have the most recent iteration
                self.safeValProof.append(self.tempSafeValProof[i].messageSummary)
                #print("Inside if statement")
            else:
                self.safeValProof.insert(0, self.tempSafeValProof[i])
                #print("Outside if statement, inside else statement")
        self.tempSafeValProof = [] # reset
    
    

    def resetSafeValProof(self):
        self.safeValProof = []


    def getMaxIterationNum(self, arr): # returns the most recent iteration number
        maxIterationNum = -1
        for i in range(len(arr)):
            if(arr[i].messageSummary.acceptedIterationNum >= maxIterationNum):
                maxIterationNum = arr[i].messageSummary.acceptedIterationNum
        return maxIterationNum
        
    

    
    def sendProposal(self, startTime):
        print("Replica " + str(self.agentID) + " is in sendProposal()")
        if(self.isLeader == True):
            #print("Replica " + str(self.agentID) + " received status message with value " + str(highestIterationStatusMessage.messageSummary.value))
            if(self.safeValProof[0].messageSummary.value != None):
                #print("Inside not random if statement with highestIterationStatusMessage.messageSummary.value: " + str(highestIterationStatusMessage.messageSummary.value))
                self.leaderProposalValue = self.safeValProof[0].messageSummary.value
                #print("Inside not random if statement with leaderProposalValue: " + str(self.leaderProposalValue))
            else:
                #print("Inside random else statement with highestIterationStatusMessage.messageSummary.value: " + str(highestIterationStatusMessage.messageSummary.value))
                self.leaderProposalValue = 5 # random value
                #print("Inside random else statement with leaderProposalValue: " + str(self.leaderProposalValue))
            
            messageSummary = ProposeMessage.ProposeMessageSummary(self.agentID, self.iterationCounter, self.leaderProposalValue)
            self.signMessage(messageSummary)
            proposeMessage = ProposeMessage.ProposeMessage(messageSummary, self.safeValProof)
            self.signMessage(proposeMessage)
            self.broadCast(proposeMessage)
            return True
            
            """
            if(self.isByzantine == 0 or self.isByzantine == 1): # Byzantine but signs with a valid signature
                if(highestIterationMessage.value == None):
                    self.receivedProposalValue = 5 # random value
                else:
                    self.receivedProposalValue = highestIterationMessage.value
                
                proposeMessage = ProposeMessage(self.agentID, self.iterationCounter, self.receivedProposalValue, self.safeValProof)
                self.signMessage(proposeMessage)
                self.byzantineBroadcast1(proposeMessage) # sends to one half of replicas

                self.receivedProposalValue = 2 # faulty value
                proposeMessage = ProposeMessage(self.agentID, self.iterationCounter, self.receivedProposalValue, self.safeValProof)
                self.signMessage(proposeMessage)
                self.byzantineBroadcast2(proposeMessage) # sends to other half of replicas

            """



    def processPropose(self, receivedMessage):
        receivedProposeMessage = receivedMessage
        if(receivedProposeMessage.verify() == True and receivedProposeMessage.messageSummary.verify() == True and self.verifySafeValProof(receivedProposeMessage) == True):
            self.receivedProposalValue = receivedProposeMessage.messageSummary.value
            self.receivedProposeMessage = receivedProposeMessage
        


    

    def receiveProposal(self, startTime):  
        print("Replica " + str(self.agentID) + " is in receiveProposal()")
        while(True):
            timeConsumed = self.getTimeConsumed(startTime)
            if(self.queue.checkQueue(self.roundNum) == False):

                if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0): # messages are being received
                    receivedProposeMessage = self.receivingSocket.recv_pyobj()
                    
                    if(self.queue.checkMessage(self.agentID, self.roundNum, receivedProposeMessage)):
                        self.processPropose(receivedProposeMessage)

                        #print("Replica " + str(self.agentID) + " received Propose Message from Replica " + str(self.receivedProposeMessage.messageSummary.agentID) + " with value " + str(self.receivedProposeMessage.messageSummary.value))
                        
                        print("Replica " + str(self.agentID) + " is in receiveProposal() inside checkMessage if statement")
                       

                else: # messages are not being received
                    print("Replica " + str(self.agentID) + " has passed poll time in receiveProposal()")
                    return 
            
            else:
                print("Replica " + str(self.agentID) + " is processing messages in the queue in receiveProposal()")
                self.processPropose(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum))
                return 





    
    
    def processCommit(self, receivedMessage):
        if(receivedMessage['proposal'].verify() == True and receivedMessage['proposal'].value == self.receivedProposalValue):
            if(receivedMessage['commitMessage'] not in self.tempCertificate and receivedMessage['commitMessage'].value == self.receivedProposalValue):
                self.tempCertificate.append(receivedMessage['commitMessage'])

        if(len(self.tempCertificate) >= (self.numReplicas/2) + 1):
            self.committedValue = self.receivedProposalValue # replica has commited
            self.certificate.append(self.tempCertificate)
            self.tempCertificate = [] #reset
            
               



    def sendCommit(self):
        print("Replica " + str(self.agentID) + " is in sendCommit()")
        if(self.receivedProposalValue != None):
            commitMessage = CommitMessage.CommitMessage(self.agentID, self.iterationCounter, self.receivedProposalValue)
           
            forwardedMessage = {'proposal' : self.receivedProposeMessage.messageSummary, 'commitMessage' : commitMessage}
            self.broadCast(forwardedMessage)
            return True


    def receiveCommit(self, startTime):
        print("Replica " + str(self.agentID) + " is in receiveCommit()")
        self.resetNumOfResponses()
        
        while(True):
            timeConsumed = self.getTimeConsumed(startTime)
            if(self.queue.checkQueue(self.roundNum) == False):
                
                if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0): # messages are being received
                    receivedMessage = self.receivingSocket.recv_pyobj()
                    if(self.queue.checkMessage(self.agentID, self.roundNum, receivedMessage)): 
                        self.processCommit(receivedMessage)
               
                else: # messages are not being received
                    self.tempCertificate = [] #reset
                    return
            else:
                self.processCommit(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum))
                return 






    def verifySafeValProof(self, receivedMessage): # checks if the leader's proposal mathces the most recently accepted value in the safeValProof
        maxIterationNum = self.getMaxIterationNum(receivedMessage.safeValProof)
        for i in range(len(receivedMessage.safeValProof)):
            if(maxIterationNum == receivedMessage.safeValProof[i].messageSummary.acceptedIterationNum):
                if(receivedMessage.safeValProof[i].messageSummary.value == None):
                    return True
                elif(receivedMessage.safeValProof[i].messageSummary.value == receivedMessage.messageSummary.value):
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
            if(receivedMessage.messageSummary.value == receivedMessage.certificate[i].value):
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






















replica_isLeader = int(sys.argv[1])
replica_id = int(sys.argv[2])
replica_leaderID = int(sys.argv[3])
replica_isByzantine = int(sys.argv[4])
numReplicas = int(sys.argv[5])


replica = Replica(replica_isLeader == 1, replica_id, replica_leaderID, replica_isByzantine, [5886, 5887, 5888], numReplicas)
replica.start()


