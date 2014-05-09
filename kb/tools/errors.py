class DataError(Exception):

	def __init__(self, msg):
		'''
		Raised when essential data is missing
		'''
		self.strerror = msg

class TransferError(Exception):

	def __init__(self, msg, type):
		'''
		Raised when transfer of data has failed
		msg: the error message
		type: the type of error
			1: Transfer timed out
			2: Not all files have been correctly copied
		'''
		self.strerror = msg
		self.typeerror = type