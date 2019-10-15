import random
import time
import string
import threading
import _thread
from socket import *	
import ast
import sys
import hashlib
import config
from socket import error
import datetime
import pickle

import os.path
from os import path

initialBalances = {'A': 100, 'B': 100, 'C': 100, 'D': 100, 'E': 100}
timeOutDuration = 10



def calculateBalances(currentState):
	currentBalances = initialBalances.copy()
	for block in currentState['blockChain']:
		for transaction in block[1]:
			sender = transaction[0]
			receiver = transaction[1]
			amt = transaction[2]
			currentBalances[receiver] = currentBalances[receiver] + int(amt)
			currentBalances[sender] = currentBalances[sender] - int(amt)
			# print(currentBalances[receiver])
			# print(currentBalances[sender])
	return currentBalances


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


def turnLetterIntoNum(letter):
	if letter.upper() == 'A':
		return 0
	else:
		if letter.upper() == 'B':
			return 1
		else:
			if letter.upper() == 'C':
				return 2
			else:
				if letter.upper() == 'D':
					return 3
				else:
					if letter.upper() == 'E':
						return 4



def balGreaterThanOrEqual(bal,BallotNum):
	# print(str(bal) + ' ' + str(BallotNum))
	if int(bal[0]) > int(BallotNum[0]):
		return True
	else:
		if int(bal[0]) == int(BallotNum[0]) and int(bal[1] > BallotNum[1]):
			return True
		else:
			if int(bal[0] == BallotNum[0]) and int(bal[1])== int(BallotNum[1]):
				return bal[2] >= BallotNum[2]
	return False

def saveState(currentState):
	saveState = currentState.copy()
	saveState['state']= 'N/A'
	saveState['acceptVal']= 'N/A'
	saveState['acceptBal']= 'N/A'
	saveState['value']= 'N/A'
	saveState['BallotNum']= (0,0,currentState['proc_num'])
	saveState['mostRecentResponse'] = 'N/A'
	saveState['messagesReceived'] = []
	saveState['transactions'] = []
	saveState['inSync'] = True

	# print(str(saveState))
	# print(str(currentState))
	pickle.dump(saveState,open( 'save' + str(currentState['proc_num']) + '.txt', "wb" ))

def readState(currentState):
	if path.exists("save" + str(currentState['proc_num'] ) + ".txt" ):
		currentState = pickle.load( open( "save" + str(currentState['proc_num']) +'.txt' , "rb" ) ) 
	return currentState

def sendPropAck(message,currentState,NWSock):
	newMessage = {}
	newMessage['type'] = 'prop_ack'
	newMessage['bal'] = message['bal']
	newMessage['acceptBal'] = currentState['acceptBal']
	newMessage['acceptVal'] = currentState['acceptVal']
	newMessage['destination'] = message['sender']
	newMessage['sender'] = message['destination']
	NWSock.send(bytes(str(newMessage)+ '%', encoding='utf8'))
	return 0


def sendAccAck(message,NWSock):
	newMessage = {}
	newMessage['type'] = 'acc_ack'
	newMessage['bal'] = message['bal']
	print('Sent acc ack message with ballowNum: ' + str(newMessage['bal']))
	newMessage['value'] = message['value']
	newMessage['destination'] = message['sender']
	newMessage['sender'] = message['destination']
	NWSock.send(bytes(str(newMessage)+ '%', encoding='utf8'))
	return 0

def sendPropMessages(currentState,NWSock,newBlock):
	newMessage = {}
	newMessage['type'] = 'prop'
	newMessage['bal'] = (getDepthNumFromBlock(newBlock),currentState['BallotNum'][1] +1,currentState['proc_num'])
	#print(newMessage['bal'])
	newMessage['sender'] = currentState['proc_num']
	currentState['messagesReceived'] = []
	currentState['state'] = 'waiting for prop_ack'
	currentState['value'] = newBlock
	print('Sending prop messages with ballot num: ' + str(newMessage['bal']))
	for server in [0,1,2,3,4]:
		newMessage['destination'] = server
		if newMessage['destination'] == newMessage['sender']:
			receiveMessage(newMessage,currentState,NWSock)
		else:
			NWSock.send(bytes(str(newMessage) + '%', encoding='utf8'))
	return 0



def sendDecisionMessages(currentState,NWSock):
	newMessage = {}
	newMessage['type'] = 'decision'
	newMessage['bal'] = currentState['messagesReceived'][0]['bal']
	newMessage['value'] = currentState['messagesReceived'][0]['value']
	newMessage['sender'] = currentState['messagesReceived'][0]['destination']
	for server in [0,1,2,3,4]:
		newMessage['destination'] = server
		if newMessage['destination'] == newMessage['sender']:
			receiveMessage(newMessage,currentState,NWSock)
		else:
			NWSock.send(bytes(str(newMessage) + '%', encoding='utf8'))
	return 0

def sendAccMessages(currentState,NWSock):
	value = None

	b = (len(currentState['blockChain']) + 1,-999,-999)
	for message in currentState['messagesReceived']:
		if message['acceptVal'] != 'N/A':
			if balGreaterThanOrEqual(message['acceptBal'],b):
				value = message['acceptVal']
				b= message['acceptBal']
	# print('')
	# print('acceptVal is: ' + str(value))
	
	newMessage = {}
	newMessage ['type'] = 'acc'
	newMessage ['bal'] = currentState['messagesReceived'][0]['bal']
	print("sending acc messages with ballot number: " + str(newMessage['bal']))
	# print('bal remains: ' + str(newMessage['bal']))	
	# print('')

	if value is not None:
		newMessage['value'] = value
	else:
		newMessage['value'] = currentState['value']
	newMessage['sender'] = currentState['messagesReceived'][0]['destination']

	currentState['messagesReceived'] = []
	currentState['state'] = 'waiting for acc_ack'

	for server in [0,1,2,3,4]:
		newMessage['destination'] = server
		if newMessage['destination'] == newMessage['sender']:
			receiveMessage(newMessage,currentState,NWSock)
		else:
			NWSock.send(bytes(str(newMessage)+ '%' , encoding='utf8'))

def sendSync(currentState,NWSock):
	#synchronize if new block is not the next block
		newMessage = {}
		newMessage['type'] = 'sync'
		newMessage['blockChainLength'] = len(currentState['blockChain'])
		newMessage['bal'] = currentState['BallotNum']
		newMessage['sender'] = currentState['proc_num']

		for server in [0,1,2,3,4]:
			newMessage['destination'] = server
			if newMessage['destination'] == newMessage['sender']:
				pass
			else:
				NWSock.send(bytes(str(newMessage)+ '%' , encoding='utf8'))



def sendSyncResponse(currentState,message,NWSock):
	newMessage = {}
	newMessage['type'] = 'sync-response'
	newMessage['data'] = currentState['blockChain'][message['blockChainLength']:]
	# print('SYNCING WITH DATA: ' + str(newMessage['data']))
	newMessage['bal'] = currentState['BallotNum']
	newMessage['sender'] = message['destination']
	newMessage['destination'] = message['sender']

	NWSock.send(bytes(str(newMessage) + '%', encoding='utf8'))



def sendTransSet(currentState,NWSock):
	newMessage = {}
	newMessage['type'] = 'trans-set'
	newMessage['sender'] = currentState['proc_num']
	newMessage['destination'] = -1
	newMessage['transactions'] = currentState['transactions']
	NWSock.send(bytes(str(newMessage) + '%', encoding='utf8'))

def sendBalance(currentState,NWSock):

	newMessage = {}
	newMessage['type'] = 'balances'
	newMessage['sender'] = currentState['proc_num']
	newMessage['destination'] = -1
	newMessage['balances'] = calculateBalances(currentState)
	newMessage['depth'] = len(currentState['blockChain'])

	NWSock.send(bytes(str(newMessage) + '%', encoding='utf8'))


def sendBlockChain(currentState,NWSock):
	newMessage = {}
	newMessage['type'] = 'blockchain'
	newMessage['sender'] = currentState['proc_num']
	newMessage['destination'] = -1
	newMessage['blockChain'] = currentState['blockChain']
	NWSock.send(bytes(str(newMessage) + '%', encoding='utf8'))

def rejectTrans(transaction,NWSock,currentState):
	newMessage = {}
	newMessage['type'] = 'failure'
	newMessage['sender'] = currentState['proc_num']
	newMessage['destination'] = -1
	newMessage['msg'] = 'Transaction Failed'
	newMessage['data'] = transaction
	NWSock.send(bytes(str(newMessage)+ '%' , encoding='utf8'))


def receiveDecision(currentState,message,NWSock):
	if currentState['proc_num'] == message['sender']:		
		currentState['state'] = 'N/A'


	#print(message['value'])
	if len(currentState['blockChain']) + 1 != getDepthNumFromBlock(message['value']):

		# print('New block is not the next value')
			
		if len(currentState['blockChain']) == getDepthNumFromBlock(message['value']):
			currentState['mostRecentResponse'] = datetime.datetime.now()
		else:
			print('Received decision out of order, updating blockchain now for all blocks past block depth:' + str(len(currentState['blockChain'])))
			sendSync(currentState,NWSock)
	else:
		# The block is the next in the chain. Now we validate the transactions
		validityCheck = checkIfTransactionsAreValid(currentState,NWSock, message['value'])
		#print(validityCheck)
		if validityCheck == [True,True]:
			#print('VALID')
			#if decided value is from this proc_num
			print('Received validated block decision: ' + str(message['value']))
			print('')
			# print('SAVE STATE OUTPUT BELOW:')
			# because we added a new block, we have to reset paxos states
			currentState['state'] = 'N/A'
			currentState['value'] = 'N/A'
			currentState['acceptBal'] = 'N/A'
			currentState['acceptVal'] = 'N/A'
			currentState['mostRecentResponse'] = 'N/A'

			currentState['messagesReceived'] = []
			currentState['blockChain'].append(message['value'])

			currentState['BallotNum'] = (len(currentState['blockChain']),0,-1)


			if currentState['proc_num'] == turnLetterIntoNum(message['value'][1][0][0]):
				trans = currentState['transactions'][:2]
				currentState['transactions'].remove(trans[0])
				currentState['transactions'].remove(trans[1])

			saveState(currentState)
		else:
			print('Invalid transactions')
			currentState['acceptVal']= 'N/A'
			currentState['acceptBal']= 'N/A'

						# if transactions are not valid:
			# print(str(currentState['transactions']))
			if currentState['proc_num'] == message['sender']:
				# print('Making state N/A')
				currentState['state'] = 'N/A'
				currentState['mostRecentResponse'] = "N/A"
				trans = currentState['transactions'][:2]

				if validityCheck[1] == False:
					rejectTrans(trans[1],NWSock,currentState)
					currentState['transactions'].remove(trans[1])
					# print('1 BAD ' + str(currentState['transactions']))
				if validityCheck[0] == False:
					rejectTrans(trans[0],NWSock,currentState)
					currentState['transactions'].remove(trans[0])
					# print('0 BAD ' + str(currentState['transactions']))

				

	# print('NEW BLOCKCHAIN CREATED:')
	# for block in currentState['blockChain']:
	# 	print(str(block))

			# if some transactions are invalid:

		# I dont think we need to use this:
		# currentState['BallotNum'] = (len(blockChain), currentState['BallotNum'][1],currentState['proc_num'])


def receiveMessage(message,currentState,NWSock):

	if message['type'] =='prop_ack' and currentState['state'] == 'waiting for prop_ack':
		print('Received prop_ack with ballot number: ' + str(message['bal']) )
		currentState['messagesReceived'].append(message)
		currentState['mostRecentResponse'] = datetime.datetime.now()
		if len(currentState['messagesReceived']) >= 3:
			sendAccMessages(currentState,NWSock)
	else:
		if message['type'] == 'acc_ack' and currentState['state'] == 'waiting for acc_ack':
			print('Received acc_ack with ballot number: ' + str(message['bal']) )
			currentState['messagesReceived'].append(message)
			currentState['mostRecentResponse'] = datetime.datetime.now()

			if len(currentState['messagesReceived']) >= 3:
				sendDecisionMessages(currentState,NWSock)
		else:
			if message['type'] == 'prop':
				print('Received prop with ballot number: ' + str(message['bal']) )
				if balGreaterThanOrEqual(message['bal'],currentState['BallotNum']):
					currentState['BallotNum'] = message['bal']
					sendPropAck(message,currentState,NWSock)
			else:
				if message['type'] == 'acc':
					print('Received acc with ballot number: ' + str(message['bal']) )
					if balGreaterThanOrEqual(message['bal'],currentState['BallotNum']):
						currentState['acceptBal']=message['bal']
						currentState['acceptVal'] = message['value']
						sendAccAck(message,NWSock)
				else:
					if message['type'] == 'decision':
						print('Received decision from message with ballot number: ' + str(message['bal']) )
						receiveDecision(currentState,message,NWSock)
					else:
						if message['type'] == 'sync':
							print('Received request to sync from process ' + str(message['sender']))
							sendSyncResponse(currentState,message,NWSock)
						else:
							if message['type'] == 'sync-response':

								print('Received data from server: ' + str(message['sender']))
								
								for block in message['data']:
									# print('Received :' + str(block))
									# Test if block is to be the next block in the chain
									if getDepthNumFromBlock(block) == len(currentState['blockChain']) + 1:
										currentState['blockChain'].append(block)
										print('Updated the blockchain')
										saveState(currentState)
								currentState['inSync'] = True

							else:
								if message['type'] == 'transaction':
									print('Received transaction request from client')
									currentState['transactions'].append(message['transaction'])
									print('Transaction List is now: ' + str(currentState['transactions']))
								else:
									if message['type'] == 'print_set':
										sendTransSet(currentState,NWSock)
									else:
										if message['type'] == 'print_balance' and currentState['inSync']:
											sendBalance(currentState,NWSock)
										else:
											if message['type'] ==  'print_blockchain' and currentState['inSync']:
												sendBlockChain(currentState,NWSock)
	return 0

#added blockChain field for initialization
def initiateCurrentState(proc_num):
	currentState = {}
	currentState['state']= 'N/A'
	currentState['acceptVal']= 'N/A'
	currentState['acceptBal']= 'N/A'
	#is default value for when a block is successfully mined:
	currentState['value']= 'N/A'
	currentState['BallotNum']= (0,0,proc_num)
	currentState['proc_num']= proc_num
	currentState['mostRecentResponse'] = 'N/A'
	currentState['messagesReceived'] = []
	currentState['transactions'] = []
	currentState['blockChain'] = []
	currentState['inSync'] = True
	currentState = readState(currentState)
	return currentState

def get_random_string():
	random_str = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]) #length of 10
	return random_str


def isValidBlock(block):
	# (depth, prevhash, nonce) = block[0]
	# transactions = block[1]
	# # print(depth, prevhash, nonce)
	# # print(transactions)
	# trans1 = str(transactions[0][0]) + " " + str(transactions[0][1] + " " + str(transactions[0][2]))
	# trans2 = str(transactions[1][0]) + " " + str(transactions[1][1]) + " " + str(transactions[1][2])
	# string_to_hash = trans1 + trans2 + nonce
	hash_value = hashlib.sha256(str(block).encode()).hexdigest()
	# print( str(hash_value[-1] ))
	if str(hash_value[-1]) == str(0) or str(hash_value[-1]) == str(1):
		return True
	else:
		return False

# TODO for ajit: put in the correct way to access depth number in the block
# Everything in slashes below needs to be replaced with the right thing based on how you organize the data structures
def getDepthNumFromBlock(block):
	return block[0][0]
	# checked function and its works

#do we want to return bal as well?
def checkIfTransactionsAreValid(currentState,NWSock,new_block):
	trans = new_block[1]
	bal= dict(calculateBalances(currentState))
	transCorrect = [True,True]
	# print(str(trans))
	for transact in [0,1]:
		sender = trans[transact][0]
		rec = trans[transact][1]
		amt = trans[transact][2]
		# print(str(amt))
		# print(type(sender), type(rec), type(amt)) #type string
		# print(type(bal[sender])) #type int
		# print(str(bal))
		# print(str(int(bal[sender]) - int(amt)))
		if bal[sender] - int(amt) < 0:
			transCorrect[transact] = False
		else:
			bal[sender] = bal[sender] - int(amt)
			# print(str(bal[sender]))
	return transCorrect

#TODO ajit: Create the block from currentState. Everything you need to make it is there.
# We will only be generating the block once every round until it works. Youll need to calculate hash of previous block and stuff too
#tested and works
def createBlock(currentState):
	# call get_random_string() to generate nonce
	transactions = currentState['transactions'][:2]
	# print(transactions[0])
	blockChain = currentState['blockChain']
	nonce = get_random_string()
	# print(nonce)
	depth_newblock = len(blockChain) + 1
	# print('New created block has depth: ' + str(depth_newblock))
	# print(depth_newblock)
	prevBlockStr = 'NULL'
	if depth_newblock > 1:
		prevBlockStr = str(currentState['blockChain'] [-1])
		prevBlockStr=  hashlib.sha256(prevBlockStr.encode()).hexdigest()

		# prev_transaction_1 = str(blockChain[len(blockChain)-1][1][0][0]) + " " + str(blockChain[len(blockChain)-1][1][0][1]]) + " " + str(blockChain[len(blockChain)-1][1][0][2])
		# prev_transaction_2 = str(blockChain[len(blockChain)-1][1][1][0]) + " " + str(blockChain[len(blockChain)-1][1][1][1])) + " " + str(blockChain[len(blockChain)-1][1][1][2])
		# prev_depth = blockChain[len(blockChain)-1][0][0]
		# hash_prev = blockChain[len(blockChain)-1][0][1]
		# prev_nonce = blockChain[len(blockChain)-1][0][2]
		# string_hash =  prev_transaction_1 + prev_transaction_2 + str(prev_depth) + hash_prev + prev_nonce
		# prev_hash =


	head_of_block = (depth_newblock,prevBlockStr, nonce)
	transactions_in_block = []
	transactions_in_block.append(transactions[0])
	transactions_in_block.append(transactions[1])
	block = (head_of_block, transactions_in_block)
	return block

def connectToNetwork(proc_num):
	NWSock = socket(AF_INET, SOCK_STREAM)
	while True:
		try:
			NWSock.connect(('127.0.0.1', config.serverPortNumber))
			break
		except:
			pass

	NWSock.send(bytes(str(proc_num), encoding='utf8'))
	NWSock.setblocking(0)
	return NWSock




def blockEquals(block1,block2):
	if block1 =='' or block2 == '':
		return False

	if block1[0][0] == block2[0][0] and block1[0][1] == block2[0][1]:
		for transaction1,transaction2 in zip(block1[1],block2[1]):
			if transaction1[0] != transaction2[0] or transaction1[1] != transaction2[1] or transaction1[2] != transaction2[2]:
				return False
	else:
		return False

	return True

def run(proc_num):

	currentState = initiateCurrentState(proc_num)
	# print(currentState)
	lastValidBlock = ''

	NWSock = connectToNetwork(currentState['proc_num'])
	print('NW Connected')

	while True:
		messageString = ''
		try:
			messageString = NWSock.recv(4096).decode('utf-8')

		except:
			pass

		if messageString != '':
			messages = separateMessages(messageString)
			for message in messages:
				messageDict = ast.literal_eval(message)
				# print('Received message' + str(messageDict))
				receiveMessage(messageDict,currentState,NWSock)


		# if currentState['mostRecentResponse'] != "N/A":
		# 	currentTime = datetime.datetime.now()
		# 	#get time passed since this response
		# 	if (currentTime - currentState['mostRecentResponse']).seconds > timeOutDuration:
		# 		print('Not received any responses to request. Proposition failed. Attempting to update blockChain')
		# 		sendSync(currentState,NWSock)
		# 		lastValidBlock = ''


		if(len(currentState['transactions']) > 1 and currentState['inSync']):
			#creates block based on current state.
			block = createBlock(currentState)
			if blockEquals(block,lastValidBlock):
				# print('Block NOT equals')
				#this means that we have already calculated the right nonce, and because we create block from current state, we know that the block is valid for being the next value
				# so a block hasnt been proposed yet and this block is able to be the next one if paxos is down.
				pass
			else:
				if isValidBlock(block):
					print("Found a valid block for transactions: " + str(currentState['transactions'][0]) +' ' + str(currentState['transactions'][1]) )
					sendPropMessages(currentState,NWSock,block)
					lastValidBlock = block
		# receive message and then process if received

		if currentState['mostRecentResponse'] != "N/A":
			currentTime = datetime.datetime.now()
			#get time passed since this response
			if (currentTime - currentState['mostRecentResponse']).seconds > timeOutDuration:
				print('Not received any responses to request. Proposition failed. Requesting blockchain update before recalculating block')
				sendSync(currentState,NWSock)
				lastValidBlock = ''
				currentState['mostRecentResponse'] = "N/A"
				currentState['inSync'] = False
				


### MAIN STARTS HERE

run(proc_num = int(sys.argv[1]))