# -*- coding: utf-8
import unittest, imp, types
marcfile = imp.load_source('toc', '../tools/marcxml.py')

class marcXmlTests(unittest.TestCase):
	
	def setUp(self):
		self.marcXml = marcfile.marcXml.initFromFile('data/dbc_marc.xml')

	def testNewMarcXml(self):
		self.failUnless(self.marcXml)

	def testData(self):
		self.failUnless(self.marcXml.data['pages'] == 'S. 5-11')
		self.failUnless(' continues' in self.marcXml.data['title'])

	def testMultipleAuthors(self):
		authors = self.marcXml.data['other_authors']
		self.failUnless(type(authors) == types.ListType)
		self.failUnless(len(authors) > 0)
		self.failUnless(authors[0]['given_name'] == 'Anders')

def run():
	unittest.main()

if __name__ == '__main__':
	run()