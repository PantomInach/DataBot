import random
from .jsonhandel import Jsonhandel

class Xpfunk(object):
	"""
	Class to handle xp calculations
	"""
	def __init__(self, jh):
		super(Xpfunk, self).__init__()
		self.jh = jh
		
	def textXP(self, message):
		if len(message)>=150:
			return random.randint(20,40)
		return random.randint(15,25)

	def randomRange(self, start, end):
		return random.randint(start,end)

	def giveXP(self, voice, text):
		return voice + text

	def levelRoleList(self, userID):
		roles = self.jh.getRoles()
		rolesXPNeed = self.jh.getRolesXPNeed()
		roleList = []
		userLevel = int(self.jh.getUserLevel(userID))
		for i in range(0,len(roles)):
			if userLevel >= rolesXPNeed(i):
				roleList.append(roles[i])
			else:
				break
		return roleList

	def levelFunk(self, voice, text):
		level = 0
		xp = int(voice)+int(text)
		levelLim = 100
		while xp > levelLim:
			level += 1
			levelLim += 100
			for x in [(55+y*10) for y in range(level)]:
				levelLim += x
		return int(level)

	def xpNeed(self, voice, text):
		level = 0
		xp = int(voice)+int(text)
		levelLim = 100
		while xp > levelLim:
			level += 1
			levelLim += 100
			for x in [(55+y*10) for y in range(level)]:
				levelLim += x
		return levelLim