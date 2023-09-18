from sqlitedict import SqliteDict
from enum import Enum
from time import time
import atexit
from typing import Dict, Tuple

# How many days the temp leaderboard maximal holds.
TIME_FRAME = 30


class XPTypes(Enum):
    OTHER = 0
    VOICE = 1
    TEXT = 2
    TEXTCOUNT = 3


class SortBy(Enum):
    NULL = (0, 0, 0, 0)
    VOICE_TEXT = (0, 1, 1, 0)
    VOICE = (0, 1, 0, 0)
    TEXTCOUNT = (0, 0, 0, 1)


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
                cls.dbPath = "data/temp_userdata.sqlite"
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

    def addUser(self, user: int | str) -> bool:
        """
        Adds user to DB if not already present.

        return -- if a new user was created.
        """
        if self.userInDB(user):
            return False
        self.db[str(user)] = []
        return True

    def removeUser(self, user: int | str):
        if self.userInDB(user):
            del self.db[str(user)]

    def addEntry(self, user: int | str, xpType: XPTypes, amount: int):
        if not self.addUser(user):
            self.removeOutdatedUserEntries(user)
        self.db[str(user)] += [(time(), xpType, amount)]

    def removeOutdatedUserEntries(self, user: int | str):
        self.addUser(user)
        self.db[str(user)] = list(
            filter(
                lambda entry: entry[0]
                > TempLeaderboard._oldestAllowedTime(self.timeFrame),
                self.db[str(user)],
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
        return self.getUserSummedDataInTimeFrame(user, TIME_FRAME)

    def getUserSummedDataInTimeFrame(
        self, user: int | str, timeFrame: int
    ) -> Dict[XPTypes, int] | None:
        self.removeOutdatedUserEntries(user)
        if not self.userInDB(user):
            return None
        entries = self.db[str(user)]
        res = {}
        for xpType in XPTypes:
            total = sum(
                map(
                    lambda entry: entry[2],
                    filter(
                        lambda entry: entry[1] == xpType
                        and entry[0] > self._oldestAllowedTime(timeFrame),
                        entries,
                    ),
                )
            )
            res[xpType] = total
        return res

    def getAllUserSummedData(self) -> Dict[str, Dict[XPTypes, int]]:
        return self.getAllUserSummedDataInTimeFrame(self.timeFrame)

    def getAllUserSummedDataInTimeFrame(
        self, timeFrame: int
    ) -> Dict[str, Dict[XPTypes, int]]:
        return {
            user: self.getUserSummedDataInTimeFrame(user, timeFrame)
            for user in self.db.keys()
        }

    def sortDataWindowBy(
        self, sortBy: SortBy, window: None | int = None
    ) -> Tuple[Tuple[str, Dict[XPTypes, int]]]:
        if window is None:
            window = self.timeFrame
        sortedData = sorted(
            self.getAllUserSummedDataInTimeFrame(window).items(),
            key=lambda tup: TempLeaderboard._applySortMask(sortBy, tup[1]),
            reverse=True,
        )
        return list(sortedData)

    @staticmethod
    def _applySortMask(sortBy: SortBy, data: Dict[XPTypes, int]) -> int:
        return sum((x * y for x, y in zip(data.values(), sortBy.value)))

    @staticmethod
    def _oldestAllowedTime(timeFrame: int) -> int:
        return time() - (86400 * timeFrame)

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
