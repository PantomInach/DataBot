import os
import json


def read_rights_of(command, category):
    datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
    rights = json.load(open(datapath + "commandRights.json"))
    if command in rights and category in rights[command]:
        return rights[command][category]
    else:
        return []


if __name__ == "__main__":
    assert read_rights_of("pollsList", "channel") == ["🚮spam"]
