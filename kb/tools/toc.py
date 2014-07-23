import csv, re

class TOC(object):
	sections = [] # a list of Section objects (see below)

	def __init__(self, path):
		'''
		Create a new toc representation
		based on the data in a LIMB *.toc file
		'''
		self.sections = []
		data = []
		with open(path, 'r') as toc_csv:
			reader = csv.reader(toc_csv, delimiter=',', quotechar='"')
			# skip the first line as this just contains header data
			iterreader = iter(reader) 
			next(iterreader)
			sect = None
			for row in iterreader:
				# decode the row
				row = self.__decodeRow(row)
				try:
					level = row[0]
					if level == '0': # this is a section
						if sect: self.addSection(sect) # if we have a section save it
						sect = TOCSection(row) # create a new section
					else: # this is an article
						art = TOCArticle(row)
						if sect: sect.addArticle(art)
				# if there's some problem with the input row, skip it
				except IndexError:
					error = ('TOC row not parsed successfully {0}')
					error = error.format(",".join(row))
					raise ValueError(error)
			# As we exit the loop we will have one more section we need to save
			if sect: self.addSection(sect)
			self.correctSections()
			self.addArticleNumbers() 
	
	def correctSections(self):
		'''
		If a section does not have any member articles
		add the section itself as an article
		Elif the section has articles, but they start after
		the sections's start page, do the same.
		'''
		for s in self.sections:			
			if len(s.articles) == 0:
				art = TOCArticle(['1', s.title, s.start_page])
				s.addArticle(art)
			elif s.articles[0] and s.articles[0].start_page > s.start_page:
				art = TOCArticle(['1', s.title, s.start_page])
				s.articles.insert(0, art) # add article to start of articles list

	def addArticleNumbers(self):
		index = 1
		for article in self.allArticles():
			article.number = index
			index += 1

	def getSections(self):
		return self.sections

	def addSection(self, section):
		self.sections.append(section)

	def addEndPageInfo(self, pdfinfo, overlapping_articles=False):
		'''
		Use data from toc and pdfinfo to add end_page
		info for Toc articles
		returns dict with new end_page field
		'''
		all_articles = self.allArticles()
		for index, article in enumerate(all_articles):
			# we need to figure out how to get the end page for the article
			start_page = article.start_page
			if index != len(all_articles) - 1: # if this is not the last article
				next_item = all_articles[index + 1]
				if overlapping_articles: 
					# last page is the start of the next items page
					end_page = next_item.start_page
				else:
					# when we're not doing overlapping pages
					# last page is the page before the next item's start page 
					# unless that page is less than current page
					if next_item.start_page-1 >= start_page:
						end_page = next_item.start_page -1
					else:
						end_page = start_page
			# if this is the last article - we need to take until the pdf's end page
			# as given by pdfinfo
			else:
				end_page = int(pdfinfo['Pages'])
			article.end_page = end_page


	def getFrontSection(self):
		return self.__getSection('Front Matter')

	def getBodySection(self):
		return self.__getSection('Body')

	def getBackSection(self):
		return self.__getSection('Back Matter')			

	def prettyPrint(self):
		for s in self.sections:
			print "==========================="
			print "Section: {0}".format(s.title)
			print "==========================="
			for a in s.articles:
				print u"Title: {0}... | Author: {1} | StartPage: {2} | EndPage {3} | Number {4}"\
				.format(a.title[0:5], a.author, a.start_page, a.end_page, a.number) 

	def __decodeRow(self, row):	
		decoded_row = []
		for i, val in enumerate(row):
			decoded_row.insert(i, val.decode('utf-8').replace('"', ''))
		return decoded_row

	def allArticles(self):
		all_articles = []
		for s in self.sections:
			for a in s.articles:
				all_articles.append(a)
		return all_articles

	
	def __getSection(self, name):
		for s in self.sections:
			if s.title == name: return s
		return None



class TOCSection(object):

	title = ''
	start_page = 0

	def __init__(self, line_array):
		'''
		based on a toc line, create new section object
		'''
		self.articles = []
		self.title = line_array[1]
		self.start_page = int(line_array[2])

	def addArticle(self, article_obj):
		self.articles.append(article_obj)

class TOCArticle(object):

	author = ''
	title = ''
	article_id = ''
	start_page = 0
	end_page = 0
	number = 0

	def __init__(self, line_array):
		'''
		Based on an article line
		create title, author, startpage and article_id if relevant
		'''
		if '|' in line_array[1]:
			self.author = line_array[1].split('|')[0].strip()
			self.title = line_array[1].split('|')[1].strip()
		elif self.isDbcId(line_array[1]):
			self.author = ""
			self.title = ""
			self.article_id = line_array[1]
		else: 
			self.author = ""
			self.title = line_array[1]
		self.start_page = int(line_array[2])

	@staticmethod
	def isDbcId(s):
		'''
		Given a string, check if it matches
		pattern <digits>:<digits>
		in which case it is a DBC id
		'''
		pattern = re.compile('\d+:\d+')
		return pattern.match(s)