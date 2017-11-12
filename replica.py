import zmq
import time
import sys
import random
import StatusMessage
import CommitMessage
import ProposeMessage
import NotifyMessage
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
        self.hasCommited = None


    def startTimer(self):
        return time.time()

    
    def elapsedTime(self, end, start):
        return end - start


    
    def start(self):
        print("Replica " + str(self.agentID))
    

        startTime = self.startTimer()
        while(self.iterationCounter < 1):    
            
            self.sendStatus()
            self.receiveStatus(startTime)
            self.roundNum += 1
        
            self.sendProposal(startTime)            
            self.receiveProposal(startTime)
            self.roundNum += 1
            
            self.sendCommit()
            self.receiveCommit(startTime)
            self.roundNum += 1

            self.sendNotify()
            self.receiveNotify(startTime)
            self.roundNum += 1

            print("Replica " + str(self.agentID) + " committed on " + str(self.committedValue) + " for iteration " + str(self.iterationCounter)) 
            self.iterationCounter += 1
            print("Iteration number: " + str(self.iterationCounter))

            #break
            

    
    
    


    


    def getTimeConsumed(self, startTime):
        currTime = time.time()
        #roundNum = int((currTime - startTime)/self.roundTime)
        timeConsumed = (currTime - startTime) - (self.roundNum * self.roundTime)
        return timeConsumed







    def sendStatus(self):
        #print("Replica " + str(self.agentID) + " is in sendStatus()")
        print("Replica " + str(self.agentID) + " is in sendStatus() with roundNum = " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        messageSummary = StatusMessage.StatusMessageSummary(self.agentID, self.iterationCounter, self.committedValue, self.acceptedIterationNum)
        self.signMessage(messageSummary)
        statusMessage = StatusMessage.StatusMessage(self.agentID, messageSummary, self.certificate)
        self.signMessage(statusMessage)
        self.sendingSocket[self.leaderID].send_pyobj(statusMessage)
        print("Replica " + str(self.agentID) + " sent a status message to Replica " + str(self.leaderID))
        return True

    
    def signMessage(self, message):
        if(self.isByzantine == 2 or self.isByzantine == 0): # isByzantine = 2 implies non byzantine and will sign with the valid signature. 0 implies byzantine and will sign its message with a valid signature
            message.signNonByzantineMessage()
        elif(self.isByzantine == 1): # isByzantine = 1 implies byzantine and will sign with the invalid signature
            message.signByzantineMessage()
        

    def processStatus(self, receivedMessage):
        print("Replica " + str(self.agentID) + " is in processStatus() with roundNum = " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        receivedStatusMessage = receivedMessage
        if(self.isLeader == True):  
            if(receivedStatusMessage.verify() == True and receivedStatusMessage.messageSummary.verify() == True and self.verifyCertificate(receivedStatusMessage) == True):
                if(receivedStatusMessage not in self.tempSafeValProof): # find the element that matches the ID of this current receivedStatusMessage and remove it from tempSafeValProof
                    print("Replica " + str(self.agentID) + " in processStatus() appending a status message from Replica " + str(receivedMessage.messageSummary.agentID) + " to tempSafeValProof")
                    self.tempSafeValProof.append(receivedStatusMessage)
                    return

    

    def receiveStatus(self, startTime):
        #print("Replica " + str(self.agentID) + " is in receiveStatus()")
        print("Replica " + str(self.agentID) + " is in receiveStatus() with roundNum = " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        tempSafeValProof = []
        #print(self.printReplica() + " in receiveStatus(), self.queue.checkQueue(self.roundNum) = " + str(self.queue.checkQueue(self.roundNum)))
        if(self.queue.checkQueue(self.roundNum) != -1):
            #print(self.printReplica() + " is inside receiveStatus() inside check queue if statement with a length of " + str(self.queue.getLength()))
            #print(self.printReplica() + " is inside receiveStatus() inside check queue if statment with self.queue.checkQueue(self.roundNum) = " + str(self.queue.checkQueue(self.roundNum)))
            while(self.queue.checkQueue(self.roundNum) != -1):
                print("Replica " + str(self.agentID) + " is processing messages in the queue in receiveStatus()")
                self.processStatus(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum)) # remove the processed message from the queue

        print("Replica " + str(self.agentID) + " in receiveStatus() is between check queue and poll")
        while(True):
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveStatus() timeConsumed = " + str(timeConsumed))
            print("Replica " + str(self.agentID) + " in receiveStatus() roundTime = " + str(self.roundTime))
            print("Replica " + str(self.agentID) + " in receiveStatus() check #1 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            
            if(timeConsumed > self.roundTime):
                print("Replica " + str(self.agentID) + " has passed round time in receiveStatus()")
                return

            print("Replica " + str(self.agentID) + " in receiveStatus() in between timeConsumed and poll")
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveStatus() with self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) = " + str(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000)))
            print("Replica " + str(self.agentID) + " in receiveStatus() check #2 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
           
            if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0): # messages are being received
                print("Replica " + str(self.agentID) + " is in receiveStatus() inside poll")
                receivedStatusMessage = self.receivingSocket.recv_pyobj()
                #print("Replica " + str(self.agentID) + " is before checkMessage in receiveStatus()")    
                if(self.queue.checkMessage(self.agentID, self.roundNum, receivedStatusMessage) == True):
                    self.processStatus(receivedStatusMessage)
                                
                    print("Replica " + str(self.agentID) + " received Status Message from Replica " + str(receivedStatusMessage.agentID) + " in receiveStatus()")
                               
           



                


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
        #print("Replica " + str(self.agentID) + " is in sendProposal()")
        print("Replica " + str(self.agentID) + " is in sendProposal() with roundNum = " + str(self.roundNum) + " and iterationCounter " + str(self.iterationCounter))
        if(self.isLeader == True):
            self.createSafeValProof()
            #print("Replica " + str(self.agentID) + " received status message with value " + str(highestIterationStatusMessage.messageSummary.value))
            if(self.safeValProof[0].messageSummary.value != None):
                print("Replica " + str(self.agentID) + " inside sendProposal() when reproposing a value")
                
                #print("Inside not random if statement with highestIterationStatusMessage.messageSummary.value: " + str(highestIterationStatusMessage.messageSummary.value))
                self.leaderProposalValue = self.safeValProof[0].messageSummary.value
                #print("Inside not random if statement with leaderProposalValue: " + str(self.leaderProposalValue))
            else:
                print("Replica " + str(self.agentID) + " inside sendProposal() when proposing a new value")
                self.leaderProposalValue = random.randint(1,10) # random value
                #print("Inside random else statement with leaderProposalValue: " + str(self.leaderProposalValue))
            
            messageSummary = ProposeMessage.ProposeMessageSummary(self.agentID, self.iterationCounter, self.leaderProposalValue)
            self.signMessage(messageSummary)
            proposeMessage = ProposeMessage.ProposeMessage(self.agentID, messageSummary, self.safeValProof)
            self.signMessage(proposeMessage)
            self.broadCast(proposeMessage)
            print("Replica " + str(self.agentID) + " has broadcasted a proposal with value " + str(self.leaderProposalValue))
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
        print("Replica " + str(self.agentID) + " is in processPropose() and roundNum " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        receivedProposeMessage = receivedMessage
        if(receivedProposeMessage.verify() == True and receivedProposeMessage.messageSummary.verify() == True and self.verifySafeValProof(receivedProposeMessage) == True):
            #print("Replica " + str(self.agentID) + " receivedProposeMessage.messageSummary.value = " + str(receivedProposeMessage.messageSummary.value) + " for iterationCounter = " + str(self.iterationCounter))
            #assert receivedProposeMessage.messageSummary.value != 5
            self.receivedProposalValue = receivedProposeMessage.messageSummary.value
            print("Replica " + str(self.agentID) + " inside processPropose() received value " + str(self.receivedProposalValue) + " for iterationCounter = " + str(self.iterationCounter))

            self.receivedProposeMessage = receivedProposeMessage
            return        


    

    def receiveProposal(self, startTime):  
        print("Replica " + str(self.agentID) + " is in receiveProposal() and roundNum " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        #print(self.printReplica() + " in receiveProposal(), self.queue.checkQueue(self.roundNum) = " + str(self.queue.checkQueue(self.roundNum)) + " and self.queue.checkQueue(self.roundNum) != False implies " + str(self.queue.checkQueue(self.roundNum) != False))
        if(self.queue.checkQueue(self.roundNum) != -1):
            #print(self.printReplica() + " is inside receiveProposal() inside check queue if statement with a length of " + str(self.queue.getLength()))
            #print(self.printReplica() + " is inside receiveProposal() inside check queue if statment with self.queue.checkQueue(self.roundNum) = " + str(self.queue.checkQueue(self.roundNum)))
            
            while(self.queue.checkQueue(self.roundNum) != -1):
                print("Replica " + str(self.agentID) + " is processing messages in the queue in receiveProposal()")
                self.processPropose(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum))
            
        print(self.printReplica() + " is in receiveProposal() between the while() loops")
        while(True):
            timeConsumed = self.getTimeConsumed(startTime)

            print("Replica " + str(self.agentID) + " in receiveProposal() timeConsumed = " + str(timeConsumed))
            print("Replica " + str(self.agentID) + " in receiveProposal() roundTime = " + str(self.roundTime))
            print("Replica " + str(self.agentID) + " in receiveProposal() check #1 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            
            if(timeConsumed > self.roundTime):
                print("Replica " + str(self.agentID) + " has passed poll time in receiveProposal()")
                return
            print("Replica " + str(self.agentID) + " in receiveProposal() in between timeConsumed and poll")
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveProposal() with self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) = " + str(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000)))
            print("Replica " + str(self.agentID) + " in receiveProposal() check #2 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0): # messages are being received
                print("Replica " + str(self.agentID) + " is in receiveProposal() inside poll")
                receivedProposeMessage = self.receivingSocket.recv_pyobj()
                
                if(self.queue.checkMessage(self.agentID, self.roundNum, receivedProposeMessage)):
                    #print(self.printReplica() + " in receiveProposal() has polled a message from Replica " + str(receivedProposeMessage.messageSummary.agentID))
                    #print(self.printReplica() + " is before processPropose()")

                    self.processPropose(receivedProposeMessage)
                    #print(self.printReplica() + " is after processPropose()")
                    print("Replica " + str(self.agentID) + " received Propose Message from Replica " + str(self.receivedProposeMessage.agentID))
                        
                    #print("Replica " + str(self.agentID) + " is in receiveProposal() inside checkMessage if statement")
                       

            
            




    def printReplica(self):
        return "Replica " + str(self.agentID)
    
    
    def processCommit(self, receivedMessage):
        print("Replica " + str(self.agentID) + " is in processCommit() with receivedMessage from " + str(receivedMessage['agentID']))
        
        #print(self.printReplica() + " from Replica " + str(receivedMessage['agentID']) + " receivedMessage['proposal'].verify() = "  + str(receivedMessage['proposal'].verify()))
        #print(self.printReplica() + " from Replica " + str(receivedMessage['agentID']) + " receivedMessage['proposal'].value = " + str(receivedMessage['proposal'].value) + " and self.receivedProposalValue = " + str(self.receivedProposalValue))
        #print(self.printReplica() + " from Replica " + str(receivedMessage['agentID']) + " receivedMessage['commitMessage'].value = " + str(receivedMessage['commitMessage'].value) + " and self.receivedProposalValue = " + str(self.receivedProposalValue))
        #print(self.printReplica() + " from Replica " + str(receivedMessage['agentID']) + " receivedMessage['commitMessage'] not in self.tempCertificate = " + str(receivedMessage['commitMessage'] not in self.tempCertificate))

        if(receivedMessage['proposal'].verify() == True and receivedMessage['proposal'].value == self.receivedProposalValue):
            if(receivedMessage['commitMessage'] not in self.tempCertificate and receivedMessage['commitMessage'].value == self.receivedProposalValue):
                print("Replica " + str(self.agentID) + " appending commit message from Replica " + str(receivedMessage['commitMessage'].agentID) + " to certificate")
                self.tempCertificate.append(receivedMessage['commitMessage'])

        #print(self.printReplica() + " len(self.tempCertificate) = " + str(len(self.tempCertificate)))
        #print(self.printReplica() + " (self.numReplicas/2) + 1 = " + str((self.numReplicas/2) + 1))

        if(len(self.tempCertificate) >= (self.numReplicas/2) + 1):
            self.committedValue = self.receivedProposalValue # replica has commited
            self.hasCommited = True
            #print("Replica " + str(self.agentID) + " inside processCommit() set it's committedValue to " + str(self.committedValue))
            self.certificate = self.certificate + self.tempCertificate
            #print(self.printReplica() + " len(self.certificate) = " + str(len(self.certificate)))
            self.tempCertificate = [] #reset
            return
               



    def sendCommit(self):
        print("Replica " + str(self.agentID) + " is in sendCommit() with roundNum = " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        if(self.receivedProposalValue != None):
            commitMessage = CommitMessage.CommitMessage(self.agentID, self.iterationCounter, self.receivedProposalValue)
            forwardedMessage = {'agentID' : self.agentID, 'proposal' : self.receivedProposeMessage.messageSummary, 'commitMessage' : commitMessage}
            self.broadCast(forwardedMessage)
            return 


    def receiveCommit(self, startTime):
        #print("Replica " + str(self.agentID) + " is in receiveCommit()")
        print("Replica " + str(self.agentID) + " is in receiveCommit() with roundNum = " + str(self.roundNum) + " and iterationCounter = " + str(self.iterationCounter))
        #self.resetNumOfResponses()
        #print("Current roundNum for Replica " + str(self.agentID) + " in receiveCommit() is " + str(self.roundNum))
        #print("Replica " + str(self.agentID) + " in receiveCommit(), self.queue.checkQueue(self.roundNum) = " + str(self.queue.checkQueue(self.roundNum)))
        if(self.queue.checkQueue(self.roundNum) != -1):
            #print(self.printReplica() + " is inside receiveCommit() inside check queue if statement with a length of " + str(self.queue.getLength()))
            #print(self.printReplica() + " is inside receiveCommit() inside check queue if statment with self.queue.checkQueue(self.roundNum) = " + str(self.queue.checkQueue(self.roundNum)))
            while(self.queue.checkQueue(self.roundNum) != -1):
                print("Replica " + str(self.agentID) + " is processing messages in the queue in receiveCommit()")
                self.processCommit(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum))

        #print("Replica " + str(self.agentID) + " is in receiveCommit() between two while() with queue length of " + str(self.queue.getLength()) + " and roundNum of " + str(self.roundNum))
        while(True):
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveCommit() timeConsumed = " + str(timeConsumed))
            print("Replica " + str(self.agentID) + " in receiveCommit() roundTime = " + str(self.roundTime))
            print("Replica " + str(self.agentID) + " in receiveCommit() check #1 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            
            if(timeConsumed > self.roundTime):
                print("Replica " + str(self.agentID) + " has passed poll time in receiveCommit()")
                self.tempCertificate = [] #reset
                return

            print(self.printReplica() + " is in receiveCommit() in between the two while loops")
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveCommit() with self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) = " + str(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000)))
            print("Replica " + str(self.agentID) + " in receiveCommit() check #2 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0): # messages are being received
                print("Replica " + str(self.agentID) + " is in receiveCommit() inside poll")
                receivedMessage = self.receivingSocket.recv_pyobj()
                if(self.queue.checkMessage(self.agentID, self.roundNum, receivedMessage)): 
                    if(self.hasCommited != True):
                        self.processCommit(receivedMessage)
                        print("Replica " + str(self.agentID) + " received a Commit message")
               
           

    def sendNotify(self):
        #print("Replica " + str(self.agentID) + " is in sendNotify()") 
        print("Replica " + str(self.agentID) + " is in sendNotify() with roundNum = " + str(self.roundNum) + " and iterationCounter " + str(self.iterationCounter))
        if(self.hasCommited == True):
            messageSummary = NotifyMessage.NotifyMessageSummary(self.agentID, self.iterationCounter, self.committedValue)
            self.signMessage(messageSummary)
            notifyMessage = NotifyMessage.NotifyMessage(self.agentID, messageSummary, self.certificate)
            self.signMessage(notifyMessage)
            self.broadCast(notifyMessage)
            return


    
    def processNotify(self, receivedMessage):
        print("Replica " + str(self.agentID) + " is in processNotify() with roundNum = " + str(self.roundNum) + " and iterationCounter " + str(self.iterationCounter))
        receivedNotifyMessage = receivedMessage
        if(receivedNotifyMessage.verify() == True and receivedNotifyMessage.messageSummary.verify() == True and self.verifyCertificate(receivedNotifyMessage) == True):
            self.acceptedIterationNum = receivedNotifyMessage.messageSummary.iterationCounter
            self.certificate = receivedNotifyMessage.certificate
            self.committedValue = receivedNotifyMessage.messageSummary.value
            return 




    def receiveNotify(self, startTime):
        print("Replica " + str(self.agentID) + " is in receiveNotify() with roundNum = " + str(self.roundNum) + " and iterationCounter " + str(self.iterationCounter))
        if(self.queue.checkQueue(self.roundNum) != -1):
            while(self.queue.checkQueue(self.roundNum) != -1): # there are messages in the queue to process
                self.processNotify(self.queue.getQueueElement(self.queue.checkQueue(self.roundNum)))
                self.queue.deQueue(self.queue.checkQueue(self.roundNum))

        while(True):
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveNotify() timeConsumed = " + str(timeConsumed))
            print("Replica " + str(self.agentID) + " in receiveNotify() roundTime = " + str(self.roundTime))
            print("Replica " + str(self.agentID) + " in receiveNotify() check #1 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            if(timeConsumed > self.roundTime):
                print("Replica " + str(self.agentID) + " has passed poll time in receiveNotify()")
                return
            print("Replica " + str(self.agentID) + " is in receiveNotify() in between the two while loops")
            timeConsumed = self.getTimeConsumed(startTime)
            print("Replica " + str(self.agentID) + " in receiveNotify() with self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) = " + str(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000)))
            print("Replica " + str(self.agentID) + " in receiveNotify() check #2 timeConsumed - self.roundTime = " + str(timeConsumed - self.roundTime))
            if(self.receivingSocket.poll((self.roundTime - timeConsumed) * 1000) != 0):
                print("Replica " + str(self.agentID) + " is in receiveNotify() inside poll")
                receivedMessage = self.receivingSocket.recv_pyobj()
                if(self.queue.checkMessage(self.agentID, self.roundNum, receivedMessage)):
                    self.processNotify(receivedMessage)
                    print("Replica " + str(self.agentID) + " received a message from Replica " + str(receivedMessage.agentID) + " in receiveNotify()")



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




    """

    def byzantineBroadcast2(self, message): #    sends to other half of replicas
        for i in range(self.numReplicas/2, self.numReplicas):
            self.sendingSocket[i].send_pyobj(message)


    def byzantineBroadcast1(self, message): # sends to half of replicas
        for i in range(self.numReplicas/2):
            self.sendingSocket[i].send_pyobj(message)
    
        
         
        for i in range(self.numReplicas):
            if(self.totalReplicas[i].isByzantine == 0 or self.totalReplicas[i].isByzantine == 1):
                self.sendingSocket[i].send_json(message)
       

    def nonByzantineBroadcast(self, message): # sends to honest replicas only
        for i in range(self.numReplicas):
            if(self.totalReplicas[i].isByzantine == 2):
                self.sendingSocket[i].send_pyobj(message)


        """

    def broadCast(self, message):
        for i in range(self.numReplicas):
            self.sendingSocket[i].send_pyobj(message)


    
    def broadCastProposal(self, message):
        for i in range(self.numReplicas):
            print("Replica " + str(self.agentID) + " sending proposal message to " + str(i))
            self.sendingSocket[i].send_pyobj(message)

    def broadCastCommit(self, message):
        for i in range(self.numReplicas):
            print("Replica " + str(self.agentID) + " sending commit message to " + str(i))
            self.sendingSocket[i].send_pyobj(message)


    def broadCastNotify(self, message):
        for i in range(self.numReplicas):
            print("Replica " + str(self.agentID) + " sending notify message to " + str(i))
            self.sendingSocket[i].send_pyobj(message)



    



    def resetNumOfResponses(self):
        self.numOfResponses = 0

    























replica_isLeader = int(sys.argv[1])
replica_id = int(sys.argv[2])
replica_leaderID = int(sys.argv[3])
replica_isByzantine = int(sys.argv[4])
numReplicas = int(sys.argv[5])


replica = Replica(replica_isLeader == 1, replica_id, replica_leaderID, replica_isByzantine, [5886, 5887, 5888, 5889, 5890], numReplicas)
replica.start()


