import random
from socket import *
import socket
import time
import threading
import _thread
import ast
import hashlib


def networkPartition():
    nwPartition = '01234'
    while True:
        with open('partition.txt', 'w') as f:
            f.write(str(nwPartition))
        print('Input partition string: ')
        nwPartition= input()
        print('New partition string: ' + str(nwPartition))
       

def sendMessageWithDelay(message, destination,destinationInt,senderInt):
    sleepAmnt = random.uniform(0, 4)
    # print('Sending message: ' + str (message))
    if inPartition(senderInt,destinationInt):
        time.sleep(sleepAmnt)
        destination.send(bytes(message + '%',encoding='utf-8'))

def inPartition(sender,destination):
    partitionStr = ''
    with open('partition.txt', 'r') as f:
        connectionsString = f.readlines()[0]

    if sender == -1 or destination == -1:
        return True

    for partition in connectionsString.split():
        if partition.find(str(sender)) > -1 and partition.find(str(destination)) > -1:
            return True
    return False



def separateMessages(message):
    remainingMessage = message
    messageStrings = []
    while len(remainingMessage) > 3:
        messageStrings.append(remainingMessage[:remainingMessage.find('%')])
        if len(remainingMessage[remainingMessage.find('%') :]) > 3:
            remainingMessage = remainingMessage[remainingMessage.find('%') + 1:]
        else:
            remainingMessage = ''
    return messageStrings



def bindSocketAndSave():
    serverPortNumber = 3456

    serverListener = socket.socket()

    while True:

        try:
            serverListener.bind(('', serverPortNumber))
            break
        except:
            serverPortNumber = serverPortNumber + 1
            pass
    print('Bound on port: ' + str(serverPortNumber))
    with open('config.py', 'w') as f:
        f.write('serverPortNumber =' + str(serverPortNumber))

    serverListener.listen(5)
    serverListener.setblocking(0)

    return serverListener


def startNetwork():
    
    serverListener = bindSocketAndSave()

    serverSockets = {}


    _thread.start_new_thread(networkPartition,( ))


    while True:
        # Try to accept other server connections
        try:

            sock, addr1 = serverListener.accept()
            procID = sock.recv(4096).decode('utf-8')

            print('Started connection with server: ' + procID)

            sock.setblocking(0)
            serverSockets[procID] = sock 
        except socket.error as err:
            pass

            
# Send messages with delay
        for socketVar in serverSockets.values():
            try:
                messageString = socketVar.recv(4096).decode('utf-8')

                if messageString != '':
                    messages = separateMessages(messageString)
                    for message in messages:
                        print('Received message: ' + message)

                        messageDict = ast.literal_eval(message)
                        if str(messageDict['destination']) in serverSockets:
                            sendThread = threading.Thread(target=sendMessageWithDelay, args=(message, serverSockets[str(messageDict['destination'])],messageDict['destination'],messageDict['sender']) )
                            sendThread.start()

            except socket.error as err:
                pass

startNetwork()