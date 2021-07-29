import json
import os
import datetime

class Poll(object):
	"""
	Handles the background interactions of all polls.
	It saves polls in poll.json.
	Creates and provides poll strings for Discrod. 
	"""
	def __init__(self):
		super(Poll, self).__init__()
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.pollData = json.load(open(self.binpath+"poll.json"))

	def newPoll(self, pollName):
		# Creats a new Poll-Entry with unique ID. Lowest ID possible.
		# Returns the pollID
		pollID=1
		while self.isAPollID(pollID):
			pollID += 1
		self.pollData[str(pollID)]={'name':str(pollName),'datum':str(datetime.datetime.now())[:19],'status':'CLOSED','messageID':['',''],'options':[], 'votes':[]}
		self.savePollData()
		return pollID

	def getAllPolls(self):
		# Returns a list of all PollsIDs
		return [x for x in self.pollData]

	def isAPollID(self, pollID):
		# Tests if a given ID is in pollData
		# Returns True, if is in pollData. False otherwise.
		return str(pollID).isdigit() and str(pollID) in self.getAllPolls()

	# Get the Status of a poll
	# Returns the Status. If pollID is not in pollData return ""
	def getStatus(self, pollID):
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]["status"]
		return ""

	def getOptions(self, pollID):
		# Gets the list of all options in a poll.
		# Returns a list containg [optionName,Votes]. If pollID is not in pollData return []
		if self.isAPollID(pollID):
			return [x for x in self.pollData[str(pollID)]["options"]]
		return []

	def isInOptions(self, pollID, optionName):
		# Checks if a option is in the poll.
		# Returns False if there is no such poll, there are no options or the optionName is not in the poll. Else returns True
		return self.getOptions(pollID) != [] and optionName in [x[0] for x in self.getOptions(pollID)]

	def optionAdd(self, pollID, optionName, votes):
		# Option consists of optionName, optionNumber, votes
		# Adds an option to the poll.
		# If the option is allready in the poll, the poll does not exist or the poll is closed or has more than 5 options, return False. Else adds the option to the poll and returns True.
		if self.getStatus(pollID) == "CLOSED" and not self.isInOptions(pollID, optionName) and not len(self.getOptions(pollID)) >= 7:
			# Get minimum option id
			id = 1
			numbers = [option[2] for option in self.getOptions(pollID)]
			while id in numbers:
				id += 1
			# Creates option
			self.pollData[str(pollID)]["options"].append([str(optionName),votes, id])
			self.savePollData()
			return True
		return False

	def optionRemove(self, pollID, optionName):
		# Removes an option from a poll
		# If the option is not in the poll, the poll does not exist or is closed the returns False. Else delets the option and returns True.
		if self.getStatus(pollID) == "CLOSED":
			options = self.getOptions(pollID)
			if options != []:
				number = 1
				# Search for option
				for x in options:
					if x[0] == optionName:
						# Delet option and votes for option
						self.pollData[str(pollID)]["options"].remove(x)
						self.removeOptionVotes(pollID, optionName)
						number = x[2]
						break
				temp = self.pollData[str(pollID)]["options"]
				# Degress poll option ids.
				for i in range(1, number +1):
					self.pollData[str(pollID)]["options"][i][2] = int(self.pollData[str(pollID)]["options"][i][2]) -1
				self.savePollData()
				return True
		return False

	def pollOpen(self, pollID):
		# Opens the poll
		# If the poll exists and the poll is CLOSED it opens the poll and returns True. Else return False.
		if self.getStatus(pollID) == "CLOSED" and len(self.getOptions(pollID)) > 1:
			self.pollData[str(pollID)]['status'] = "OPEN"
			self.savePollData()
			return True
		return False

	def pollClose(self, pollID):
		# Closes the poll
		# If the poll exists and the poll is Open it closes the poll and returns True. Else return False.
		if self.getStatus(pollID) == "OPEN":
			self.pollData[str(pollID)]['status'] = "CLOSED"
			self.savePollData()
			return True
		return False

	
	def pollPublish(self, pollID):
		# Publishes the poll
		# If the poll exists and the poll is Open it publishes the poll and returns True. Else return False.
		if self.getStatus(pollID) == "OPEN":
			self.pollData[str(pollID)]['status'] = "PUBLISHED"
			self.savePollData()
			return True
		return False						

	def getVotesOfOption(self, pollID, optionName):
		# Get the votes of a option in a poll
		# If poll exists and options is in the poll then returns the votes. Else returns -1
		if self.isAPollID(pollID):
			for x in self.getOptions(pollID):
				if x[0] == optionName:
					return x[1]
		return -1

	def setVotesOfOption(self, pollID, optionName, votes):
		# Sets the votes of an option in a poll to a set amount
		# Returns True, if the operation is succesfull. Otherwise Flase.
		if self.isAPollID(pollID):
			for i in range(len(self.getOptions(pollID))):
				copy = self.pollData[str(pollID)]["options"][i]
				if copy[0] == str(optionName):
					self.pollData[str(pollID)]["options"][i] = [copy[0], votes, copy[2]]
					self.savePollData()
					return True
		return False

	def incVotesOfOption(self, pollID, optionName):
		# Increments the votes of an option in a poll
		# Returns True if the operation was succesfull. Else false.
		votes = self.getVotesOfOption(pollID, optionName)
		re = self.setVotesOfOption(pollID, optionName, votes+1)
		return re

	def decVotesOfOption(self, pollID, optionName):
		# Decrements the votes of an option in a poll
		# Returns True if the operation was succesfull. Else false.
		votes = self.getVotesOfOption(pollID, optionName)
		if votes <= 0:
			return False
		return self.setVotesOfOption(pollID, optionName, votes-1)

	def getOptionByNumber(self, pollID, optionNumber):
		# Gets the optionName from the optionNumber
		# Returns the Name if all is succesful, else return ""
		for option in self.getOptions(pollID):
			if option[2] == optionNumber:
				return option[0]
		return ""

	def getVotes(self, pollID):
		# Get the votes by users
		# Returns the votes by users if the pollID exists. Else return {}.
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]['votes']
		return {}

	def hasUserVote(self, pollID, userID):
		# Test if a user voted in a poll.
		# Returns false if poll does not exist or user has not voted for this poll. Else return True.
		for vote in self.getVotes(pollID):
			if vote[0] == userID:
				return True  
		return False

	def getUserVote(self, pollID ,userID):
		# Gets the vote of a User.
			# If poll does not exist or user has not voted than returns []. Else returns the vote of the user.
		if self.hasUserVote(pollID, userID):
			for vote in self.getVotes(pollID):
				if vote[0] == userID:
					return vote
		return None

	def addUserVote(self, pollID, userID, optionName):
		# Adds the vote of a user. If user has already voted, than removes the previes vote.
		# If the user vote is added succesful than returns True. Else False.
		if self.isAPollID(pollID):
			if self.isInOptions(pollID, optionName):
				# Remove vote so user can change his vote
				if self.hasUserVote(pollID, userID):
					userVote = self.getUserVote(pollID, userID)
					self.decVotesOfOption(pollID, userVote[1])
					self.removeUserVote(pollID, userID)
				# Sets vote again
				self.pollData[str(pollID)]['votes'].append([userID, optionName])
				self.incVotesOfOption(pollID, optionName)
				self.savePollData()
				return True
		return False

	def removeUserVote(self, pollID, userID):
		# removes the vote of a user.
		# returns True only if the user vote was removed from the poll. Else returns False.
		if self.isAPollID(pollID):
			vote = self.getUserVote(pollID, userID)
			if vote != None:
				self.pollData[str(pollID)]['votes'].remove(vote)
				return True
		return False

	def removeOptionVotes(self, pollID, optionName):
		# Removes all votes with the given optionName
		# Returns True if the votes where succefully removed. Else return Flase.
		if self.isAPollID(pollID):
			if self.isInOptions(pollID, optionName):
				for vote in self.getVotes(pollID):
					if vote[1] == optionName:
						self.pollData[str(pollID)]['votes'].remove(vote)
				return True
		return False

	def getSumVotes(self, pollID):
		# Get the sum of all votes and returns them.
		s = 0
		for option in self.getOptions(pollID):
			s += int(option[1])
		return s

	def setMessageID(self, pollID, messageID, channelID):
		# Sets messageID of Poll
		# If operation succesful, return True, else False.
		if self.isAPollID(pollID):
			self.pollData[str(pollID)]["messageID"] = [messageID, channelID]
			self.savePollData()
			return True
		return False
 
	def getName(self, pollID):
		# Gets the poll name
		# Returns the name of the poll, if poll exists. Otherwise returns None.
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]['name']
		return None

	def getMessageID(self, pollID):
		# Returns MessageID of Poll
		# Returns messageID, if poll exists, else -1
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]["messageID"]
		return -1

	def getDate(self, pollID):
		# Gets the date of a poll creation
		# If no poll exists, return 0, else the date of the poll.
		if self.isAPollID(pollID):
			return self.pollData[str(pollID)]["datum"]
		return 0

	def removePoll(self, pollID):
		# Removes a poll.
		# If the poll exists, then removes the poll and returns True. Else return False.
		if self.isAPollID(pollID):
			del self.pollData[str(pollID)]
			self.savePollData()
			return True
		return False

	def savePollData(self):
		# saves pollData to poll.json
		with open(self.binpath+"poll.json",'w') as f:
			json.dump(self.pollData, f ,indent = 6)
		self.pollData = json.load(open(self.binpath+"poll.json"))
 
	def sortOptionsBy(self, pollID, sortBy):
		# Sorts the options of a poll by votes(1) or by optionNumber(2)
		# Returns [] when pollID does not exist. Else returns options sorted by sortBy.
		options = self.getOptions(pollID)
		if not (sortBy == 1 or sortBy == 2) or len(options) == 0:
			return []
		# Sorting
		sortedOptions = sorted(options, key = lambda option: int(option[sortBy]))
		if sortBy == 1:
			sortedOptions = sortedOptions[::-1]
		return sortedOptions

	def resetVotes(self, pollID):
		# Resets the votes of a poll.
		# Returns true if the poll exists. Otherwise return False.
		if self.isAPollID(pollID):
			# Undo votes in options
			for option in self.getOptions():
				self.setVotesOfOption(pollID, option[0], 0)
			# Delet votes
			self.pollData[str(pollID)]["votes"] = []	
			return True
		return False

	def pollHeader(self, pollID):
		# Generates the poll header.
		# Returns the poll header a String. If pollID does not exist returns an empty String
		if self.isAPollID(pollID):
			name = str(self.getName(pollID))
			datum = str(self.getDate(pollID))[:10]
			status = str(self.getStatus(pollID)) 
			sumVotes = str(self.getSumVotes(pollID))
			text = f"```md\n{' '*(3-len(str(pollID)))}{pollID} {name}{' '*(72-len(name))}      Date: {datum}     Status: {status}{' '*(9-len(status))}     Votes:{' '*(5-len(sumVotes))}{sumVotes}\n```\n"
			return text
		return ""

	def pollString(self, pollID):
		# Creates the generall poll to be the output.
		return self.pollStringSortBy(pollID, 2)	

	def pollStringSortBy(self, pollID, sortBy):
		message = self.pollHeader(pollID)
		# Check if pollID exists.
		if message:
			for option in self.sortOptionsBy(pollID, sortBy)[::-1]:
				optionName = str(option[0])
				optionVotes = str(option[1])
				optionNumber = str(option[2])
				message += f"```md\n     {optionNumber}. {optionName}{' '*(112-len(optionName))}     Votes: {' '*(4-len(optionVotes))}{optionVotes}\n```\n"
		return message