# -*- coding: utf-8
import unittest, imp
tocfile = imp.load_source('toc', '../tools/toc.py')

class tocTests(unittest.TestCase):
	
	def setUp(self):
		self.toc = tocfile.TOC('data/lan.toc')

	def testNewToc(self):
		self.failUnless(self.toc)
	
	def testTocSections(self):
		self.failUnless(len(self.toc.sections) == 3)
		body = self.toc.sections[1]
		self.failUnless(body.title == 'Body')

	def testTocArticles(self):
		body = self.toc.sections[1]
		articles = body.articles
		self.failUnless(len(articles) == 12)
		self.failUnless('Arbejder fra' in articles[0].title)
		self.failUnless('Annemarie' in articles[0].author)
		self.failUnless(articles[1].article_id == '34434476:870971')
		self.failIf(len(articles[1].author) > 0)

	def testIsDbcId(self):
		self.failUnless(tocfile.TOCArticle.isDbcId('34434476:870971'))
		self.failIf(tocfile.TOCArticle.isDbcId('3443447870971'))
		self.failIf(tocfile.TOCArticle.isDbcId('344344a:7870971'))


def run():
	unittest.main()

if __name__ == '__main__':
	run()