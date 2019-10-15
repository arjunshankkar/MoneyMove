import random
from socket import *
import threading
import _thread
import time
import config
import ast
import hashlib


def connectToNetwork(proc_num):
	NWSock = socket(AF_INET, SOCK_STREAM)

	while True:
		try:
			NWSock.connect(('127.0.0.1', config.serverPortNumber))
			break
		except:
			pass
	NWSock.send(bytes(str(proc_num), encoding='utf8'))
	return NWSock

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

def sendTransaction(transaction, NWSock):
	newMessage = {}
	newMessage['type'] = 'transaction'
	newMessage['sender'] = -1
	newMessage['destination'] = turnLetterIntoNum(transaction[0])
	newMessage['transaction'] = transaction
	NWSock.send(bytes(str(newMessage) + '%' , encoding='utf8'))


def listen(connection):
	try:
		while True:
			msg = connection.recv(4096).decode()
			print(msg)
	finally:
		connection.close()

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


def sendCustom(NWSock,request, node):
	newMessage = {}
	newMessage['type'] = request
	newMessage['sender'] = -1
	newMessage['destination'] = turnLetterIntoNum(node)
	NWSock.send(bytes(str(newMessage) + '%' , encoding='utf8'))


def checkForMessages(NWSock,clientState):
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
				receiveMessage(messageDict,clientState)


def receiveMessage(messageDict,clientState):
	# print('Receiving message')

	if messageDict['type'] == 'blockchain' and clientState['receivedBloc'] == False:
		clientState['receivedBloc'] = True

		print('BlockChain received:')
		for block in messageDict['blockChain']:
			print (str(block))
	else:
		if messageDict['type'] == 'balances' and clientState ['receivedBal'] == False:
			clientState['receivedBal'] = True

			print('Balances received:')
			for bal in messageDict['balances']:
				print(str(bal) + ': ' + str(messageDict['balances'][bal]))
		else:
			if messageDict['type'] == 'trans-set':
				print('Set of transactions recorded at: ' + str(messageDict['sender']))
				for trans in messageDict['transactions']:
					print(str(trans))
			else:
				if messageDict['type'] == 'failure':
					print('Transaction ' + str(messageDict['data']) + ' failed. ')



def interpretInput(input,NWSock):

	transaction = input.split()
	if transaction[0].upper() == 'printBlockchain'.upper():
		sendCustom(NWSock,'print_blockchain', transaction[1].upper())
		clientState['receivedBloc'] = False
	else:
		if transaction[0].upper() == 'printBalance'.upper():
			sendCustom(NWSock,'print_balance', transaction[1].upper())
			clientState['receivedBal'] = False
		else:
			if transaction[0].upper() == 'printSet'.upper():
				sendCustom(NWSock,'print_set',transaction[1].upper())
				clientState['receivedSet'] = False
			else:
				if len(transaction) == 3:
					(sender, receiver, value) = transaction
					transaction = (sender.upper(), receiver.upper(), value)
					sendTransaction(transaction,NWSock)

NWSock = connectToNetwork(-1)
NWSock.setblocking(0)
clientState ={}
clientState['receivedBal'] = False
clientState['receivedBloc'] = False


_thread.start_new_thread(checkForMessages,(NWSock,clientState ))

while(True):
	print('Please input a command:')
	print('printBlockchain')
	print('printBalance')
	print('printSet')
	print('moneyTransfer: must be in form: A B 20 , A-E only')
	inputVal = input('')
	interpretInput(inputVal,NWSock)