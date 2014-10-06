#!/usr/bin/env python
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
            'process_path' : 'folder',
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
        
        # join paths to create absolute paths on limb-server
        self.limb_dir = os.path.join(limb, process_title)
        self.alto_dir = os.path.join(self.limb_dir, alto)
        self.toc_dir = os.path.join(self.limb_dir, toc)
        self.pdf_input_dir = os.path.join(self.limb_dir, pdf)
        
        # get paths for output folder on goobi-server
        self.goobi_altos = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_alto_path', None, 'process_folder_structure'))
        self.goobi_toc = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_toc_path', None, 'process_folder_structure'))
        self.goobi_pdf = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_limbpdf_path', None, 'process_folder_structure'))
        
        # Set flag for ignore if files already have been copied
        if (self.command_line.has('ignore_dest') and 
            self.command_line.ignore_dest.lower() == True):
            self.ignore_dest = True
        else:
            self.ignore_dest = False
        
        # Get path for input-files in process folder
        process_path = self.command_line.process_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files_dir = os.path.join(process_path,input_files)
        
        # throw Error if one of our directories is missing
        
    
    def step(self):
        '''
        This class checks the output from a LIMB process
        to see if it matches certain criteria
        Require params process_title from command line
        Other values taken from config.ini
        In the case of errors a message will be returned
        and sent to the previous step.
        '''
        error = None
        try:
            self.getVariables()
            # Check files on goobi-server, if they already have been moved
            if (not self.ignore_dest and 
                limb_tools.alreadyMoved(self.goobi_toc,self.goobi_pdf,
                                        self.input_files_dir,self.goobi_altos)):
                return error
            tools.ensureDirsExist(self.limb_dir, self.alto_dir,
                                  self.toc_dir, self.pdf_input_dir,
                                  self.input_files_dir)
            limb_tools.performValidations(self.toc_dir,self.pdf_input_dir,
                                          self.input_files_dir,self.alto_dir)
            return None
        except IOError as e:
            return "IOError - {0}".format(e.strerror)
        except DataError as e: 
            return "Validation error - {0}.".format(e.strerror)
        
if __name__ == '__main__':
    
    ValidateLimbOutput().begin()