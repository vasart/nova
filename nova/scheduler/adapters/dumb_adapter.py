from nova.scheduler import adapters

class DumbAdapter(adapters.BaseAdapter):
	def __init__(self):
		pass

	def is_trusted(self, host, trust):
		return (True, False)
