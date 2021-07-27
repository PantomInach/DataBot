import json
import os
import time

class Jsonhandel(object):
	"""docstring for Jsonhandel"""
	def __init__(self):
		super(Jsonhandel, self).__init__()
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.config = json.load(open(self.binpath+"config.json"))
		self.data = json.load(open(self.binpath+"data.json"))
		#self.test()

	#Config handel

	#Get Values from config file
	def getFromConfig(self, toget):
		return self.config[str(toget)]

	#Gives back the privilege level
	#Level 0:	User
	#Level 1:	Mod
	#Level 2:	Owner
	def getPrivilegeLevel(self, userID):
		if str(userID) in [x for x in self.config["privilege"]]:
			return self.config["privilege"][str(userID)]
		return 0

	def getInPrivilege(self):
		return [x for x in self.config["privilege"]]

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

	def saveConfig(self):
		with open(self.binpath+"config.json",'w') as f:
			json.dump(self.config, f, indent = 6)
		self.config = json.load(open(self.binpath+"config.json"))
		print("Config saved in JSON-File.")

	def getRoles(self):
		return self.config["roles"]

	def getRolesXPNeed(self):
		return self.config["rolesXPNeed"]

	#Data handel

	def getCooldown(self, userID):
		if self.isInData(userID):
			return self.data[str(userID)]["Cooldown"]

	def writeCooldown(self, userID, time):
		if self.isInData(userID):
			self.data[str(userID)]["Cooldown"] = str(time)

	#Returns true if a userID is in data
	def isInData(self, userID):
		return str(userID) in [x for x in self.data]

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

	#Saves data in json file
	def saveData(self):
		with open(self.binpath+"data.json",'w') as f:
			json.dump(self.data, f, indent = 6)
		self.data = json.load(open(self.binpath+"data.json"))
		print("Data saved in JSON-File.")

	#Adds a minute of voicetime for a userID in data
	def dataIncVoice(self, userID):
		if self.isInData(userID):
			self.data[str(userID)]["Voice"]=str(int(self.data[str(userID)]["Voice"])+1)

	#Adds a XP for Text for a userID in data
	def dataAddText(self, userID, amount):
		self.addNewDataEntry(userID)
		cooldownTime = self.data[str(userID)]["Cooldown"]
		cooldownCon = self.getFromConfig("textCooldown")
		self.data[str(userID)]["TextCount"] = str(int(self.data[str(userID)]["TextCount"])+1)
		t = time.time()
		deltat = t-cooldownTime
		if deltat >= float(cooldownCon):
			self.data[str(userID)]["Text"] = str(int(self.data[str(userID)]["Text"])+amount)
			self.data[str(userID)]["Cooldown"] = t
			print(f"\tUser {userID} gained {amount} TextXP")
		else:
			print(f"\tUser {userID} is on Cooldown. CurrentTime: {deltat}")

	def dataAddTextXP(self, userID, amount):
		self.addNewDataEntry(userID)
		cur = int(self.data[str(userID)]["Text"])
		self.data[str(userID)]["Text"] = cur + amount 		

	def dataAddReaction(self, userID, amount):
		self.addNewDataEntry(str(userID))
		cooldownTime = self.data[str(userID)]["Cooldown"]
		cooldownCon = 10
		t =time.time()
		deltat = t-cooldownTime
		if deltat >= float(cooldownCon):
			self.data[str(userID)]["Text"] = str(int(self.data[str(userID)]["Text"])+amount)
			self.data[str(userID)]["Cooldown"] = t
			print(f"\tUser {userID} gained {amount} TextXP")
		else:
			print(f"\tUser {userID} is on Cooldown. CurrentTime: {deltat}")

	#Increments the voice minuts for all userID in userIDs
	def onlineUserInc(self, userIDs):
		for userID in userIDs:
			self.addNewDataEntry(userID)
			self.dataIncVoice(userID)
		print("Incremented userIDs")
		self.saveData()

	def getUserText(self, userID):
		return self.data[str(userID)]["Text"]

	def getUserVoice(self, userID):
		return self.data[str(userID)]["Voice"]

	def getUserTextCount(self, userID):
		return self.data[str(userID)]["TextCount"]

	def setUserVoice(self, userID, voice):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Voice"] = voice
		self.saveData()

	def setUserText(self, userID, text):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["Text"] = text
		self.saveData()

	def setUserTextCount(self, userID, textCount):
		self.addNewDataEntry(userID)
		self.data[str(userID)]["TextCount"] = textCount
		self.saveData()