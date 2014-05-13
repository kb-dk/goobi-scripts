#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step

from tools import tools
from tools.errors import DataError
import tools.limb as limb_tools
import os
class ValidateLimbOutput( Step ):

    def setup(self):
        self.name = 'ValidateLimbOutput'
        self.config_main_section = 'limb_output'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            'process_title' : 'string',
            'process_root_path' : 'folder',
            'auto_report_problem' : 'string',
            'step_id' : 'string'
        }
    
    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        process_title = self.command_line.process_title
        limb = self.getConfigItem('limb_output')
        alto = self.getConfigItem('alto')
        toc = self.getConfigItem('toc')
        pdf = self.getConfigItem('pdf')
        
        
        # join paths to create absolute paths
        self.limb_dir = os.path.join(limb, process_title)
        self.alto_dir = os.path.join(self.limb_dir, alto)
        self.toc_dir = os.path.join(self.limb_dir, toc)
        self.pdf_dir = os.path.join(self.limb_dir, pdf)
        
        # Get path for input-files in process folder
        process_path = self.command_line.process_root_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files_dir = os.path.join(process_path,input_files)
        
        # throw Error if one of our directories is missing
        tools.ensureDirsExist(self.limb_dir, self.alto_dir, \
            self.toc_dir, self.pdf_dir, self.input_files_dir)
    
    def step(self):
        '''
        This class checks the output from a LIMB process
        to see if it matches certain criteria
        Require params process_title from command line
        Other values taken from config.ini
        In the case of errors a message will be returned
        and sent to the previous step.
        '''
        try:
            self.getVariables()
            self.performValidations()
            return None
        except IOError as e:
            return "IOError - {0}".format(e.strerror)
        except DataError as e: 
            return "Validation error - {0}.".format(e.strerror)
    
    def performValidations(self):
        '''
        1: validering af pdf (antal sider i pdf == antal input billeder)
        2: validering af toc-fil (pt. er der en fil - validering ved parsing efterfoelgende)
        3: validering af alto-filer (evt. "er der lige saa mange som input billeder" eller "er der filer")
        
        Throw DataError if any validation fails
        '''
        if not limb_tools.tocExists(self.toc_dir): 
            raise DataError("TOC not found!")
        if not self.pageCountMatches():
            raise DataError("PDF page count does not match input picture count!")
        if not limb_tools.altoFileCountMatches(self.alto_dir, self.input_files_dir):
            raise DataError("Number of alto files does not match number of input files.")
        #self.info_message("All validations performed successfully.")
        

    def pageCountMatches(self):
        '''
        Compare num pages in pdfinfo with pages in input 
        picture directory. 
        return boolean 
        '''
        msg = ('Comparing page count with input files')
        self.debug_message(msg)
        pdf = tools.getFirstFileWithExtension(self.pdf_dir, '.pdf')
        pdfInfo = tools.pdfinfo(os.path.join(self.pdf_dir, pdf))
        numPages = int(pdfInfo['Pages'])
        numInputFiles = len(os.listdir(self.input_files_dir))
        return numPages == numInputFiles

if __name__ == '__main__':
    
    ValidateLimbOutput().begin()