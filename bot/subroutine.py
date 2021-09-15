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
					time in UTC when role willbe given
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
		self.run = False
		# Indicates if subroutine can be stopped savely.
		self.canStop = True
		# Reads sub.json
		self.binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		self.subjson = json.load(open(self.binpath+"sub.json"))		

	async def startSubRoutine(self):
		"""
		Creates a new asyncio event loop in which the subroutine runs.
		If the subroutine is already running nothing happens.
		"""
		if self.run:
			# Subroutine is running
			return

		self.run = True
		await self.subRoutine()

	async def stopSubRoutine(self):
		if not self.run:
			# Subroutine is not running
			return
		if not self.canStop:
			await self.helpf.log("[Subroutine] Waiting for subRoutine to stop...",2)
		while not self.canStop:
			await asyncio.sleep(0.05)
		await self.helpf.log("[Subroutine] Stopping subRoutine",2)
		self.run = False

	async def subRoutine(self):
		"""
		Runs the subroutine. After a determant waiting time the the features will be called.

		Features implemented (will be carried out in this order):
			Remove role
			Give role once
		"""
		await self.helpf.log("[Subroutine] Started subroutine",2)
		"""
		waitTime says how long the subroutine will sleep between cycles. 
		Also indicates buffer of activities.
		When a time is mentiont in this function, than a time window is ment from 0 to waitTime.
		!!! waitTime must be an int !!!
		"""
		waitTime = 120

		guild = self.helpf.getGuild()
		while self.run:
			self.canStop = False
			currentTime = time.time()

			"""
			Remove role subroutine:
				Continuously removes the role in a given intervall starting on the offset.
			"""
			await self.removeRoleSubroutineFunction(currentTime, waitTime, guild)

			"""
			Give role once:
				Gives a member a role when the time window is hit.
				The time window is defined with an offset and intervall.
				If the intervall is hit beginning on the offset, than only once the role is given. 
			"""
			await self.giveRoleOnceSubroutineFunction(currentTime)

			# Pauses the subroutine.
			self.canStop = True
			for i in range(waitTime):
				if not self.run:
					# Stop subroutine preemptively
					break
				await asyncio.sleep(1)
			

	async def removeRoleSubroutineFunction(self, currentTime, waitTime, guild):
		"""
		param currentTime:	Float time on what the timing will be compared on.

		Removes the role for all users in the guilde.
		First scanns sub.json for 'removeRole' events. 
		Than determants if they should be carried out and carrys them out.
		"""
		for toRemove in self.subjson["removeRole"]:
			if not toRemove.isdigit():
				await self.helpf.log(f"[Subroutine ERROR] In 'removeRoleSubroutineFunction'. Key {toRemove} in removeRole is no role id. Remove key to ressolve this error.",2)
				continue
			offset, intervall = self.subjson["removeRole"][toRemove][:2]
			if (currentTime - offset) % intervall < waitTime and currentTime > offset:
				role = guild.get_role(int(toRemove))
				if role == None:
					await self.helpf.log(f"[Subroutine ERROR] In 'removeRoleSubroutineFunction'. Role with id {toRemove} is not in Guilde. Remove it from 'sub.json' to fix this issue.",2)
				else:
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
		entrysToDelet = []
		for toGiveOnce in self.subjson["giveRoleOnce"]:
			time, userID, roleID = self.subjson["giveRoleOnce"][toGiveOnce]
			if time <= currentTime:
				# Gives role to member and clears entry in sub.json.
				try:
					await self.helpf.giveRoles(userID, [roleID])
				except AttributeError as e:
					# When user is not anymore in the guild.
					await self.helpf.log("[ERROR] Tried to give member role which is not in the guild.",2)
					await self.helpf.log(traceback.format_exc(),2)
				entrysToDelet.append(toGiveOnce)
		for entry in entrysToDelet:
			del self.subjson["giveRoleOnce"][entry]
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

	def addGiveRoleOnce(self, timeWhenGiveRole, userID, roleID):
		"""
		param timeWhenGiveRole:	Unix Epoch time as float when role will be given.
		param userID:	Is the userID from discord user as int.
		param roleID:	The id of a role on the discord guilde as int.

		Makes a entry in sub.json to give a role in specified time window.
		Entries will have the lowest key possible.
		The giving of a role is carried out by subRoutine().
		"""
		if timeWhenGiveRole < time.time():
			return
		i = 1
		while str(i) in self.subjson["giveRoleOnce"].keys():
			i += 1
		self.subjson["giveRoleOnce"][str(i)] = [timeWhenGiveRole, userID, roleID]
		self.saveSubjson()

	def queueGiveRoleOnceAfter(self, userID, roleID, after, timeWhenNothingInQueue):
		"""
		param userID:	Is the userID from discord user as int
		param roleID:	The id of a role on the discord guilde as int.
		param after:	Float how long should be waited.
		param timeWhenNothingInQueue:	Time in float when will be queued if queue is empty.

		Queues a new give role after an existing giveRoleOnce entry, which matches the roleid.
		Always the last entry by offfset will be queued after.

		When entry does not exist, than a new entry will be added with the intervallDefaulte.
		"""
		excetutionTime = timeWhenNothingInQueue
		timesWithRole = [entry[0] for entry in self.subjson["giveRoleOnce"].values() if entry[2] == roleID]
		if timesWithRole:
			# Entry exists => queue new entry
			lastEntryTime = max(timesWithRole, key =  lambda entry: entry)
			excetutionTime = lastEntryTime + after
		self.addGiveRoleOnce(excetutionTime, userID, roleID)
		# Format time to String in form Year Month Day DayName.
		return time.strftime("%Y %b %d %a %H:%M:%S", time.localtime(excetutionTime))

