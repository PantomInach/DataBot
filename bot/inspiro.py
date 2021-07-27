import requests

class Inspiro(object):
	"""docstring for Inspiro"""
	def __init__(self):
		super(Inspiro, self).__init__()
		self.url = "https://inspirobot.me/api?generate=true"

	def getPictureUrl(self):
		r = requests.get(self.url)
		return str(r.content)[2:-1]