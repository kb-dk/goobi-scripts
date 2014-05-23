#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step

from tools import tools as tools
from tools import errors
from tools.toc import TOC
import os

class SplitPdf( Step ):

    def setup(self):
        self.config_main_section = 'split_pdf_file'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            'process_path' : 'folder',
            'overlapping_articles' : 'string'
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
            self.getToc()
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
        # parse boolean from command line
        if self.command_line.overlapping_articles.lower() == 'true':
            self.overlapping_articles = True
        elif self.command_line.overlapping_articles.lower() == 'false':
            self.overlapping_articles = False
        else:
            error = ('Invalid value {0} given for overlapping_articles '
                    'argument.')
            error = error.format(self.command_line.overlapping_articles)
            raise ValueError(error)
        
        process_path = self.command_line.process_path
        pdf_input = self.getConfigItem('doc_limbpdf_path',
                                       section= self.folder_structure_section)
        pdf_output = self.getConfigItem('doc_pdf_path',
                                        section= self.folder_structure_section)
        toc = self.getConfigItem('metadata_toc_path',
                                 section= self.folder_structure_section)
        # Create paths for 
        self.pdf_input_dir = os.path.join(process_path, pdf_input)
        self.pdf_output_dir = os.path.join(process_path,pdf_output)
        self.toc_dir = os.path.join(process_path, toc)
        # raises exception if one of our directories is missing
        tools.ensureDirsExist(self.toc_dir,
                              self.pdf_input_dir,
                              self.pdf_output_dir)
    
    def getPdf(self):
        self.pdf_name = tools.getFirstFileWithExtension(self.pdf_input_dir, '.pdf')
        self.pdf_path = os.path.join(self.pdf_input_dir, self.pdf_name)
        self.pdfinfo = tools.pdfinfo(self.pdf_path)
    
    def getToc(self):
        toc = tools.getFirstFileWithExtension(self.toc_dir, '.toc')
        self.toc_data = TOC(os.path.join(self.toc_dir, toc))
        self.toc_data.addEndPageInfo(self.pdfinfo,self.overlapping_articles)

    def dividePdf(self):
        ''' 
        Cut up the volume into articles pdfs based on the data in the LIMB toc
        '''
        for article in self.toc_data.allArticles():
            output_name = tools.getArticleName(self.pdf_name, article.number)
            output_path = os.path.join(self.pdf_output_dir, output_name)
            self.debug_message("creating file {0}".format(output_path))
            # if our call to pdftk fails, get out quickly
            if not tools.cutPdf(self.pdf_path,  output_path, article.start_page, article.end_page):
                error = ('PDF division failed. Input file: {0}, '
                         'start page: {1}, end page: {2}')
                error = error.format(self.pdf_path,
                                     article.start_page,
                                     article.end_page)
                raise IOError(error)
        return None

    def profit(self):
        ''' ChaChing! '''

if __name__ == '__main__':
    
    SplitPdf( ).begin()
