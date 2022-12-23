import json
import os
import datetime


class Poll(object):
    """
    Handles the background interactions of all polls.
    It saves polls in poll.json.
    Creates and provides poll strings for Discord.

    Poll structure:
        "ID": {
            "name": String,
            "datum": "JJJJ-MM-DD HH:MM:SS",
            "Status": "CLOSE" or "OPEN" or "PUBLISHED",
            "messageID": [
                "Channel of message",
                "Message ID"
            ],
            "options": [
                 [
                    "option name",
                    votes,
                    optionID
                ]
            ],
            "votes": [
                [
                    userID,
                    "Member Nick, User Name"
                ]
            ]
        }
    """

    def __init__(self):
        """
        Creates Poll object
        """
        super(Poll, self).__init__()
        # Opens poll.json file
        self.datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
        self.pollData = json.load(open(self.datapath + "poll.json"))

    def newPoll(self, pollName):
        """
        pollName:	Name for a new poll.

        Creates a new poll-entry with unique ID. Lowest ID possible.


        """
        pollID = 1
        # Get lowest poll ID
        while self.isAPollID(pollID):
            pollID += 1
        self.pollData[str(pollID)] = {
            "name": str(pollName),
            "datum": str(datetime.datetime.now())[:19],
            "status": "CLOSED",
            "messageID": ["", ""],
            "options": [],
            "votes": [],
        }
        self.savePollData()
        return pollID

    def getAllPolls(self):
        """
        Returns a list of all poll IDs
        """
        return [x for x in self.pollData]

    def isAPollID(self, pollID):
        """
        pollID:	The ID of the poll

        Tests if a given ID is in pollData
        """
        return str(pollID).isdigit() and str(pollID) in self.getAllPolls()

    def getStatus(self, pollID):
        """
        pollID:	The ID of the poll

        Gets the status of a poll: OPEN, CLOSED, PUBLISHED
        """
        if self.isAPollID(pollID):
            return self.pollData[str(pollID)]["status"]
        return ""

    def getOptions(self, pollID):
        """
        pollID:	The ID of the poll

        Gets the list of all options in a poll.
        """
        if self.isAPollID(pollID):
            return [x for x in self.pollData[str(pollID)]["options"]]
        return []

    def isInOptions(self, pollID, optionName):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option

        Checks if a option is in the poll.
        """
        return self.getOptions(pollID) != [] and optionName in [
            x[0] for x in self.getOptions(pollID)
        ]

    def optionAdd(self, pollID, optionName, votes):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option
        votes:	The amount of votes for the new option

        Adds an option to the poll.
        """
        if (
            self.getStatus(pollID) == "CLOSED"
            and not self.isInOptions(pollID, optionName)
            and not len(self.getOptions(pollID)) >= 7
        ):
            # Get minimum option ID
            id = 1
            numbers = [option[2] for option in self.getOptions(pollID)]
            while id in numbers:
                id += 1
            # Creates option
            self.pollData[str(pollID)]["options"].append([str(optionName), votes, id])
            self.savePollData()
            return True
        return False

    def optionRemove(self, pollID, optionName):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option

        Removes an option from a poll
        """
        if self.getStatus(pollID) == "CLOSED":
            options = self.getOptions(pollID)
            if options != []:
                optionNumber = 1
                # Search for option
                for x in options:
                    if x[0] == optionName:
                        # Delete option and votes for option
                        self.pollData[str(pollID)]["options"].remove(x)
                        self.removeOptionVotes(pollID, optionName)
                        optionNumber = x[2]
                        break
                temp = self.pollData[str(pollID)]["options"]
                # Reduce poll option IDs by 1 if ID is above removed IDs.
                # len(options)-1 because one option was removed
                for i in range(optionNumber - 1, len(options) - 1):
                    self.pollData[str(pollID)]["options"][i][2] = (
                        int(self.pollData[str(pollID)]["options"][i][2]) - 1
                    )
                self.savePollData()
                return True
        return False

    def pollOpen(self, pollID):
        """
        pollID:	The ID of the poll

        Opens the poll if possible.
        """
        if self.getStatus(pollID) == "CLOSED" and len(self.getOptions(pollID)) > 1:
            # Set status
            self.pollData[str(pollID)]["status"] = "OPEN"
            self.savePollData()
            return True
        return False

    def pollClose(self, pollID):
        """
        pollID:	The ID of the poll

        Closes the poll if possilbe
        """
        if self.getStatus(pollID) == "OPEN":
            # Sets status
            self.pollData[str(pollID)]["status"] = "CLOSED"
            self.savePollData()
            return True
        return False

    def pollPublish(self, pollID):
        """
        pollID:	The ID of the poll

        Publishes the poll
        """
        if self.getStatus(pollID) == "OPEN":
            # Sets status
            self.pollData[str(pollID)]["status"] = "PUBLISHED"
            self.savePollData()
            return True
        return False

    def getVotesOfOption(self, pollID, optionName):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option

        Get the votes of a option in a poll
        """
        if self.isAPollID(pollID):
            for x in self.getOptions(pollID):
                if x[0] == optionName:
                    return x[1]
        return -1

    def setVotesOfOption(self, pollID, optionName, votes):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option
        votes:	The amount of votes for theoption

        Sets the votes of an option in a poll to a set amount
        """
        if self.isAPollID(pollID):
            for i in range(len(self.getOptions(pollID))):
                copy = self.pollData[str(pollID)]["options"][i]
                if copy[0] == str(optionName):
                    self.pollData[str(pollID)]["options"][i] = [
                        copy[0], votes, copy[2]]
                    self.savePollData()
                    return True
        return False

    def incVotesOfOption(self, pollID, optionName):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option

        Increments the votes of an option in a poll
        """
        votes = self.getVotesOfOption(pollID, optionName)
        re = self.setVotesOfOption(pollID, optionName, votes + 1)
        return re

    def decVotesOfOption(self, pollID, optionName):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option

        Decrements the votes of an option in a poll
        """
        votes = self.getVotesOfOption(pollID, optionName)
        if votes <= 0:
            return False
        return self.setVotesOfOption(pollID, optionName, votes - 1)

    def getOptionByNumber(self, pollID, optionNumber):
        """
        pollID:	The ID of the poll
        optionNumber:	The number of targeted option

        Gets the optionName from the optionNumber
        """
        for option in self.getOptions(pollID):
            if option[2] == optionNumber:
                return option[0]
        return ""

    def getVotes(self, pollID):
        """
        pollID:	The ID of the poll

        Get the votes by users
        """
        if self.isAPollID(pollID):
            return self.pollData[str(pollID)]["votes"]
        return {}

    def hasUserVote(self, pollID, userID):
        """
        pollID:	The ID of the poll
        userID:	Is the user ID from discord user as a string or int

        Test if a user voted in a poll.
        """
        for vote in self.getVotes(pollID):
            if vote[0] == userID:
                return True
        return False

    def getUserVote(self, pollID, userID):
        """
        pollID:	The ID of the poll
        userID:	Is the user ID from discord user as a string or int

        Gets the vote of a User.
        """
        if self.hasUserVote(pollID, userID):
            for vote in self.getVotes(pollID):
                if vote[0] == userID:
                    return vote
        return None

    def addUserVote(self, pollID, userID, optionName):
        """
        pollID:	The ID of the poll
        userID:	Is the user ID from discord user as a string or int
        optionName:	The name of targeted option

        Adds the vote of a user. If user has already voted, than removes the previes vote.
        """
        if self.isAPollID(pollID):
            if self.isInOptions(pollID, optionName):
                # Remove vote so user can change his vote
                if self.hasUserVote(pollID, userID):
                    userVote = self.getUserVote(pollID, userID)
                    self.decVotesOfOption(pollID, userVote[1])
                    self.removeUserVote(pollID, userID)
                # Sets vote again
                self.pollData[str(pollID)]["votes"].append([userID, optionName])
                self.incVotesOfOption(pollID, optionName)
                self.savePollData()
                return True
        return False

    def removeUserVote(self, pollID, userID):
        """
        pollID:	The ID of the poll
        userID:	Is the user ID from discord user as a string or int

        Removes the vote of a user from poll.
        """
        if self.isAPollID(pollID):
            vote = self.getUserVote(pollID, userID)
            if vote != None:
                self.pollData[str(pollID)]["votes"].remove(vote)
                return True
        return False

    def removeOptionVotes(self, pollID, optionName):
        """
        pollID:	The ID of the poll
        optionName:	The name of targeted option

        Removes all votes with the given optionName.
        """
        if self.isAPollID(pollID):
            if self.isInOptions(pollID, optionName):
                for vote in self.getVotes(pollID):
                    if vote[1] == optionName:
                        self.pollData[str(pollID)]["votes"].remove(vote)
                return True
        return False

    def getSumVotes(self, pollID):
        """
        pollID:	The ID of the poll

        Get the sum of all votes and returns them.
        """
        s = 0
        for option in self.getOptions(pollID):
            s += int(option[1])
        return s

    def setMessageID(self, pollID, messageID, channelID):
        """
        pollID:	The ID of the poll
        messageID:	The ID of a message in discord.
        channelID:	The ID of the channel the message of messageID is in.

        Sets messageID of Poll
        """
        if self.isAPollID(pollID):
            self.pollData[str(pollID)]["messageID"] = [messageID, channelID]
            self.savePollData()
            return True
        return False

    def getName(self, pollID):
        """
        pollID:	The ID of the poll

        Gets the poll name
        """
        if self.isAPollID(pollID):
            return self.pollData[str(pollID)]["name"]
        return None

    def getMessageID(self, pollID):
        """
        pollID:	The ID of the poll

        Returns MessageID of Poll.
        """
        if self.isAPollID(pollID):
            return self.pollData[str(pollID)]["messageID"]
        return None

    def getDate(self, pollID):
        """
        pollID:	The ID of the poll

        Gets the date of a poll creation
        """
        if self.isAPollID(pollID):
            return self.pollData[str(pollID)]["datum"]
        return 0

    def removePoll(self, pollID):
        """
        pollID:	The ID of the poll

        Removes a poll.
        """
        if self.isAPollID(pollID):
            del self.pollData[str(pollID)]
            self.savePollData()
            return True
        return False

    def savePollData(self):
        """
        Saves pollData to poll.json
        """
        with open(self.datapath + "poll.json", "w") as f:
            json.dump(self.pollData, f, indent=6)
        self.pollData = json.load(open(self.datapath + "poll.json"))

    def sortOptionsBy(self, pollID, sortBy):
        """
        pollID:	The ID of the poll
        sortBy:	How to sort the output
                                        sortBy = 1 => Sort options by votes
                                        sortBy = 2 => Sort by optionNuber

        Sorts the options of a poll by votes(1) or by optionNumber(2)
        """
        options = self.getOptions(pollID)
        if not (sortBy == 1 or sortBy == 2) or len(options) == 0:
            return []
        # Sorting
        sortedOptions = sorted(options, key=lambda option: int(option[sortBy]))
        if sortBy == 1:
            sortedOptions = sortedOptions[::-1]
        return sortedOptions

    def resetVotes(self, pollID):
        """
        pollID:	The ID of the poll

        Resets the votes of a poll.
        """
        if self.isAPollID(pollID):
            # Undo votes in options
            for option in self.getOptions():
                self.setVotesOfOption(pollID, option[0], 0)
            # Delet votes
            self.pollData[str(pollID)]["votes"] = []
            return True
        return False

    def pollHeader(self, pollID):
        """
        pollID:	The ID of the poll

        Generates the poll header.
        """
        if self.isAPollID(pollID):
            name = str(self.getName(pollID))
            datum = str(self.getDate(pollID))[:10]
            status = str(self.getStatus(pollID))
            sumVotes = str(self.getSumVotes(pollID))
            text = f"```md\n{' '*(3-len(str(pollID)))}{pollID} {name}{' '*(72-len(name))}      Date: {datum}     Status: {status}{' '*(9-len(status))}     Votes:{' '*(5-len(sumVotes))}{sumVotes}\n```\n"
            return text
        return ""

    def pollString(self, pollID):
        """
        pollID:	The ID of the poll

        Creates the generall poll to be the output.
        """
        return self.pollStringSortBy(pollID, 2)

    def pollStringSortBy(self, pollID, sortBy):
        """
        pollID:	The ID of the poll
        sortBy:	How to sort the output
                                        sortBy = 1 => Sort options by votes
                                        sortBy = 2 => Sort by optionNuber

        Generates the poll String to post in Discord with sorting the options by sortBy.
        """
        message = self.pollHeader(pollID)
        # Check if pollID exists.
        if message:
            for option in self.sortOptionsBy(pollID, sortBy):
                optionName = str(option[0])
                optionVotes = str(option[1])
                optionNumber = str(option[2])
                message += f"```md\n     {optionNumber}. {optionName}{' '*(112-len(optionName))}     Votes: {' '*(4-len(optionVotes))}{optionVotes}\n```\n"
        return message
