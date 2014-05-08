from xml.dom import minidom
from errors import DataError

def getAnchorFileData(anchor_file, required_fields):
	'''
	Get the required data from the meta_anchor.xml
	file - raise an error if any required data is missing
	'''
	anchor = minidom.parse(anchor_file)
	metadata = anchor.getElementsByTagName('goobi:metadata')
	data = dict()
	for elem in metadata:
		name = elem.getAttribute('name')
		if name in required_fields:
			data[name] = elem.firstChild.nodeValue
	
	for item in required_fields:
		if item not in data: 
			raise DataError("{0} missing value {1}".format(self.anchor_file, item))

	return data