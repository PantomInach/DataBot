import json
import os

print(str(os.path.dirname(__file__))+"/data.json")
data = json.load(open(str(os.path.dirname(__file__))+"/data.json"))

a=sorted(data, key=lambda id: int(data[id]["Level"]) if int(data[id]["Level"]) > 5 else -int(data[id]["Level"]))
print(a)
