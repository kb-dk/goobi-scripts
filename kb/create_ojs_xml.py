#!/usr/bin/env python
# -*- coding: utf-8 -*-
from goobi.goobi_step import Step
from xml.dom import minidom
from tools.errors import DataError, InputError
from tools.mets import mets_tools
from tools import tools
import os, time
import traceback

class CreateOJSXML( Step ):

    def setup(self):
        self.name = 'Oprettelse af OJS XML-filer til www.tidsskrift.dk'
        self.config_main_section = 'ojs'
        self.essential_config_sections = set( ['ojs',
                                               'process_folder_structure',
                                               'process_files'] )
        self.essential_commandlines = {
            'process_id' : 'number',
            'process_title' : 'string',
            'process_path' : 'folder',
            'step_id' : 'number'
        }

    def step(self):
        try:
            self.getVariables()
            self.createXML()
        except OSError as e:
            return e.strerror + " " + e.filename
        except (DataError, IOError, InputError) as e:
            self.debug_message(str(e))
            return e.strerror
        except Exception as e:
            self.debug_message(str(e))
            print(str(traceback.format_exc()))
            raise e
        # if we got here everything is fine
        return None

    def getVariables(self):
        '''
        Ensure we have the variables necessary to execute the script
        Tools will throw an Exception otherwise
        '''
        process_path = self.command_line.process_path
        mets_file_name = self.getConfigItem('metadata_goobi_file', None, 'process_files')
        self.mets_file = os.path.join(process_path, mets_file_name)
        
        self.ojs_root = self.getConfigItem('ojs_root')
        ojs_metadata_dir = self.getConfigItem('metadata_ojs_path', None, 'process_folder_structure')
        self.ojs_metadata_dir = os.path.join(process_path, ojs_metadata_dir)

        pdf_path = self.getConfigItem('doc_limbpdf_path', None, 'process_folder_structure')
        abs_pdf_path = os.path.join(process_path, pdf_path)
        self.pdf_name = tools.getFirstFileWithExtension(abs_pdf_path, '.pdf')
        self.pdf_file = os.path.join(abs_pdf_path, self.pdf_name)
        # TODO: check files in 'doc_pdf_path' instead of 'doc_limbpdf_path'
        # 'doc_limbpdf_path' contains the splitted pdf-files
        tools.ensureFilesExist(self.mets_file)
        tools.ensureDirsExist(self.ojs_metadata_dir)
        
        # parse boolean from command line
        self.overlapping_articles = self.getSetting('overlapping_articles', bool, default=True)

        # we also need the required issue fields
        req_fields = self.getConfigItem('issue_required_fields')
        self.issue_required_fields = req_fields.split(';')
        opt_fields = self.getConfigItem('issue_optional_fields')
        self.issue_optional_fields = opt_fields.split(';')
        
        # Set namespaces
        self.mets_ns = 'http://www.loc.gov/METS/'
        self.goobi_ns = 'http://meta.goobi.org/v1.5.1/'
        # Set sections
        self.front_matter = []
        self.articles = []
        self.back_matter = []
        

    def createXML(self):
        '''
        Get the data from the issue file and the toc
        Use this to construct the OJS XML
        '''
        data = minidom.parse(self.mets_file)
        issue_data = mets_tools.getIssueData(self.mets_file)
        article_data = mets_tools.getArticleData(data,['FrontMatter','Articles','BackMatter'])
        # this is the dir where files will be uploaded to
        journal_title_path = tools.parseTitle(issue_data['TitleDocMain'])
        self.ojs_dir = os.path.join(self.ojs_root,journal_title_path, self.command_line.process_title)
        #=======================================================================
        # Get and validate PublicationYear
        # I.e. s only four digits and starts with 17,18,19 or 20
        #=======================================================================
        err = ('Publiceringsåret ("{0}") for hæftet skal være et firecifret tal '
               'begyndende med enten 17, 18, 19 eller 20, f.eks. 1814, 1945 '
               'eller 2001.  {1}. Åben metadata-editor og ret metadata for '
               'hæftet og afslut opgaven.')
        pub_year = issue_data['PublicationYear']
        pub_year = pub_year.strip() # Remove leading and trailing spaces.
        if not pub_year.isdigit():
            raise Exception(pub_year,err.format('Data er ikke et korrekt firecifret tal'))
        if not len(pub_year) == 4:
            raise Exception(pub_year,err.format('Tallet er ikke præcis fire cifre langt'))
        if not int(int(pub_year)/100) in [17,18,19,20]:
            raise Exception(pub_year,err.format('Tallet starter ikke med 17, 18, 19 eller 20'))
        date_published = "{0}-01-01".format(pub_year)
        #=======================================================================
        # Create base xml for issue
        #=======================================================================
        impl = minidom.getDOMImplementation()
        doc = impl.createDocument(None, "issue", None)
        doc = self.createHeadMaterial(doc, issue_data)
        # Get data for articles in the sections front matter, articles and back matter
        if article_data['FrontMatter']:
            front_section = self.createFrontSectionXML(doc, issue_data)
            front_section = self.createArticlesForSection(article_data['FrontMatter'],
                                                          front_section,
                                                          doc,
                                                          date_published)
            doc.documentElement.appendChild(front_section)
        if article_data['Articles']:
            article_section = self.createArticleSectionXML(doc, issue_data)
            article_section = self.createArticlesForSection(article_data['Articles'],
                                                            article_section,
                                                            doc,
                                                            date_published)
            doc.documentElement.appendChild(article_section)
            
        if article_data['BackMatter']:
            back_section = self.createBackSectionXML(doc, issue_data)
            back_section = self.createArticlesForSection(article_data['BackMatter'],
                                                         back_section,
                                                         doc,
                                                         date_published)
            doc.documentElement.appendChild(back_section)

        # save the xml content to the correct file
        output_name = os.path.join(self.ojs_metadata_dir, self.command_line.process_title + '.xml')
        output = open(output_name, 'w')
        output.write(doc.toxml())#'utf-8'))
    
    
    def createArticlesForSection(self, articles, section_tag, doc, date):
        for art in articles:
            art = self.__translateArticleTitles(art)
            article = self.createArticleXML(doc, art, date)
            section_tag.appendChild(article)
        return section_tag    

    def createSectionXML(self, doc, issue_data, title, abbrev):
        section = doc.createElement('section')
        section_title_tag = self.createXMLTextTag(doc, 'title', title)
        abbrev_tag = self.createXMLTextTag(doc, 'abbrev', abbrev)
        locale = tools.convertLangToLocale(issue_data['DocLanguage'])
        abbrev_tag.setAttribute('locale', locale)
        section.appendChild(section_title_tag)
        section.appendChild(abbrev_tag)
        
        return section

    def createFrontSectionXML(self, doc, issue_data):
        return self.createSectionXML(doc, issue_data, 'Indledning', 'IND')

    def createArticleSectionXML(self, doc, issue_data):
        return self.createSectionXML(doc, issue_data, 'Artikler', 'ART')

    def createBackSectionXML(self, doc, issue_data):
        return self.createSectionXML(doc, issue_data, 'Diverse', 'DIV')
        
    def createArticleXML(self, doc, article, date_published):
        '''
        Given an article dict, create the OJS XML
        corresponding to this data
        '''
        #=======================================================================
        # Create article stub with title
        #=======================================================================
        article_tag = doc.createElement('article')
        doc_language = tools.convertLangToLocale(article['DocLanguage'])
        article_tag.setAttribute('locale',doc_language)
        article_tag.setAttribute('language',article['DocLanguage'])
        title_tag = self.createXMLTextTag(doc, 'title', article['TitleDocMain'])
        article_tag.appendChild(title_tag)
        #=======================================================================
        # Add DBC-id to article
        #=======================================================================
        dbc_id_tag = doc.createElement('id')
        dbc_id_tag.setAttribute('type','dbcMarcxID')
        if 'dbcMarcxID' in article:
            dbc_id_tag.createTextNode(article['dbcMarcxID'])
        article_tag.appendChild(dbc_id_tag)
        #=======================================================================
        # Add page range
        #=======================================================================
        start_page,end_page = article['start_page'], article['end_page']
        page_range = "{0}-{1}".format(start_page,end_page)
        pages_tag = self.createXMLTextTag(doc, 'pages', page_range) # TODO fix this to use range
        article_tag.appendChild(pages_tag)
        #=======================================================================
        # Add date published tag
        #=======================================================================
        published_tag = self.createXMLTextTag(doc, 'date_published', date_published) 
        article_tag.appendChild(published_tag)
        #=======================================================================
        # Add authors
        #=======================================================================
        # don't add an author tag if we don't have one (e.g. Front Matter)
        if 'Author' in article: #Author is a list of zero, one or multuple authors
            for author in article['Author']:
                author_tag = self.createAuthorXML(doc, author)
                article_tag.appendChild(author_tag)
        #=======================================================================
        # Add subjects
        # see http://pkp.sfu.ca/wiki/index.php/Importing_and_Exporting_Data#Creating_the_XML_Import_File
        #=======================================================================
        if 'Subject' in article: #Author is a list of zero, one or multuple authors
            indexing_tag = doc.createElement('indexing')
            subjects = ''
            if isinstance(article['Subject'],list):
                subjects = ';'.join(article['Subject'])
            else:
                subjects = article['Subject']
            subject_tag = self.createXMLTextTag(doc,'subject',subjects) 
            subject_tag.setAttribute('locale',tools.convertLangToLocale('da'))
            indexing_tag.appendChild(subject_tag)
            article_tag.appendChild(indexing_tag)
        #=======================================================================
        # Add pdf-link
        #=======================================================================
        md5_hash = tools.getHashName(article['TitleDocMain'])
        pdf_name = tools.getArticleName(md5_hash, start_page,end_page)
        galley_tag = self.createGalleyXML(doc, pdf_name)
        article_tag.appendChild(galley_tag)
        return article_tag
       

    def createGalleyXML(self, doc, pdf_name):
        galley_tag = doc.createElement('galley')
        label_tag = self.createXMLTextTag(doc, 'label', 'PDF')
        galley_tag.appendChild(label_tag)

        file_tag = doc.createElement('file')
        link_tag = doc.createElement('href')
        link_tag.setAttribute('mime_type', 'application/pdf')
        article_link = os.path.join(self.ojs_dir, pdf_name)
        link_tag.setAttribute('src', article_link)
        file_tag.appendChild(link_tag)
        galley_tag.appendChild(file_tag)
        return galley_tag


    def createAuthorXML(self, doc, author):
        ''' 
        Create OJS Author tag based on name string
        Firstname is first word in string
        Lastname is last word in string 
        Middlename is anything in between or CDATA
        '''

        author_tag = doc.createElement('author')
    
        # only create a firstname if there's more than one name
        if 'firstName' in author:
            firstname_tag = self.createXMLTextTag(doc, 'firstname', author['firstName'])
        else:
            firstname_tag = self.createEmptyElement(doc, 'firstname')

        if 'lastName' in author:
            lastname_tag = self.createXMLTextTag(doc, 'lastname', author['lastName'])
        else:
            lastname_tag = self.createEmptyElement(doc, 'lastname')

        email_tag = self.createEmptyElement(doc, 'email')
        
        author_tag.appendChild(firstname_tag)
        author_tag.appendChild(lastname_tag)
        author_tag.appendChild(email_tag)

        return author_tag


    def createEmptyElement(self, doc, name):
        tag = doc.createElement(name)
        cdata = doc.createCDATASection(' ')
        tag.appendChild(cdata)

        return tag

    def createHeadMaterial(self, doc, issue_data):
        '''
        Create and append all the OJS XML Header data
        to XML Document doc based on the data in mets file
        '''
        top = doc.documentElement

        top.setAttribute('current', 'false')
        top.setAttribute('published', 'true')
        
        top.setAttribute('identification', 'num_vol_year')
        
        
        title_tag = self.createXMLTextTag(doc, 'title', issue_data['TitleDocMain'])
        top.appendChild(title_tag)
        
        year_tag = self.createXMLTextTag(doc, 'year', issue_data['PublicationYear'])
        top.appendChild(year_tag)
        
        volume_tag = self.createXMLTextTag(doc, 'volume', issue_data['VolumeNumber'])
        top.appendChild(volume_tag)

        number_tag = self.createXMLTextTag(doc, 'number', issue_data['IssueNumber'])
        top.appendChild(number_tag)

        access_tag = self.createXMLTextTag(doc, 'access_date', time.strftime("%Y-%m-%d"))
        top.appendChild(access_tag)

        # we just say that it's the first of the year - we don't know the real date
        date_published = "{0}-01-01".format(issue_data['PublicationYear'])
        date_tag = self.createXMLTextTag(doc, 'date_published', date_published)
        top.appendChild(date_tag)

        return doc


    def createXMLTextTag(self, doc, tag_name, tag_val):
        '''
        Convenience function to return xml text tag
        with simple form <tag_name>tag_val</tag_name>
        Note - this function does not append the tag to your
        doc - you will need to this this with Element.appendChild(tag) 
        '''
        tag = doc.createElement(tag_name)
        text = doc.createTextNode(tag_val)
        tag.appendChild(text)
        return tag


    
    
    def __translateArticleTitles(self, article):
        if article['TitleDocMain'] == 'FrontMatter': article['TitleDocMain'] = 'Indledning'
        elif article['TitleDocMain'] == 'Back Matter': article['TitleDocMain'] = 'Diverse'

        return article

if __name__ == '__main__':
    
    CreateOJSXML( ).begin()
