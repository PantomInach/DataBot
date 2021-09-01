import json
import os
import asyncio
import time as t

class Textban(object):
	"""
	Backend for textban functionality.
	Handels interactions between textban.json file and bot textban commands.
	"""

	def __init__(self):
		"""
		Creates textban object
		"""
		super(Textban, self).__init__()
		# Opens textban.json
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.ban = json.load(open(self.binpath+"textban.json"))

	def hasTextBan(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Checks if a user has an entry in textban.json.	
		"""
		return str(userID) in self.ban

	async def addTextBan(self, userID, time):
		"""
		param userID:	Is the userID from discord user as a String or int
		param time:		Who long the user should be banned. Format: String or int.

		Adds a textban for a user and delets it after the amount of time.
		Textbans are carryed out in main.on_message() by deleting send messages.
		"""
		if str(time).isdigit():
			#if self.hasTextBan(userID) and self.ban[str(userID)][1]:
			self.ban[str(userID)] = [str(time), t.time()]
			self.saveBan()
			print("Added Textban")
			# Sleeps thread till the time is up 
			await asyncio.sleep(int(time))
			# Remove textban
			print("Remove textban")
			if self.hasTextBan(userID):
				self.removeTextBan(userID)
				self.saveBan()
			return True
		return False

	def getTextBanTime(self, userID):
		pass

	def removeTextBan(self, userID):
		"""
		param userID:	Is the userID from discord user as a String or int

		Removes a user from textban.json, so the user is no more textbanned.
		"""
		if self.hasTextBan(userID):
			del self.ban[str(userID)]
			self.saveBan()
			return True
		return False

	def removeAllTextBan(self):
		"""
		Removes all users from textban.json.
		"""
		bans = self.ban
		for userID in bans:
			self.removeTextBan(str(userID))
			self.saveBan()

	def clearInvalidTextban(self):
		"""
		Clear all textbans ffrom textban.json, which are run out but did not get cleared.
		"""
		for userID in self.ban:
			if t.time() - int(self.ban[userID][1]) >= int(self.ban[userID][0]):
				self.removeTextBan(userID)
				self.saveBan()

	def saveBan(self):
		"""
		Saves current textban to file and rereads it.
		"""
		with open(self.binpath+"textban.json",'w') as f:
			json.dump(self.ban, f ,indent = 6)
		self.ban = json.load(open(self.binpath+"textban.json"))