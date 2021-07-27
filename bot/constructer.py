from .xpfunk import Xpfunk
from .jsonhandel import Jsonhandel
from .poll import Poll
from .textban import Textban
from .counter import Counter

class Constructer(object):
	"""docg for Constructer"""
	def __init__(self):
		super(Constructer, self).__init__()
		print("\nConstructing jsonhandel Object...")
		self.jh = Jsonhandel()
		print("Constructing xpfunk Object...")
		self.xpf = Xpfunk(self.jh)
		print("Constructing poll Object...")
		self.poll = Poll()
		print("Constructing textban Object...")
		self.tban = Textban()
		print("Constructing counter Object...")
		self.cntr = Counter()


	def giveObjects(self):
		return [self.jh, self.xpf, self.poll, self.tban, self.cntr]		
		