#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools import errors
from tools.filesystem import fs
import tools.limb as limb_tools



class CopyToWebServer( Step ):

    def setup(self):
        self.name = "Kopiering af PDF'er til public webserver"
        self.config_main_section = 'copy_to_webserver'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section] )
        self.essential_commandlines = {
            "process_id" : "number",
            "process_path" : "folder"
        }


    def getVariables(self):
        '''
        Get all required vars from command line + config
        '''
        # source folders for color and bw pdfs
        process_path = self.command_line.process_path
        color = self.getConfigItem('doc_pdf_color_path', section= self.folder_structure_section) 
        self.source_folder_color = os.path.join(process_path,color)
        black = self.getConfigItem('doc_pdf_bw_path', section= self.folder_structure_section) 
        self.source_folder_bw = os.path.join(process_path,black)
        # destination folder on public webserver
        self.dest_folder = self.getConfigItem('webserver_path')
        # retry variables
        self.retry_wait = int(self.getConfigItem('retry_wait'))
        self.retry_num = int(self.getConfigItem('retry_num'))
        #self.apache_owner = self.getSetting('apache_owner',var_type=int)

    def step(self):
        '''
        Copy PDF's from Goobi to webserver
        ''' 
        error = None   
        try:
            self.getVariables()
            tools.ensureDirsExist(self.source_folder_color, self.source_folder_bw)
            self.copyFiles(self.source_folder_color, self.dest_folder)
            self.copyFiles(self.source_folder_bw, self.dest_folder)
        except ValueError as e:
            return e.strerror
            #return "Could not convert string to int - check config file."
        except (TransferError, TransferTimedOut, IOError) as e:
            return e.strerror
        return None


    def copyFiles(self, source_dir, dest_dir):
        '''
        Wrapper around tools method
        Throws TransferError, TransferTimedOut
        '''
        tools.copy_files(source = source_dir,
                         dest = dest_dir,
                         transit = None,
                         delete_original = False,
                         wait_interval = self.retry_wait,
                         max_retries = self.retry_num,
                         logger = self.glogger)

if __name__ == '__main__':    
    CopyToWebServer().begin()