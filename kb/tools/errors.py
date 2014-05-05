class DataError(Exception):

	def __init__(self, msg):
		'''
		Raised when essential data is missing
		'''
		self.strerror = msg
