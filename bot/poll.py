import json
import os
import datetime

class Poll(object):
	def __init__(self):
		super(Poll, self).__init__()
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.pollData = json.load(open(self.binpath+"poll.json"))

	#Creats a new Poll-Entry with unique ID. Lowest ID possible.
	#Returns the pollID
	def newPoll(self, pollName):
		pollID=1
		while self.isAPollID(pollID):
			pollID += 1
		self.pollData[str(pollID)]={'name':str(pollName),'datum':str(datetime.datetime.now())[:19],'status':'CLOSED','messageID':['',''],'options':[], 'votes':[]}
		self.savePollData()
		return pollID

	#Returns a list of all PollsIDs
	def getAllPolls(self):
		return [x for x in self.pollData]

	#Tests if a given ID is in pollData
	#Returns True, if is in pollData. False otherwise.
	def isAPollID(self, pollID):
		if str(pollID).isdigit():
			return str(pollID) in self.getAllPolls()
		return False

	#Get the Status of a poll
	#Returns the Status. If pollID is not in pollData return ""
	def getStatus(self, pollID):
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]["status"]
		return ""

	#Gets the list of all options in a poll.
	#Returns a list containg [optionName,Votes]. If pollID is not in pollData return []
	def getOptions(self, pollID):
		if self.isAPollID(pollID):
			return [x for x in self.pollData[str(pollID)]["options"]]
		return []

	#Checks if a option is in the poll.
	#Returns False if there is no such poll, there are no options or the optionName is not in the poll. Else returns True
	def isInOptions(self, pollID, optionName):
		if self.getOptions(pollID) != None:
			return optionName in [x[0] for x in self.getOptions(pollID)]
		return False

	#Option consists of optionName, votes, optionNumber
	#Adds an option to the poll.
	#If the option is allready in the poll, the poll does not exist or the poll is closed or has more than 5 options, return False. Else adds the option to the poll and returns True.
	def optionAdd(self, pollID, optionName, votes):
		if self.getStatus(pollID) == "CLOSED" and not self.isInOptions(pollID, optionName) and not len(self.getOptions(pollID)) >= 7:
			number = 1
			numbers = []
			for option in self.getOptions(pollID):
				numbers.append(option[2])
			while number in numbers:
				number += 1
			self.pollData[str(pollID)]["options"].append([str(optionName),votes, number])
			self.savePollData()
			return True
		return False

	#Removes an option from a poll
	#If the option is not in the poll, the poll does not exist or is closed the returns False. Else delets the option and returns True.
	def optionRemove(self, pollID, optionName):
		if self.getStatus(pollID) == "CLOSED":
			options = self.getOptions(pollID)
			if options != None:
				number = 1
				for x in options:
					if x[0] == optionName:
						self.pollData[str(pollID)]["options"].remove(x)
						self.removeOptionVotes(pollID, optionName)
						number = x[2]
						break
				temp = self.pollData[str(pollID)]["options"]
				for i in range(1, len(options)+1):
					if number < int(temp[i][2]):
						self.pollData[str(pollID)]["options"][i][2] = int(self.pollData[str(pollID)]["options"][i][2]) -1
				self.savePollData()
				return True
		return False

	#Opens the poll
	#If the poll exists and the poll is CLOSED it opens the poll and returns True. Else return False.
	def pollOpen(self, pollID):
		status = self.getStatus(pollID)
		if status == "CLOSED" and len(self.getOptions(pollID)) > 1:
			self.pollData[str(pollID)]['status'] = "OPEN"
			self.savePollData()
			return True
		return False

	#Closes the poll
	#If the poll exists and the poll is Open it closes the poll and returns True. Else return False.
	def pollClose(self, pollID):
		status = self.getStatus(pollID)
		if status == "OPEN":
			self.pollData[str(pollID)]['status'] = "CLOSED"
			self.savePollData()
			return True
		return False

	#Publishes the poll
	#If the poll exists and the poll is Open it publishes the poll and returns True. Else return False.
	def pollPublish(self, pollID):
		status = self.getStatus(pollID)
		if status == "OPEN":
			self.pollData[str(pollID)]['status'] = "PUBLISHED"
			self.savePollData()
			return True
		return False						

	#Get the votes of a option in a poll
	#If poll exists and options is in the poll then returns the votes. Else returns -1
	def getVotesOfOption(self, pollID, optionName):
		if self.isAPollID(pollID):
			options = self.getOptions(pollID)
			if options != None:
				for x in options:
					if x[0] == optionName:
						return x[1]
		return -1

	#Sets the votes of an option in a poll to a set amount
	#Returns True, if the operation is succesfull. Otherwise Flase.
	def setVotesOfOption(self, pollID, optionName, votes):
		if self.isAPollID(pollID):
			for i in range(len(self.getOptions(pollID))):
				copy = self.pollData[str(pollID)]["options"][i]
				if copy[0] == str(optionName):
					self.pollData[str(pollID)]["options"][i] = [copy[0], votes, copy[2]]
					self.savePollData()
					return True
		return False


	#Increments the votes of an option in a poll
	#Returns True if the operation was succesfull. Else false.
	def incVotesOfOption(self, pollID, optionName):
		votes = self.getVotesOfOption(pollID, optionName)
		re = self.setVotesOfOption(pollID, optionName, votes+1)
		self.savePollData()
		return re

	#Decrements the votes of an option in a poll
	#Returns True if the operation was succesfull. Else false.
	def decVotesOfOption(self, pollID, optionName):
		re = False
		votes = self.getVotesOfOption(pollID, optionName)
		if votes <= 0:
			return re
		re = self.setVotesOfOption(pollID, optionName, votes-1)
		self.savePollData()
		return re

	#Gets the optionName from the optionNumber
	#Returns the Name if all is succesful, else return ""
	def getOptionByNumber(self, pollID, optionNumber):
		for option in self.getOptions(pollID):
			if option[2] == optionNumber:
				return option[0]
		return ""

	#Get the votes by users
	#Returns the votes by users if the pollID exists. Else return {}.
	def getVotes(self, pollID):
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]['votes']
		return {}

	#Test if a user voted in a poll.
	#Returns false if poll does not exist or user has not voted for this poll. Else return True.
	def hasUserVote(self, pollID, userID):
		for vote in self.getVotes(pollID):
			if vote[0] == userID:
				return True  
		return False

	#Gets the vote of a User.
	#If poll does not exist or user has not voted than returns []. Else returns the vote of the user.
	def getUserVote(self, pollID ,userID):
		if self.hasUserVote(pollID, userID):
			for vote in self.getVotes(pollID):
				if vote[0] == userID:
					return vote
		return []

	#Adds the vote of a user. If user has already voted, than removes the previes vote.
	#If the user vote is added succesful than returns True. Else False.
	def addUserVote(self, pollID, userID, optionName):
		if self.isAPollID(pollID):
			if self.isInOptions(pollID, optionName):
				if self.hasUserVote(pollID, userID):
					userVote = self.getUserVote(pollID, userID)
					self.decVotesOfOption(pollID, userVote[1])
					self.removeUserVote(pollID, userID)
				self.pollData[str(pollID)]['votes'].append([userID, optionName])
				self.incVotesOfOption(pollID, optionName)
				self.savePollData()
				return True
		return False

	#removes the vote of a user.
	#returns True only if the user vote was removed from the poll. Else returns False.
	def removeUserVote(self, pollID, userID):
		if self.isAPollID(pollID):
			vote = self.getUserVote(pollID, userID)
			if vote != []:
				self.pollData[str(pollID)]['votes'].remove(vote)
				return True
		return False

	#Removes all votes with the given optionName
	#Returns True if the votes where succefully removed. Else return Flase.
	def removeOptionVotes(self, pollID, optionName):
		if self.isAPollID(pollID):
			if self.isInOptions(pollID, optionName):
				votes = getVotes(pollID)
				for vote in votes:
					if vote[1] == optionName:
						self.pollData[str(pollID)]['votes'].remove(vote)
				return True
		return False

	#Get the sum of all votes and returns them.
	def getSumVotes(self, pollID):
		s = 0
		for option in self.getOptions(pollID):
			s += int(option[1])
		return s

	#Sets messageID of Poll
	#If operation succesful, return True, else False.
	def setMessageID(self, pollID, messageID, channelID):
		if self.isAPollID(pollID):
			self.pollData[str(pollID)]["messageID"] = [messageID, channelID]
			self.savePollData()
			return True
		return False

	#Gets the poll name
	#Returns the name of the poll, if poll exists. Otherwise returns None. 
	def getName(self, pollID):
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]['name']
		return None

	#Returns MessageID of Poll
	#Returns messageID, if poll exists, else -1
	def getMessageID(self, pollID):
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]["messageID"]
		return -1

	#Gets the date of a poll
	#If no poll exists, return 0, else the date of the poll.
	def getDate(self, pollID):
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]["datum"]
		return 0

	#Removes a poll.
	#If the poll exists, then removes the poll and returns True. Else return False.
	def removePoll(self, pollID):
		if self.isAPollID(pollID):
			del self.pollData[str(pollID)]
			self.savePollData()
			return True
		return False

	#saves pollData to poll.json
	def savePollData(self):
		with open(self.binpath+"poll.json",'w') as f:
			json.dump(self.pollData, f ,indent = 6)
		self.pollData = json.load(open(self.binpath+"poll.json"))

	#Sorts the options of a poll by votes(1) or by optionNumber(2)
	#Returns [] when pollID does not exist. Else returns options sorted by sortBy. 
	def sortOptionsBy(self, pollID, sortBy):
		if not (sortBy == 1 or sortBy == 2):
			return []
		reOptions = []
		options = self.getOptions(pollID)
		if len(options) == 0:
			return []
		reOptions.append(options[0])
		for option in options[1:]:
			i = len(reOptions)-1
			while i >= 0 and option[sortBy] >= reOptions[i][sortBy]:
				i -= 1
			reOptions.insert(i+1, option)
		if sortBy == 1:
			return reOptions[::-1]
		return reOptions

	#Resets the votes of a poll.
	#Returns true if the poll exists. Otherwise return False.
	def resetVotes(self, pollID):
		if self.isAPollID(pollID):
			for option in self.getOptions():
				self.setVotesOfOption(pollID, option[0], 0)
			self.pollData[str(pollID)]["votes"] = []	
			return True
		return False

	#Generates the poll header.
	#Returns the poll header a String. If pollID does not exist returns an empty String
	def pollHeader(self, pollID):
		if self.isAPollID(pollID):
			name = str(self.getName(pollID))
			datum = str(self.getDate(pollID))[:10]
			status = str(self.getStatus(pollID)) 
			sumVotes = str(self.getSumVotes(pollID))
			text = f"```md\n{' '*(3-len(str(pollID)))}{pollID} {name}{' '*(72-len(name))}      Date: {datum}     Status: {status}{' '*(9-len(status))}     Votes:{' '*(5-len(sumVotes))}{sumVotes}\n```\n"
			return text
		return ""

	#Creates the generall poll to be the output.
	def pollString(self, pollID):
		return self.pollStringSortBy(pollID, 2)	

	def pollStringSortBy(self, pollID, sortBy):
		message = self.pollHeader(pollID)
		#Check if pollID exists.
		if message:
			for option in self.sortOptionsBy(pollID, sortBy)[::-1]:
				optionName = str(option[0])
				optionVotes = str(option[1])
				optionNumber = str(option[2])
				message += f"```md\n     {optionNumber}. {optionName}{' '*(112-len(optionName))}     Votes: {' '*(4-len(optionVotes))}{optionVotes}\n```\n"
		return message