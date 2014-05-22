import csv

class TOC(object):
	sections = [] # a list of Section objects (see below)

	def __init__(self, path):
		'''
		Create a new toc representation
		based on the data in a LIMB *.toc file
		'''
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
	
	def correctSections(self):
		'''
		If a section does not have any member articles
		add the section itself as an article
		Elif the section has articles, but they start after
		the sections's start page, do the same.
		'''
		for s in self.sections:			
			#print "{0} is gt than {1}? {2}".format(s.articles[0].start_page, s.start_page, (s.articles[0].start_page > s.start_page))
			if len(s.articles) == 0:
				art = TOCArticle(['1', s.title, s.start_page])
				s.addArticle(art)
			elif s.articles[0] and s.articles[0].start_page > s.start_page:
				art = TOCArticle(['1', s.title, s.start_page])
				s.articles.insert(0, art) # add article to start of articles list


	def getSections(self):
		return self.sections

	def addSection(self, section):
		self.sections.append(section)

	def prettyPrint(self):
		for s in self.sections:
			print "==========================="
			print "Section: {0}".format(s.title)
			for a in s.articles:
				print u"Title: {0} | Author: {1} | Start Page {2}".format(a.title, a.author, a.start_page) 

	def __decodeRow(self, row):	
		decoded_row = []
		for i, val in enumerate(row):
			decoded_row.insert(i, val.decode('utf-8').replace('"', ''))
		return decoded_row


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
	start_page = 0
	end_page = 0

	def __init__(self, line_array):
		'''
		Based on an article line
		create title, author, startpage 
		'''
		if '|' in line_array[1]:
			self.author = line_array[1].split('|')[0].strip()
			self.title = line_array[1].split('|')[1].strip()
		else: 
			self.author = ""
			self.title = line_array[1]
		self.start_page = int(line_array[2])