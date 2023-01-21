import json
import time
import os


class Sub(object):
    """
    Handels interaction with 'data/sub.json'.
    sub.json stores critical information, which should be retained at a restart for 'cogs/commandsubroutine.py'.

    sub.json foramting:
                    "Name of subRoutine":
                            Information for subroutine

                    "removeRole":{
                            "ID of role to remove": [
                                    offset as float,
                                    interval as int,
                            ]
                    },

                    "giveRoleOnce":{
                            "some number": [
                                    time in Unix Epoch when role will be given
                                    userID to whom the role is given as int,
                                    ID of role to give as int
                            ]
                    }

    Example for remove role:
            Offset is 2021.01.04 CEST == 1609711200.0. Can be determaint through 'time.mktime(time.strptime("2021 Jan 4 CEST","%Y %b %d %Z"))'.
            interval is 1 Week == 604800
            So every Monday the role will be removed.
    """

    def __init__(self):
        super(Sub, self).__init__()
        self.subpath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
        self.subjson = json.load(open(self.subpath + "sub.json"))

    def _reloadSubjson(func):
        """
        Type:	Decorator for functions in Sub using self.subjson

        Reloads the sub.json file and executes the function.
        Midigates race conditions and data corruption when creating multiple Sub objects.
        """

        def decorator(self, *args, **kwargs):
            self.subjson = json.load(open(self.subpath + "sub.json"))
            return func(self, *args, **kwargs)

        return decorator

    def reloadSubjson(self):
        """
        Reloads sub.json from file.
        """
        self.subjson = json.load(open(self.subpath + "sub.json"))

    def saveSubjson(self):
        """
        Saves subjson to sub.json.
        """
        with open(self.subpath + "sub.json", "w") as f:
            json.dump(self.subjson, f, indent=6)

    @_reloadSubjson
    def getRoleRemoveIDs(self):
        """
        Returns all keys, which are the role IDs, from removeRole.
        """
        return self.subjson["removeRole"].keys()

    @_reloadSubjson
    def getContantOfRoleRemoveID(self, id):
        """
        param id:	ID of role to remove.

        Gets the offset and interval of a removeRole entry from sub.json.
        If not found -> return [0,0]
        """
        if id not in self.subjson["removeRole"]:
            return [0, 0]
        return self.subjson["removeRole"][id][:2]

    def addGiveRoleOnce(self, timeWhenGiveRole, userID, roleID):
        """
        param timeWhenGiveRole:	Unix Epoch time as float when role will be given.
        param userID:	Is the user ID from discord user as int.
        param roleID:	The ID of a role on the discord guild as int.

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
        param userID:	Is the user ID from discord user as int
        param roleID:	The ID of a role on the discord guild as int.
        param after:	Float how long should be waited.
        param timeWhenNothingInQueue:	Time in float when will be queued if queue is empty.

        Queues a new give role after an existing giveRoleOnce entry, which matches the roleID.
        Always the last entry by offfset will be queued after.

        When entry does not exist, a new entry will be added with the intervalDefaulte.
        """
        excetutionTime = timeWhenNothingInQueue
        timesWithRole = [
            entry[0]
            for entry in self.subjson["giveRoleOnce"].values()
            if entry[2] == roleID
        ]
        if timesWithRole:
            # Entry exists => queue new entry
            lastEntryTime = max(timesWithRole, key=lambda entry: entry)
            excetutionTime = lastEntryTime + after
        self.addGiveRoleOnce(excetutionTime, userID, roleID)
        # Format time to String in form Year Month Day DayName.
        return time.strftime("%Y %b %d %a %H:%M:%S", time.localtime(excetutionTime))

    @_reloadSubjson
    def getGiveRoleOnceIDs(self):
        """
        Returns all keys, which are the role IDs, from giveRoleOnce.
        """
        return self.subjson["giveRoleOnce"].keys()

    @_reloadSubjson
    def getContantOfGiveRoleOnceID(self, id):
        """
        param id:	ID of role to give.

        Gets the offset and interval of a removeRole entry from sub.json.
        If not found -> return [0,0,0]
        """
        if id not in self.subjson["giveRoleOnce"]:
            return [0, 0, 0]
        return self.subjson["giveRoleOnce"][id][:3]

    @_reloadSubjson
    def deleteGiveRoleOnce(self, ids):
        """
        param ids:	List of IDs which should be removed from sub.json giveRoleOnce

        Removes all giveRoleOnce specified by the given IDs if they are in sub.json giveRoleOnce.
        """
        for id in ids:
            if id in self.subjson["giveRoleOnce"]:
                del self.subjson["giveRoleOnce"][id]
        self.saveSubjson()
