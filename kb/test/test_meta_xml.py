# -*- coding: utf-8
import unittest, imp, types
metafile = imp.load_source('toc', '../tools/goobi/meta_xml.py')

class metaXmlTests(unittest.TestCase):

	def setUp(self):
		meta = metafile.MetaXml
		art_data = [
			{'name' : 'Abstract', 'data' : 'This article seeks to...'}, 
			{'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
			{'name' : 'Author', 'type' : 'person', 'fields' : [
					{'tag' : 'goobi:firstName', 'data' : 'Peter'},
					{'tag' : 'goobi:lastName', 'data' : 'Turchin'}
			]}
		]
		self.xml = meta.generateArticleXml('111', art_data)

	def testGenerateArticleXml(self):
		metadataFields = self.xml.getElementsByTagName('goobi:metadata')
		self.failUnless(len(metadataFields) == 3)
	
	def testGenerateMetadata(self):
		authorFirstName = self.xml.getElementsByTagName('goobi:firstName').item(0).firstChild
		self.failUnless(authorFirstName.nodeValue == 'Peter')


def run():
	unittest.main()

if __name__ == '__main__':
	run()