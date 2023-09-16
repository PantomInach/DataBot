from sqlitedict import SqliteDict
from enum import Enum
from time import time
import atexit
from typing import Dict

# How many days the temp leaderboard maximal holds.
TIME_FRAME = 30


class XPTypes(Enum):
    OTHER = 0
    VOICE = 1
    TEXT = 2


class TempLeaderboard(object):
    _instance = None

    def __new__(
        cls,
        dbFilePath=None,
        overrideSingelton=False,
        timeFrame=TIME_FRAME,
    ):
        if cls._instance is None or overrideSingelton:
            cls._instance = super(TempLeaderboard, cls).__new__(cls)
            cls.timeFrame = timeFrame
            if not dbFilePath:
                cls.dbPath = cls.datapath + "temp_userdata.sqlite"
            else:
                cls.dbPath = dbFilePath

            cls.db = SqliteDict(cls.dbPath, outer_stack=True, autocommit=True)

            atexit.register(TempLeaderboard._cleanup, cls.db)
        return cls._instance

    def userInDB(self, user: int | str) -> bool:
        """
        Keyword arguments:
        user -- user id as int or str
        """
        return str(user) in self.db.keys()

    def addUser(self, user: int | str):
        if self.userInDB(user):
            return
        self.db[str(user)] = []

    def removeUser(self, user: int | str):
        if self.userInDB(user):
            del self.db[str(user)]

    def addEntry(self, user: int | str, xpType: XPTypes, amount: int):
        self.addUser(user)
        self.db[str(user)] += [(time(), xpType, amount)]

    def removeOutdatedUserEntries(self, user: int | str):
        self.addUser(user)
        daysInSeconds = 89400
        self.db[str(user)] = list(
            filter(
                lambda entry: time() < daysInSeconds *
                self.timeFrame + entry[0],
                self.db[str(user)]
            )
        )

    def removeAllOutdatedEntries(self):
        for user in self.db.keys():
            self.removeOutdatedUserEntries(user)

    def removeEmptyUser(self):
        for user in self.db.keys():
            if not self.db[user]:
                del self.db[user]

    def getUserSummedData(self, user: int | str) -> Dict[XPTypes, int] | None:
        self.removeOutdatedUserEntries(user)
        if not self.userInDB(user):
            return None
        entries = self.db[str(user)]
        res = {}
        for xpType in XPTypes:
            total = sum(map(lambda entry: entry[2], filter(
                lambda entry: entry[1] == xpType, entries)))
            res[xpType] = total
        return res

    def getAllUserSummedData(self) -> Dict[str, Dict[XPTypes, int]]:
        return {user: self.getUserSummedData(user) for user in self.db}

    @classmethod
    def _cleanup(cls, db):
        """
        Method closing the database file, when the object is destroyed.
        Is defined to be executed in the constructor with 'atexit'.

        Keyword arguments:
        db -- SqliteDict database object, which should be closed.
        """
        print("[TempLeaderboard] Closing Databank")
        db.commit()
        db.close()
