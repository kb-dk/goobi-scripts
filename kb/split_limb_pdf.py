#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step

from tools import tools as tools
from tools import errors
from tools.mets import mets_tools
import os
from xml.dom import minidom

class SplitPdf( Step ):

    def setup(self):
        self.config_main_section = 'split_pdf_file'
        self.folder_structure_section = 'process_folder_structure'
        self.process_files_section = 'process_files'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.process_files_section] )
        self.essential_commandlines = {
            'process_path' : 'folder',
        }

    def step(self):
        '''
        Splits a pdf file according to a toc file
        1. set necessary variables
        2. get data from toc file
        2.1. get data from pdf file
        3. cut up pdf file
        4. profit!
        '''
        try:
            self.getVariables()
            self.getPdf()
            self.getArticles()
            self.dividePdf()
            return None
        except ValueError as e:
            return e
        except (IOError, errors.PdftkError) as e:
            #"Execution halted due to error {0}".format()
            return e.strerror

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        process_path = self.command_line.process_path
        mets_file_name = self.getConfigItem('metadata_goobi_file', None, self.process_files_section)
        self.mets_file = os.path.join(process_path, mets_file_name)
        
        process_path = self.command_line.process_path
        pdf_input = self.getConfigItem('doc_limbpdf_path',
                                       section= self.folder_structure_section)
        pdf_output = self.getConfigItem('doc_pdf_path',
                                        section= self.folder_structure_section)

        # Create paths for 
        self.pdf_input_dir = os.path.join(process_path, pdf_input)
        self.pdf_output_dir = os.path.join(process_path,pdf_output)
        # raises exception if one of our directories is missing
        tools.ensureDirsExist(self.pdf_input_dir,self.pdf_output_dir)
        tools.ensureFilesExist(self.mets_file)
    
    def getPdf(self):
        self.pdf_name = tools.getFirstFileWithExtension(self.pdf_input_dir, '.pdf')
        self.pdf_path = os.path.join(self.pdf_input_dir, self.pdf_name)
        self.pdfinfo = tools.pdfinfo(self.pdf_path)
    
    def getArticles(self):
        data = minidom.parse(self.mets_file)
        self.article_data = mets_tools.getArticleData(data,['FrontMatter','Articles','BackMatter'])

    def dividePdf(self):
        ''' 
        Cut up the volume into articles pdfs based on the data in the LIMB toc
        '''
        for _,articles in self.article_data.items():
            for article in articles:
                hash_name = tools.getHashName(article['TitleDocMain'])
                start_page = article['start_page'] 
                end_page = article['end_page']
                output_name = tools.getArticleName(hash_name, start_page,end_page)
                output_path = os.path.join(self.pdf_output_dir, output_name)
                self.debug_message("creating file {0}".format(output_path))
                # if our call to pdftk fails, get out quickly
                if not tools.cutPdf(self.pdf_path,  output_path, start_page, end_page):
                    error = ('PDF division failed. Input file: {0}, '
                             'start page: {1}, end page: {2}')
                    error = error.format(self.pdf_path,start_page,end_page)
                    raise IOError(error)
        return None

    def profit(self):
        ''' ChaChing! '''

if __name__ == '__main__':
    
    SplitPdf( ).begin()
