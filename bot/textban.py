import json
import os
import asyncio
import time as ttime

class Textban(object):
	"""docstring for Textban"""
	def __init__(self):
		super(Textban, self).__init__()
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.ban = json.load(open(self.binpath+"textban.json"))

	def hasTextBan(self, userID):
		if str(userID) in self.ban:
			return True
		return False

	async def addTextBan(self, userID, time):
		if str(time).isdigit():
			#if self.hasTextBan(userID) and self.ban[str(userID)][1]:
			self.ban[str(userID)] = [str(time), ttime.time()]
			self.saveBan()
			await asyncio.sleep(int(time))
			if self.hasTextBan(userID):
				self.removeTextBan(userID)
				self.saveBan()
			return True
		return False

	def getTextBanTime(self, userID):
		pass

	def removeTextBan(self, userID):
		if self.hasTextBan(userID):
			del self.ban[str(userID)]
			self.saveBan()
			return True
		return False

	def removeAllTextBan(self):
		bans = self.ban
		for userID in bans:
			self.removeTextBan(str(userID))
			self.saveBan()

	def clearInvalidTextban(self):
		for userID in self.ban:
			if ttime.time() - int(self.ban[userID][1]) >= int(self.ban[userID][0]):
				self.removeTextBan()
				self.saveBan()

	def saveBan(self):
		with open(self.binpath+"textban.json",'w') as f:
			json.dump(self.ban, f ,indent = 6)
		self.ban = json.load(open(self.binpath+"textban.json"))