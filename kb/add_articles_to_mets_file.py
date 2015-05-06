#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from goobi.goobi_step import Step
import os
from tools import tools as tools
from tools.toc import TOC
from tools.marcxml import MarcXml 
from tools.xml_tools import dict_tools, xml_tools
from tools.mets import mets_tools as mets_tools, mets_tools
import pprint
import sys
import traceback

class AddArticlesToMetsFile( Step ):

    def setup(self):
        self.name = 'Indsæt indholdsfortegnelse i METS metadata'
        self.config_main_section = 'add_articles_to_mets_file'
        self.essential_config_sections = set( ['process_folder_structure',
                                               'process_files',
                                               'dbc'] )
        self.essential_commandlines = {
            'process_path' : 'folder'
        }

    def step(self):
        try:
            self.getVariables()
            self.getPdf()
            self.parseTocFile()
            self.isIssnSet()
            self.buildXml()
            self.writeXml()
        except ValueError as e:
            return str(e) + str(traceback.format_exc())
        except IOError as e:
            return str(e) + str(traceback.format_exc())
        except Exception as e:
            return str(e) + str(traceback.format_exc())

    def getVariables(self):
        '''
        This method pulls in all the variables
        from the command line and the config file 
        that are necessary for its running.
        We need a path to our toc file, our meta.xml
        and a link to our DBC data service (eXist API).
        Errors in variables will lead to an 
        Exception being thrown.
        '''
        self.page_offset = None
        self.issnSet = False
        
        process_path = self.command_line.process_path
        toc_dir = os.path.join(
            process_path, 
            self.getConfigItem('metadata_toc_path', section='process_folder_structure')
        )
        toc_name = tools.getFirstFileWithExtension(toc_dir, '.toc')
        self.toc_file_path = os.path.join(toc_dir, toc_name)
        
        
        self.service_url = self.getConfigItem('dbc_service', section='dbc')
        self.meta_file = os.path.join(
            self.command_line.process_path, 
            self.getConfigItem('metadata_goobi_file', section='process_files')
        )
        # Parse initial Goobi METS file to a dictionary tree for processing
        self.meta_data,_ = dict_tools.parseXmlToDict(self.meta_file)
        
        # For pdf info
        pdf_input = self.getConfigItem('doc_limbpdf_path',
                                       section= 'process_folder_structure')
        self.pdf_input_dir = os.path.join(process_path, pdf_input)
        
        # parse for overlapping articles
        self.overlapping_articles = self.getSetting('overlapping_articles',
                                                    'bool',default=True)
        # parse boolean from command line - for overlapping articles
        self.default_language = self.getSetting('default_language',
                                                'string',default='da')

    def getDBCData(self, article_id):
        url = self.service_url.format(article_id)
        return MarcXml.initFromWeb(url)

    def getPdf(self):
        self.pdf_name = tools.getFirstFileWithExtension(self.pdf_input_dir, '.pdf')
        self.pdf_path = os.path.join(self.pdf_input_dir, self.pdf_name)
        self.pdfinfo = tools.pdfinfo(self.pdf_path)

    def parseTocFile(self):
        self.toc_data = TOC(self.toc_file_path,self.service_url,
                            self.pdfinfo, self.overlapping_articles,
                            self.glogger)
        #=======================================================================
        # Various checks of the toc-file
        #=======================================================================
        data_check = self.toc_data.erroneousPages()
        if data_check == 1:
            msg = ('NB!!! Der er kun en artikel for hæftet. Flere kan oprettes '
                   ' via Goobis metadata-editor eller hæftet kan sendes '
                   ' LIMB igen. Suk!')
            self.error_message(msg)
        elif data_check == 2:
            msg = ('NB!!! En fejl i LIMB har medført, at alle hæftets artikler '
                   'har samme startside. Dette skal rettes manuelt i '
                   'METS-editoren for hver enkelt artikel. Suk!')
            self.error_message(msg)

    def writeXml(self):
        '''
        Write the xml generated back to file
        '''
        xml_tools.writeDictTreeToFile(self.meta_data,self.meta_file)

    def isIssnSet(self):
        '''
        Goes through and metadata in dmd_sec in mets.xml file to see if the ISSN
        field has been set. If so set self.issnSet to True else to False. 
        '''
        self.issnSet = mets_tools.hasMetadataField(self.meta_data,'ISSN')
    
    def addIssnToPeriodical(self, issn):
        '''
        Adds the field ISSN to the doc stuct type PeriodicalVolume, if it isn't
        already set.
        :param issn:
        '''
        self.issnSet = mets_tools.addFieldToDocType(self.meta_data,
                                                    'PeriodicalVolume',
                                                    'ISSN',issn)

    def buildXml(self):
        '''
        Given a toc object consisting of articles with dbc ids
        use the DBC service to     generate data for each article.
        When all data is created, append this to the exising
        meta.xml data
        '''
        self.createFrontMatterSection()
        self.createArticlesSection()
        self.createBackMatterSection()
        mets_tools.addOffsetToPhysicalStructMap(self.meta_data,
                                                self.toc_data.page_offset)
        self.meta_data = mets_tools.expandPagesFromChildrenToParent(self.meta_data)
        
    def createFrontMatterSection(self):
        articles = self.toc_data.getFrontMatterSection()
        if articles: self.createArticles(articles,'FrontMatter')
    
    def createArticlesSection(self):
        articles = self.toc_data.getArticlesSection()
        if articles: self.createArticles(articles,'Articles')
    
    def createBackMatterSection(self):
        articles = self.toc_data.getBackMatterSection()
        if articles: self.createArticles(articles,'BackMatter')
        
    def createArticles(self,section,section_type):
        if not mets_tools.docTypeExists(self.meta_data, section_type):
            # Create section, e.g. FrontMatter if it doesn't exists
            section_data = {'doc_type': section_type,'content': [{'name':'TitleDocMain','data':section_type}]}
            self.meta_data = mets_tools.addNewDocStruct(self.meta_data,section_data)
        articles = section.articles
        #TODO: Create articles-docstruct if not already there
        section_attrib = ('TYPE',section_type)
        for article in articles:
            article_data = self.createArticleData(article)
            if article_data and not self.articleExists(article_data):
                self.meta_data = mets_tools.addNewDocStruct(self.meta_data,
                                                            article_data,
                                                            section_attrib)
    
    def articleExists(self,article_data):
        article_title = [c['data'] for c in article_data['content']
                         if c['name'] == 'TitleDocMain'][0]
        start_page = article_data['start_page']
        end_page = article_data['end_page']
        if mets_tools.articleExists(self.meta_data, article_title,
                                    start_page,end_page):
            err = ('Article "{0}" already exist in METS-file. Possible '
                   'duplicate. Article is skipped.')
            err = err.format(article_title.encode('utf-8'))
            self.debug_message(err)
            return True
        else: return False
    
    def createArticleData(self, article):
        '''
        Create a metadata structure that can be 
        consumed by the Meta XML builder class.
        This takes the form of a list of dictionaries,
        with each dictionary representing a field or set of fields.
        For example: [{'name': 'Abstract', 'data' : 'From the Roman Empire...' }, 
            {'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
            {'name' : 'Author', 'type' : 'person', 'fields' : [
                {'tag' : 'goobi:firstName', 'data' : 'Peter'},
                {'tag' : 'goobi:lastName', 'data' : 'Turchin'}
            ]}
        ]
        See the MetaXml class for more details.
        '''
        content = list()
        #=======================================================================
        # Set language
        #=======================================================================
        content.append({'name': 'DocLanguage', 'data':article.language})
        #=======================================================================
        # Add title
        #=======================================================================
        if article.article_id:
            content.append({'name': 'dbcMarcxID', 'data':article.article_id})
        #=======================================================================
        # Add title, update time and sub title
        #=======================================================================
        content.append({'name': 'TitleDocMain', 'data':article.title})
        if article.update_time:
            content.append({'name': 'UpdateTime', 'data':article.update_time})
        
        if article.sub_title:
            content.append({'name': 'TitleDocSub1', 'data':article.sub_title})
        #=======================================================================
        # Add subjects
        #=======================================================================
        for subject in article.subjects:
            content.append({'name': 'Subject', 'data':subject})
        #=======================================================================
        # Add description and content description
        #=======================================================================
        if article.description:
            content.append({'name': 'Description', 'data':article.description})
        if article.content_description:
            content.append({'name': 'ContentDescription', 'data':article.content_description})
            
        #=======================================================================
        # Add start and endpage
        #=======================================================================
        start_page = article.start_page
        # legr: subtracted 1 from end_page to avoid duplicate when pages are "uncounted"
        # legr: When uncounted gets fixed, we need to test if this still apply.
        end_page = article.end_page - 1
        #=======================================================================
        # Add authors
        #=======================================================================
        if article.authors: # multiple authors or author from dbc-data
            for author in article.authors:
                given_name = author[0]
                family_name  = author[1]
                author_element = self.__createAuthorElement(given_name, family_name)
                if author_element: content.append(author_element)
        elif article.author:
            if len(article.author.split(' ')) > 1: # multiple names
                given_name, family_name = article.author.split(' ',1) 
            else:
                given_name = article.author 
                family_name = ''
            author_element = self.__createAuthorElement(given_name, family_name)
            if author_element: content.append(author_element)
        else:
            given_name = ''
            family_name = ''
            author_element = self.__createAuthorElement(given_name, family_name)
            if author_element: content.append(author_element)
            # TODO: Do check on the numbers of author names. If very long
            # raise a note to quality control. This is a larger implementation.
            # An example of a long author field:
            #    "Else Marie Pedersen i samarbejde med I�rn Pi� og Holger Rasmussen"
        # create elements for any other authors
        # TODO: routine to split up author field - e.g. use ';' to separate
        # authors.
        #=======================================================================
        # Add issn if it isnt set. ISSN lives in the metadata for the issue
        # but comes from articles in DBCs metadata. Thus we give the issue 
        # the ISSN from the article, if it isn't previously set. 
        #=======================================================================
        if not self.issnSet and article.issn:
            self.addIssnToPeriodical(article.issn)
        
        #=======================================================================
        # Join article element to be added to mets-file 
        #=======================================================================
        article_data = {'doc_type': 'Article',
                        'content': content,
                        'start_page': start_page,
                        'end_page': end_page}
        return article_data

    def __createAuthorElement(self, firstname, lastname):
        '''
        Given a firstname and a lastname, create 
        a list of dictionaries representing a single author
        in the following form:
        [{'tag' : 'firstName', 'data' : 'Peter'},
        {'tag' : 'lastName', 'data' : 'Turchin'}]
        If firstname and lastName are empty, it will return
        an empty hash
        '''
        author = dict()
        author['name'] = 'Author'
        author['type'] = 'person'
        author_fields = list()
        if firstname:
            firstname_elem = dict()
            firstname_elem['tag'] = 'firstName'
            firstname_elem['data'] = firstname
            author_fields.append(firstname_elem)
        if lastname:
            lastname_elem = dict()
            lastname_elem['tag'] = 'lastName'
            lastname_elem['data'] = lastname
            author_fields.append(lastname_elem)
        # build the best display name we can, given the 
        # data available to us
        display_name = dict()
        display_name['tag'] = 'displayName'
        if firstname and lastname:
            display_name['data'] = u"{0}, {1}".format(lastname, firstname)
            author_fields.append(display_name)
        elif lastname:
            display_name['data'] = lastname
            author_fields.append(display_name)
        elif firstname:
            display_name['data'] = firstname
            author_fields.append(display_name)

        if author_fields:
            author['fields'] = author_fields
            return author
        else:
            return None


if __name__ == '__main__':
    
    AddArticlesToMetsFile( ).begin()
