#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools.errors import DataError, TransferError, TransferTimedOut

class MoveToGoobi( Step ):

    def setup(self):
        self.name = 'Move to Goobi'
        self.config_main_section = 'limb_output'
        self.essential_commandlines = {
            "process_id" : "number",
            "process_path" : "folder",
            "process_title" : "string",
            'auto_report_problem' : 'string',
            'step_id' : 'number'
        }

    def step(self):
        '''
        Move altos, toc, pdf from limb to goobi
        '''    
        try:
            self.getVariables()
            self.moveFiles(self.limb_altos, self.goobi_altos)
            self.moveFiles(self.limb_toc, self.goobi_toc)
            self.moveFiles(self.limb_pdf, self.goobi_pdf)
        except ValueError:
            return "Could not convert string to int - check config file."
        except (TransferError, TransferTimedOut, IOError) as e:
            return e.strerror

        return None


    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        Throws ValueError if config strings cannot be converted to input_files
        Throws IOError if necessary directories could not be found
        '''
        limb_process_root = os.path.join(self.getConfigItem('limb_output'), self.command_line.process_title)
        self.limb_altos = os.path.join(limb_process_root, self.getConfigItem('alto'))
        self.limb_toc = os.path.join(limb_process_root, self.getConfigItem('toc'))
        self.limb_pdf = os.path.join(limb_process_root, self.getConfigItem('pdf'))
                
        self.goobi_altos = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_alto_path', None, 'process_folder_structure'))
        self.goobi_toc = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_toc_path', None, 'process_folder_structure'))
        self.goobi_pdf = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_pdf_path', None, 'process_folder_structure'))
        
        self.sleep_interval = int(self.getConfigItem('sleep_interval', None, 'copy_to_limb'))
        self.retries = int(self.getConfigItem('retries', None, 'copy_to_limb'))
        

        tools.ensureDirsExist(self.limb_altos, self.limb_toc, self.limb_pdf)
        tools.ensureDirsExist(self.goobi_altos, self.goobi_toc, self.goobi_pdf)

    def moveFiles(self, source_dir, dest_dir):
        '''
        Wrapper around tools method
        Throws TransferError, TransferTimedOut
        '''
        tools.copy_files(source = source_dir,
                             dest = dest_dir,
                             transit = None,
                             delete_original = True,
                             wait_interval = self.sleep_interval,
                             max_retries = self.retries,
                             logger = self.glogger,
                             debug = True)

if __name__ == '__main__':    
    MoveToGoobi().begin()