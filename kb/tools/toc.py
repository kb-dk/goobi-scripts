#!/usr/bin/python
# -*- encoding: utf-8 -*-
import csv, re
from marcxml import MarcXml

class TOC(object):
    sections = [] # a list of Section objects (see below)

    def __init__(self, path, dbc_service, pdfinfo, overlapping_articles,
                 logger = None):
        '''
        Create a new toc representation
        based on the data in a LIMB *.toc file
        '''
        self.sections = []
        self.page_offset = None
        data = []
        self.dbc_service = dbc_service
        self.logger = logger
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
                        if art.article_id:
                            art = self.parseDbcDataToArticle(art)
                        if sect: sect.addArticle(art)
                # if there's some problem with the input row, skip it
                except IndexError:
                    error = ('TOC row not parsed successfully {0}')
                    error = error.format(",".join(row))
                    raise ValueError(error)
            # As we exit the loop we will have one more section we need to save
            if sect: self.addSection(sect)
        # Add page offset, only to dbc-articles
        self.addPageOffset()
        # Sort the articles by their start pages -> they may come in random order
        self.sortPages()
        # Fix the sections, so empty sections will appear as articles
        self.correctSections()
        # Add end page to those articles where it hasn't been set (i.e. limb toc articles)
        self.addEndPageInfo(pdfinfo, overlapping_articles)
        # Add article numbers to the articles for OJS (?)
        self.addArticleNumbers() 
    
    def sortPages(self):
        temp_sections = {}
        sorted_sections = []
        for s in self.sections:
            if not s.articles: continue
            temp_articles = dict()
            sorted_articles = []
            for a in s.articles: # Sort list of articles - articles can have same start page
                if a.start_page not in temp_articles:
                    temp_articles[a.start_page] = [a]
                else:
                    temp_articles[a.start_page].append(a)
            for sa in sorted(temp_articles.keys()):
                sorted_articles.extend(temp_articles[sa])
            s.articles = sorted_articles
            if s.start_page not in temp_sections:
                    temp_sections[s.start_page] = [s]
            else:
                temp_sections[s.start_page].append(s)
        for ss in sorted(temp_sections.keys()):
            sorted_sections.extend(temp_sections[ss])
        self.sections = sorted_sections
    
    def parseDbcDataToArticle(self,article):
        '''
        Gets metadata from DBC data and adds this to the article object
        :param article:
        '''
        dbc_data = self.getDBCData(article.article_id).data
        # Get title
        article.title = self.getFromDbcData(dbc_data,'title', '')
        # Get update time
        article.update_time = self.getFromDbcData(dbc_data,'update_time', '')
        # Get authors
        article.authors = self.getAuthorsFromDbcData(dbc_data)
        # Get start and end page
        article.start_page,article.end_page = self.getPagesFromDbcData(dbc_data,article)
        # Get subjects
        article.subjects = list(set(self.getSubjectsFromDbcData(dbc_data))) # remove duplicates with list+set
        # Get language
        article.language = self.getLanguageFromDbcData(dbc_data)
        # Get description
        article.description = self.getFromDbcData(dbc_data,'description', '')
        # Get ISSN
        article.issn = self.getFromDbcData(dbc_data,'issn', '')
        # Get sub title
        article.sub_title = self.getFromDbcData(dbc_data,'sub_title', '')
        
        return article
        
        
    def getLanguageFromDbcData(self,dbc_data):
        '''
        Returns language extracted from DBC metadata for an article
        
        Converts "ISO 639-2/B:1998" to "ISO 639-1"
        
        :param dbc_data: parsed metadata from DBC MarcX file
        '''
        dbc_to_goobi = {'dan':'da',
                        'swe': 'sv',
                        'nor': 'no',
                        'eng': 'en',
                        }
        lang = self.getFromDbcData(dbc_data,'language', 'da')
        return dbc_to_goobi.get(lang,'da')
        
    def getSubjectsFromDbcData(self,dbc_data):
        '''
        Returns a list of keywords extracted from DBC metadata for an article
        :param dbc_data: parsed metadata from DBC MarcX file
        '''
        return map(lambda k: k['subject'],self.getFromDbcData(dbc_data,'subjects', []))
        
    def getAuthorsFromDbcData(self,dbc_data):
        '''
        Returns a list of authors extracted from DBC metadata for an article
        :param dbc_data: parsed metadata from DBC MarcX file
        '''
        authors = []
        given_name = self.getFromDbcData(dbc_data,'author_given_name')
        family_name = self.getFromDbcData(dbc_data,'author_family_name')
        authors.append((given_name, family_name))
        # create elements for any other authors
        for a in dbc_data['other_authors']:
            authors.append((a['given_name'],a['family_name']))
        return authors
    
    def getFromDbcData(self,dbc_data, key,default=''):
        if key in dbc_data:
            return dbc_data[key]
        else:
            return default
    
    def getPagesFromDbcData(self,dbc_data,toc_data):
        '''
        Extracts start and end page from from DBC metadata for an article.
        Tries to set page offset for the pages in the volume. toc_data is used
        for this.
        
        :param dbc_data: parsed metadata from DBC MarcX file
        :param toc_data: parsed metadata from TOC file from LIMB
        '''
        if not 'pages' in dbc_data:
            err = ('Sektionen "pages" er ikke tilstede for artiklen "{0}" med '
                   'id {1}.')
            err = err.format(dbc_data['title'],toc_data.article_id)
            if self.logger: self.logger.info_message(err)
        if not isinstance(dbc_data['pages'],basestring):
            err = ('Sektionen "pages" indeholder ikke tekst for artiklen "{0}" '
                   'med id {1}.')
            err = err.format(dbc_data['title'],toc_data.article_id)
            if self.logger: self.logger.info_message(err)
        pages = dbc_data['pages']
        start_page = end_page = 0
        # Different parsings of pages
        ## of the format e.g. "S. 6-26, 124"
        re_twopages_1 = re.compile('[Ss]\.[ ]*\d+-\d+.*')
        ## of the format e.g. "6-26"
        re_twopages_2 = re.compile('\d+-\d+')
        ## of the format e.g. "S. 6, 124"
        re_onepage_1 = '[Ss]\.[ ]*\d+.*'
        extr_re = re.compile('\d+')
        if not re_twopages_1.match(pages) or not re_twopages_2.match(pages):
            start_page,end_page = map(lambda x: int(x), extr_re.findall(pages)[:2])
        elif not re_onepage_1.match(pages):
            start_page = end_page = int(extr_re.findall(pages)[0])
        else:
            err = ('Det var ikke muligt at anvende start og slutsidetal for '
                   'artiklen "{0}" med id {1}. Disse skal indtastes manuelt '
                   ' og de �vrige af h�ftets artiklers sidetal skal tjekkes.')
            err = err.format(dbc_data['title'],toc_data.article_id)
            if self.logger: self.logger.info_message(err)
        if (self.page_offset is None and # Not yet set
            toc_data.start_page > 1 and   # page number set for article
            toc_data.start_page > start_page): # volume has offset
            self.page_offset = toc_data.start_page-start_page
        return start_page,end_page
    
    def getDBCData(self, article_id):
        url = self.dbc_service.format(article_id)
        return MarcXml.initFromWeb(url)
    
    def addPageOffset(self):
        if self.page_offset is None: # page_offset not set -> do nothing
            return 
        for s in self.sections:
            for a in s.articles:
                if not a.article_id: continue # Only add offset for the ones from dbc
                if a.start_page > 0:
                    a.start_page = a.start_page + self.page_offset
                if a.end_page > 0:
                    a.end_page = a.end_page + self.page_offset
    
    def correctSections(self):
        '''
        If a section does not have any member articles
        add the section itself as an article
        Elif the section has articles, but they start after
        the sections's start page, do the same.
        '''
        for s in self.sections:
            if len(s.articles) == 0:
                print(s.title)
                print(s.start_page)
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
            if article.end_page > 0: continue # skip article if end_page is set
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


    def getFrontMatterSection(self):
        return self.__getSection('Front Matter')

    def getArticlesSection(self):
        return self.__getSection('Body')

    def getBackMatterSection(self):
        return self.__getSection('Back Matter')            

    def prettyPrint(self):
        for s in self.sections:
            print("===========================")
            print("Section: {0}".format(s.title))
            print("===========================")
            for a in s.articles:
                print(u"Title: {0}... | Author: {1} | StartPage: {2} | EndPage {3} | Number {4}"
                .format(a.title[0:5].encode('utf-8'), a.author, a.start_page, a.end_page, a.number)) 
    
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

    
    def erroneousPages(self):
        '''
        Checks if all the pages are the same, usually error is all page numbers
        are equal 1
        '''
        pages = set()
        for a in self.allArticles():
            pages.add(a.start_page)
        if len(pages) <= 1:
            return True
        return False
    

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
    authors = []
    title = ''
    update_time = ''
    sub_title = ''
    subjects = []
    description = ''
    content_description = ''
    issn = ''
    language = 'da'
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