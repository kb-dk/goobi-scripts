class DataError(Exception):

	def __init__(self, msg):
		'''
		Raised when essential data is missing
		'''
		self.strerror = msg

class TransferError(Exception):

	def __init__(self, msg):
		'''
		Raised when transfer of data has failed
		msg: the error message

		'''
		self.strerror = msg

class TransferTimedOut(Exception):
	def __init__(self,msg):
		'''
		Raised when transfer of data has timed out
		msg: the error message

		'''
		self.strerror = msg