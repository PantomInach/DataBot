import json
import os
import time

class Jsonhandel(object):
	"""
	Handles maipulation and reading from data.json and config.json
	"""
	def __init__(self):
		super(Jsonhandel, self).__init__()
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		# Reads in data.json and config.json
		self.config = json.load(open(self.binpath+"config.json"))
		self.data = json.load(open(self.binpath+"data.json"))

	"""
	###########################################
	Part: config
		Functions to maipulate the config json
	"""

	def isInConfig(self, isIn):
		"""
		param isIn:		String or integer which may be in config.json.

		Tests if isIn is in config
		"""
		return isIn in [x for x in self.config]

	def getFromConfig(self, toGet):
		"""
		param toget:	Reads String or integer from config.json

		Get Values from config file
		"""
		return self.config[str(toGet)]

	def getPrivilegeLevel(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gives back the privilege level of userID
			Level 0:	User
			Level 1:	Mod
			Level 2:	Owner
		"""
		if str(userID) in [x for x in self.config["privilege"]]:
			return int(self.config["privilege"][str(userID)])
		return 0

	def getInPrivilege(self):
		"""
		Get userIDs with there privilage level in config.json.
		"""
		return [x for x in self.config["privilege"]]

	def saveConfig(self):
		"""
		Saves config.json and reads it in again.
		"""
		with open(self.binpath+"config.json",'w') as f:
			json.dump(self.config, f, indent = 6)
		self.config = json.load(open(self.binpath+"config.json"))
		print("Config saved in JSON-File.")

	def getRoles(self):
		"""
		Get from config.json the rolls which the bot will give depending on the users XP.
		"""
		return self.config["roles"]

	def getRolesXPNeed(self):
		"""
		Gets which level is needed for each role.
		"""
		return self.config["rolesXPNeed"]

	"""
	##########
	channel Black and White list
	"""

	def isInBlacklist(self, channelID):
		"""
		param channelID:	The id of the channel the message of messageID is in.

		Test if he channelID is in the balcklist of the config.json.
		"""
		return str(channelID) in [x for x in self.config["serverVoiceBlacklist"]]

	def writeToBalcklist(self, channelID):
		"""
		param channelID:	The id of the channel the message of messageID is in.

		Stores the channelID in config.json in the blacklist list.
		"""
		if not self.isInBlacklist(channelID):
			self.config["serverVoiceBlacklist"].append(str(channelID))
			self.saveConfig()
			return 1
		return 0

	def removeFromBalcklist(self, channelID):
		"""
		param channelID:	The id of the channel the message of messageID is in.

		Removes the channelID from the blacklist in config.json
		"""
		if self.isInBlacklist(channelID):
			self.config["serverVoiceBlacklist"].remove(str(channelID))
			self.saveConfig()
			return 1
		return 0

	def isInWhitelist(self, channelID):
		"""
		param channelID:	The id of the channel the message of messageID is in.

		Test if channelID is in whitelist in config.json
		"""
		return str(channelID) in [x for x in self.config["serverTextWhitelist"]]

	def writeToWhitelist(self, channelID):
		"""
		param channelID:	The id of the channel the message of messageID is in.

		Stores the channelID in config.json in the whitelist list.
		"""
		if not self.isInWhitelist(channelID):
			self.config["serverTextWhitelist"].append(str(channelID))
			self.saveConfig()
			return 1
		return 0

	def removeFromWhitelist(self, channelID):
		"""
		param channelID:	The id of the channel the message of messageID is in.

		Removes the channelID from the whitelist in config.json
		"""
		if self.isInWhitelist(channelID):
			self.config["serverTextWhitelist"].remove(str(channelID))
			self.saveConfig()
			return 1
		return 0

	"""
	###########################################
	Part: Data
		Functions to maipulate the data json
	"""

	def isInData(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Tests if the user has an entry in data.json.
		"""
		return str(userID) in [x for x in self.data]

	def sortDataBy(self, sortBy):
		"""
		param sortBy:
			0 => Sort by voice + text
			1 => Sort by voice
			2 => Sort by textcount

		Sorts data.json depending in sortBy 
		"""
		sortMode = [[1,1,0],[0,1,0],[0,0,1]]
		sortedData = sorted(self.data, key = lambda id: sortMode[sortBy][0] * self.getUserText(id) + sortMode[sortBy][1] * self.getUserVoice(id) +sortMode[sortBy][2] * self.getUserTextCount(id))
		return sortedData[::-1]

	def getSortedDataEntrys(self, entryBeginn, entryEnd, sortBy):
		"""
		param entrBeginn:	Beginn of user entry which will be returned. When into in data range, than empty list will be returned.
		param entryEnd:		Defines the ende of the returned user datas. Is not included. When is larger or smaller than data, than all datapoints beginning wih entryBeginn will be returned.
		param sortBy:
			0 => Sort by voice + text
			1 => Sort by voice
			2 => Sort by textcount	

		Sorts Data by given parameter and returns the given entrys.
		"""
		l = len(self.data)
		if entryBeginn >= l:
			return []
		if entryEnd > l:
			entryEnd = l
		return self.sortDataBy(sortBy)[entryBeginn:entryEnd]

	def addNewDataEntry(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Adds a new data entry with the userID.

		Format of new data entry:
			{"Voice": "0", "Text": "0", "TextCount": "0", "Cooldown": float, "Level": "0"}
		"""
		if not self.isInData(userID):
			t = time.time() - 60
			self.data[str(userID)]={'Voice':'0','Text':'0','TextCount':'0','Cooldown':t, 'Level':'0'}
			print(f"\tCreated userID-Entry: {userID, self.data[str(userID)]}")
			self.saveData()

	def removeUserFromData(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Removes user entry with userID from data.json if it exists.
		"""
		if self.isInData(userID):
			del self.data[str(userID)]
			self.saveConfig()
			return 1
		return 0

	def addTextMindCooldown(self, userID, amount, cooldown):
		"""
		param userID:	Is the userID from discord user as a String or int
		param amount:	How much XP will be added. As an int. Also negative numbers are possible to remove XP.
		param cooldown:	How long a user needs to wait before being able to get XP.

		Adds XP for user in data.json by the amount in amount. Only add if user is not on cooldown.
		"""
		self.addNewDataEntry(userID)
		cooldownTime = self.data[str(userID)]["Cooldown"]
		cooldownCon = cooldown
		self.addUserTextCount(userID)
		t = time.time()
		deltat = t - float(cooldownTime)
		# Check if cooldown is up
		if deltat >= float(cooldownCon):
			# Add XP
			self.addUserText(userID, amount)
			self.setCooldown(userID, t = t)
			print(f"\tUser {userID} gained {amount} TextXP")
		else:
			print(f"\tUser {userID} is on Cooldown. CurrentTime: {deltat}")

	def addTextXP(self, userID, amount):
		"""
		param userID:	Is the userID from discord user as a String or int
		param amount:	How much XP will be added. As an int. Also negative numbers are possible to remove XP.

		Adds XP for user in data.json by the amount in amount. Only add if user is not on cooldown of Texts.
		"""
		cooldownCon = self.getFromConfig("textCooldown")
		self.addTextMindCooldown(userID, amount, cooldownCon)

	def addReactionXP(self, userID, amount):
		"""
		param userID:	Is the userID from discord user as a String or int
		param amount:	How much XP will be added. As an int. Also negative numbers are possible to remove XP.

		Adds XP for user in data.json by the amount in amount. Only add if user is not on cooldown for Reactions.
		"""
		self.addTextMindCooldown(userID, amount, 10)

	def updateLevel(self, userID, level):
		"""
		param userID:	Is the userID from discord user as a String or int
		param level:	Integer which level the user should get.

		Sets user level to level if he is in data.json.
		"""
		if self.isInData(userID):
			self.data[str(userID)]["Level"] = level

	def addAllUserVoice(self, userIDs):
		"""
		param userIDs:	Is a list of userIDs from discord user as a String or int

		Increments the hours of all users in userIDs by 1.
		If user not in data.json, than a new user entry will be added.
		"""
		for userID in userIDs:
			self.addUserVoice(userID)
		self.saveData()

	def getUserText(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gets the Text from data.json for user with userID.
		"""
		return int(self.data[str(userID)]["Text"])

	def getUserVoice(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gets the Voice from data.json for user with userID.
		"""
		return int(self.data[str(userID)]["Voice"])

	def getUserHours(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gets the Hours from data.json for user with userID.
		"""
		return round(self.getUserVoice(userID)/30.0, 1)

	def getUserTextCount(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gets the TextCount from data.json for user with userID.
		"""
		return int(self.data[str(userID)]["TextCount"])

	def getCooldown(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gets the Cooldown from data.json for user with userID.
		"""
		if self.isInData(userID):
			return self.data[str(userID)]["Cooldown"]

	def getUserLevel(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Gets the level from data.json for user with userID.
		"""
		if self.isInData(userID):
			return int(self.data[str(userID)]["Level"])

	def getUserIDsInData(self):
		"""
		Gets the userIDs in data.json.
		"""
		return [id for id in self.data]

	def setCooldown(self, userID, t = time.time()):
		"""
		param userID:	Is the userID from discord user as a String or int
		param t:	Time to set the cooldown to. Default current time.

		Sets the cooldown of a user in data.json.
		"""
		if self.isInData(userID):
			self.data[str(userID)]["Cooldown"] = str(t)

	def setUserVoice(self, userID, voice):
		"""
		param userID:	Is the userID from discord user as a String or int
		param voice:	Integer to which the Voice off a user is set to.

		Sets a users Voice to voice in data.json.
		"""
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Voice"] = int(voice)
		self.saveData()

	def setUserText(self, userID, text):
		"""
		param userID:	Is the userID from discord user as a String or int
		param text:		Integer to which the Text is set to.

		Sets the users Text to text in data.json.
		"""
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Text"] = int(text)
		self.saveData()

	def setUserTextCount(self, userID, textCount):
		"""
		param userID:	Is the userID from discord user as a String or int
		param textCount:	Integer to which the TextCount is set to.

		Sets the users TextCount to textCount in data.json.
		"""
		self.addNewDataEntry(userID)
		self.data[str(userID)]["TextCount"] = int(textCount)
		self.saveData()

	def addUserVoice(self, userID, voice = 1):
		"""
		param userID:	Is the userID from discord user as a String or int
		param voice:	Integer to which is added to Voice. Default is 1.

		Adds voice to the users Voice in data.json.
		"""
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Voice"] = int(self.data[str(userID)]["Voice"]) + int(voice)
		self.saveData()

	def addUserText(self, userID, text):
		"""
		param userID:	Is the userID from discord user as a String or int
		param 

		Adds text to the users Text in data.json.
		"""
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Text"] = int(self.data[str(userID)]["Text"]) + int(text)
		self.saveData()

	def addUserTextCount(self, userID, count = 1):
		"""
		param userID:	Is the userID from discord user as a String or int
		param voice:	Integer to which is added to Voice. Default is 1.

		Adds count to the users TextCount in data.json.
		"""
		self.addNewDataEntry(userID)
		self.data[str(userID)]["TextCount"] = int(self.data[str(userID)]["TextCount"]) + int(count)
		self.saveData()

	def saveData(self):
		"""
		Saves current data.json to disc and reads it again.
		"""
		with open(self.binpath+"data.json",'w') as f:
			json.dump(self.data, f, indent = 6)
		self.data = json.load(open(self.binpath+"data.json"))