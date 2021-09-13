import asyncio
import time
import os
import json
import traceback

class Sub(object):
	"""
	Manages subroutines of bot.
	Bot subroutines are functions, which are called after some time has passed.
	These features are not event driven like all other.

	Also handels all changes which will be made to sub.json.

	Subroutines:
		Removes role
		Give role once
		(Not yet moved from commandowner.startlog) Log users in channel and gives xp

	subroutine.json stores critical information, which should be retained at a restart.

	sub.json foramting:
			"Name of subRoutine":
				Information for subroutine

			"removeRole":{
				"ID of role to remove": [
					offset as float,
					intervall as int,
				]
			},

			"giveRoleOnce":{
				"some number": [
					offset as float,
					intervall as float,
					userID to whom the role is given as int,
					ID of role to give as int
				]
			}

	Example for remove role:
		Offset is 2021.01.04 CEST == 1609711200.0. Can be determaint through 'time.mktime(time.strptime("2021 Jan 4 CEST","%Y %b %d %Z"))'.
		Intervall is 1 Week == 604800
		So every Monday the role will be removed.
	"""

	def __init__(self, helpf):
		super(Sub, self).__init__()
		self.helpf = helpf
		self.loop = None
		# Indicates if subroutine can be stopped savely.
		self.canStop = True
		# Reads sub.json
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.subjson = json.load(open(binpath+"sub.json"))		

	def startSubRoutine(self):
		"""
		Creates a new asyncio event loop in which the subroutine runs.
		If the subroutine is already running nothing happens.
		"""
		if self.loop:
			# Subroutine is running
			return

		self.loop = asyncio.new_event_loop()
		self.loop.run_until_complete(subRoutine)

	async def stopSubRoutine(self):
		if not self.loop:
			# Subroutine is not running
			return
		while not self.canStop:
			print("[Subroutine] Waiting for subRoutine to stop...")
			await asyncio.sleep(0.1)
		print("[Subroutine] Stopping subRoutine")
		self.loop.close()

	async def subRoutine(self):
		"""
		Runs the subroutine. After a determant waiting time the the features will be called.

		Features implemented (will be carried out in this order):
			Remove role
			Give role once
		"""
		"""
		waitTime says how long the subroutine will sleep between cycles. 
		Also indicates buffer of activities.
		When a time is mentiont in this function, than a time window is ment from 0 to waitTime.
		"""
		waitTime = 120

		guild = self.helpf.getGuild()
		while True:
			currentTime = time.time()

			"""
			Remove role subroutine:
				Continuously removes the role in a given intervall starting on the offset.
			"""
			await self.removeRoleSubroutineFunction(currentTime)

			"""
			Give role once:
				Gives a member a role when the time window is hit.
				The time window is defined with an offset and intervall.
				If the intervall is hit beginning on the offset, than only once the role is given. 
			"""
			await giveRoleOnceSubroutineFunction(currentTime)

			# Pauses the subroutine.
			self.canStop = True
			await asyncio.sleep(waitTime)
			self.canStop = False

	async def removeRoleSubroutineFunction(self, currentTime):
		"""
		param currentTime:	Float time on what the timing will be compared on.

		Removes the role for all users in the guilde.
		First scanns sub.json for 'removeRole' events. 
		Than determants if they should be carried out and carrys them out.
		"""
		for toRemove in self.subjson["removeRole"]:
			offset, intervall = self.subjson["removeRole"][toRemove][:2]
			if (currentTime - offset) % intervall < waitTime and currentTime > offset:
				role = guilde.get_role(int(toRemove))
				# Remove roles
				for member in role.members:
					await self.helpf.removeRoles(member.id, [toRemove])

	async def giveRoleOnceSubroutineFunction(self, currentTime):
		"""
		param currentTime:	Float time on what the timing will be compared on.

		Gives member a role if conditions are right.
		Scans sub.json for timing, userID and roleID.
		Than determants if they should be carried out and carrys them out.
		"""
		for toGiveOnce in self.subjson["giveRoleOnce"]:
			offset, intervall, userID, roleID = self.subjson["giveRoleOnce"][toGiveOnce]
			if (currentTime - offset) % intervall < waitTime and currentTime > offset:
				# Removes role from member and clears entry in sub.json.
				try:
					self.helpf.giveRoles(userID, roleID)
				except AttributeError as e:
					# When user is not anymore in the guild.
					print("[ERROR] Tried to give member role which is not in the guild.")
					print(traceback.format_exc())

				del self.subjson["giveRoleOnce"][toGiveOnce]
				self.saveSubjson()



	"""
	######################################################################

	sub.json functions.

	######################################################################
	"""

	def saveSubjson(self):
		"""
		Saves subjson to sub.json.
		"""
		with open(self.binpath+"sub.json",'w') as f:
			json.dump(self.subjson, f, indent = 6)

	def addGiveRoleOnce(self, offset, intervall, userID, roleID):
		"""
		param offset:	Starting point as float time. Can be determaint through 'time.mktime(time.strptime("2021 Jan 4 CEST","%Y %b %d %Z"))'
		param intervall:	How long between time windows should be waited as float.
		param userID:	Is the userID from discord user as int
		param roleID:	The id of a role on the discord guilde as int.

		Makes a entry in sub.json to give a role in specified time window.
		Entries will have the lowest key possible.
		The giving of a role is carried out by subRoutine().
		"""
		i = 1
		while str(i) in self.subjson["giveRoleOnce"].keys():
			i += 1
		self.subjson["giveRoleOnce"][str(i)] = [offset, intervall, userID, roleID]
		self.saveSubjson()

	def queueGiveRoleOnceAfter(self, userID, roleID, after, intervallDefaulte = 604800, offsetDefaulte = 345600):
		"""
		param userID:	Is the userID from discord user as int
		param roleID:	The id of a role on the discord guilde as int.
		param after:	Float how long sshould be waited.
		param intervallDefaulte:	Definess intervall as int if no entry is found. Defaulte = 604800 =^= 1 Week.
		param offsetDefaulte:	Offset when a new entry will be created. Defaulte = 345600 =^= Set to Monday.

		Queues a new give role after an existing giveRoleOnce entry.
		Always the last entry by offfset will be queued after.

		When entry does not exist, than a new entry will be added with the intervallDefaulte.
		Only does it if intervallDefaulte is not 0.
		"""
		offset = 0
		intervall = 0
		excetutionTime = None
		# Get last queued giveRoleOnce matching with role. Last is determanted by offset.
		for queueBefor in sorted(self.subjson["giveRoleOnce"]):
			offsetBefor, intervallBefor, userIDBefor, roleIDBefor = self.subjson["giveRoleOnce"][toGiveOnce][:4]
			if roleID == roleIDAfter and offsetBefor > offset:
				offset, intervall = offsetBefor, intervallBefor
				excetutionTime = ((offsetBefor // intervall) + 1) * intervall

		if excetutionTime:
			# When a entry matches search parameters.
			excetutionTime += after
		elif intervallDefaulte:
			# Create new entry ssince no entry is found.
			intervall = intervallDefaulte
			excetutionTime = (((time.time() + offsetDefaulte) // intervall) + 1) * intervall
		if not excetutionTime:
			# When no entry will be created and none is found.
			return excetutionTime
		self.addGiveRoleOnce(excetutionTime, intervall, userID, roleID)
		# Format time to String in form Year Month Day DayName.
		return time.strftime("%Y %b %d %a", excetutionTime)




