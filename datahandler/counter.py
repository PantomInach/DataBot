import json
import os
import time

class Counter(object):
	"""
	Work in progress.
	"""
	def __init__(self):
		super (Counter, self).__init__()
		self.datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
		self.counterData = json.load(open(self.datapath+"counter.json"))

	def saveCounter(self):
		with open(self.datapath+"counter.json",'w') as f:
			json.dump(self.counterData, f ,indent = 6)
		self.counterData = json.load(open(self.datapath+"counter.json"))

	def createCounter(self, counterName):
		counterID = 1
		while str(i) in [x for x in self.counterData]:
			counterID += 1
		self.counterData[str(counterID)] = {'counterName':counterName, 'createTime':time.time(), 'counterAdd':[]}
		self.saveCounter()

	def isInCounter(self, counterID):
		return str(counterID) in [x for x in self.counterData]

	def addCounter(self, counterID, value):
		if self.isInCounter(counterID):
			self.counterData['counterAdd'].append([value, time.time()])
			self.saveCounter()
			return True
		return False

	def getTotalFromTime(self, counterID, start):
		if self.isInCounter(counterID):
			value = 0
			for x in self.counterData:
				if time.time() - x[1] < start:
					value += x[0]
			return value
		return None

	def getTotal(self, counterID):
		if self.isInCounter(counterID):
			return self.getTotalFromTime(counterID, self.counterData['CreateTime'])
		return None

	def getMonth(self, counterID):
		if self.isInCounter(counterID):
			return self.getTotalFromTime(counterID, 2592000)
		return None

	def getCounterSting(self, counterID):
		pass

	def getCounterStrings(self):
		pass