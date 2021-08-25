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
		self.config = json.load(open(self.binpath+"config.json"))
		self.data = json.load(open(self.binpath+"data.json"))

	"""
	###########################################
	Part: config
		Functions to maipulate the config json
	"""

	def isInConfig(self, isIn):
		# Tests if isIn is in config
		return isIn in [x for x in self.config]

	def getFromConfig(self, toGet):
		#Get Values from config file
		return self.config[str(toGet)]

	def getPrivilegeLevel(self, userID):
		#Gives back the privilege level of userID
		#Level 0:	User
		#Level 1:	Mod
		#Level 2:	Owner
		if str(userID) in [x for x in self.config["privilege"]]:
			return int(self.config["privilege"][str(userID)])
		return 0

	def getInPrivilege(self):
		return [x for x in self.config["privilege"]]

	def saveConfig(self):
		with open(self.binpath+"config.json",'w') as f:
			json.dump(self.config, f, indent = 6)
		self.config = json.load(open(self.binpath+"config.json"))
		print("Config saved in JSON-File.")

	def getRoles(self):
		# Rolls are given depending on xp
		return self.config["roles"]

	def getRolesXPNeed(self):
		# Rolls are given depending on xp
		return self.config["rolesXPNeed"]

	"""
	##########
	channel Black and White list
	"""

	def isInBlacklist(self, channelID):
		return str(channelID) in [x for x in self.config["serverVoiceBlacklist"]]

	def writeToBalcklist(self, channelID):
		if not self.isInBlacklist(channelID):
			self.config["serverVoiceBlacklist"].append(str(channelID))
			self.saveConfig()
			return 1
		return 0

	def removeFromBalcklist(self, channelID):
		if self.isInBlacklist(channelID):
			self.config["serverVoiceBlacklist"].remove(str(channelID))
			self.saveConfig()
			return 1
		return 0

	def isInWhitelist(self, channelID):
		return str(channelID) in [x for x in self.config["serverTextWhitelist"]]

	def writeToWhitelist(self, channelID):
		if not self.isInWhitelist(channelID):
			self.config["serverTextWhitelist"].append(str(channelID))
			self.saveConfig()
			return 1
		return 0

	def removeFromWhitelist(self, channelID):
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

	#Returns true if a userID is in data
	def isInData(self, userID):
		return str(userID) in [x for x in self.data]

	def sortDataBy(self, sortBy):
		"""
		sortBy:
			0 => Sort by voice + text
			1 => Sort by voice
			2 => Sort by textcount
		"""
		sortMode = [[1,1,0],[0,1,0],[0,0,1]]
		sortedData = sorted(self.data, key = lambda id: sortMode[sortBy][0] * self.getUserText(id) + sortMode[sortBy][1] * self.getUserVoice(id) +sortMode[sortBy][2] * self.getUserTextCount(id))
		return sortedData[::-1]

	def getSortedDataEntrys(self, entryBeginn, entryEnd, sortBy):
		"""
		Sorts Data by given parameter and returns the given entrys.
		entryBeginn included and entryEnd is excluded.
		When entryBeginn would be outside of the data, then a emtpy list is returned
		When entryEnd would point outside of the data, than it points to the end 
		"""
		l = len(self.data)
		if entryBeginn >= l:
			return []
		if entryEnd > l:
			entryEnd = l
		return self.sortDataBy(sortBy)[entryBeginn:entryEnd]

	#Adds a new userID in data
	def addNewDataEntry(self, userID):
		if not self.isInData(userID):
			t = time.time() - 60
			self.data[str(userID)]={'Voice':'0','Text':'0','TextCount':'0','Cooldown':t, 'Level':'0'}
			print(f"\tCreated userID-Entry: {userID, self.data[str(userID)]}")
			self.saveData()

	def removeUserFromData(self, userID):
		if self.isInData(userID):
			del self.data[str(userID)]
			self.saveConfig()
			return 1
		return 0

	#Adds a XP for Text for a userID in data
	def addTextXP(self, userID, amount):
		self.addNewDataEntry(userID)
		cooldownTime = self.data[str(userID)]["Cooldown"]
		cooldownCon = self.getFromConfig("textCooldown")
		self.addUserTextCount(userID)
		t = time.time()
		deltat = t - float(cooldownTime)
		# Check if cooldown is up
		if deltat >= float(cooldownCon):
			self.addUserText(userID, amount)
			self.setCooldown(userID, t = t)
			print(f"\tUser {userID} gained {amount} TextXP")
		else:
			print(f"\tUser {userID} is on Cooldown. CurrentTime: {deltat}")	

	def addReactionXP(self, userID, amount):
		self.addNewDataEntry(str(userID))
		cooldownTime = float(self.data[str(userID)]["Cooldown"])
		cooldownCon = 10
		t =time.time()
		deltat = t-cooldownTime
		# Check if cooldown is up
		if deltat >= float(cooldownCon):
			self.addUserText(userID, amount)
			self.setCooldown(userID, t = t)
			print(f"\tUser {userID} gained {amount} TextXP")
		else:
			print(f"\tUser {userID} is on Cooldown. CurrentTime: {deltat}")

	def updateLevel(self, userID, level):
		if self.isInData(userID):
			self.data[str(userID)]["Level"] = level

	#Increments the voice minuts for all userID in userIDs
	def addAllUserVoice(self, userIDs):
		for userID in userIDs:
			self.addUserVoice(userID)
		self.saveData()

	def getUserText(self, userID):
		return int(self.data[str(userID)]["Text"])

	def getUserVoice(self, userID):
		return int(self.data[str(userID)]["Voice"])

	def getUserHours(self, userID):
		return round(self.getUserVoice(userID)/30.0, 1)

	def getUserTextCount(self, userID):
		return int(self.data[str(userID)]["TextCount"])

	def getCooldown(self, userID):
		if self.isInData(userID):
			return self.data[str(userID)]["Cooldown"]

	def getUserLevel(self, userID):
		if self.isInData(userID):
			return int(self.data[str(userID)]["Level"])

	def getUserIDsInData(self):
		return [id for id in self.data]

	def setCooldown(self, userID, t = time.time()):
		if self.isInData(userID):
			self.data[str(userID)]["Cooldown"] = str(t)

	def setUserVoice(self, userID, voice):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Voice"] = int(voice)
		self.saveData()

	def setUserText(self, userID, text):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Text"] = int(text)
		self.saveData()

	def setUserTextCount(self, userID, textCount):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["TextCount"] = int(textCount)
		self.saveData()

	def addUserVoice(self, userID, voice = 1):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Voice"] = int(self.data[str(userID)]["Voice"]) + int(voice)
		self.saveData()

	def addUserText(self, userID, text):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Text"] = int(self.data[str(userID)]["Text"]) + int(text)
		self.saveData()

	def addUserTextCount(self, userID, count = 1):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["TextCount"] = int(self.data[str(userID)]["TextCount"]) + int(count)
		self.saveData()

	#Saves data in json file
	def saveData(self):
		with open(self.binpath+"data.json",'w') as f:
			json.dump(self.data, f, indent = 6)
		self.data = json.load(open(self.binpath+"data.json"))
		print("Data saved in JSON-File.")