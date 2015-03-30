#!/usr/bin/env python
# -*- coding: utf-8

from goobi.goobi_step import Step
import os
import tools.tools as tools
import tools.goobi.metadata as goobi_tools
from tools.mets import mets_tools
from tools.errors import DataError
from tools import ojs

class UploadToOJS( Step ):

    def setup(self):
        self.name = 'Upload PDF-filer og XML-fil til OJS'
        self.config_main_section = 'ojs'
        self.folder_structure_section = 'process_folder_structure'
        self.process_files_section = 'process_files'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.process_files_section]
                                               )
        
        self.essential_commandlines = {
            'process_id' : 'number',
            'process_path' : 'folder',
            'process_title' : 'string',
            'issn' : 'string'
        }

    def step(self):
        '''
        Transfer article pdfs and OJS xml
        to the relevant folder on the OJS server
        '''
        try:
            self.getVariables()
            self.transferPDFs()
            self.transferXML()
        except (DataError, OSError) as e:
            print(e)
            return "Execution halted due to error {0}".format(e.strerror)

        return None

    def getVariables(self):
        '''
        This script pulls in all the variables
        from the command line and the config file 
        that are necessary for its running.
        Errors in variables will lead to an 
        Exception being thrown.
        We need the path to the OJS mount,
        the current process dir, the pdf dir,
        and the ojs xml dir.
        '''
        process_path = self.command_line.process_path
        ojs_mount = self.getConfigItem('ojs_mount')
        ojs_metadata_dir = self.getConfigItem('metadata_ojs_path',
                                              section= self.folder_structure_section)
        self.ojs_metadata_dir = os.path.join(process_path, ojs_metadata_dir)
        
        pdf_path = self.getConfigItem('doc_pdf_path',
                                      section= self.folder_structure_section)
        self.pdf_input_dir = os.path.join(process_path, pdf_path)
        
        issn = self.command_line.issn
        ojs_journal_path = ojs.getJournalPath(self.ojs_server, issn)
        ojs_journal_folder = os.path.join(ojs_mount, ojs_journal_path)

        # Create folder and set owner to gid 1000 => ojs-group
        tools.find_or_create_dir(ojs_journal_folder,change_owner=1000)
        self.ojs_dest_dir = os.path.join(ojs_journal_folder,
                                         self.command_line.process_title)
        # Create folder and set owner to gid 1000 => ojs-group
        tools.find_or_create_dir(self.ojs_dest_dir,change_owner=1000)

        tools.ensureDirsExist(self.ojs_metadata_dir,
                              self.pdf_input_dir,
                              self.ojs_dest_dir)

        self.debug_message("metadata_dir is %s" % self.ojs_metadata_dir)
        self.debug_message("pdf_input_dir is %s" % self.pdf_input_dir)
        self.debug_message("dest_dir is %s" % self.ojs_dest_dir)

    def transferPDFs(self):
        tools.copy_files(source = self.pdf_input_dir,
                         dest = self.ojs_dest_dir,
                         transit=None,
                         delete_original=False,
                         wait_interval=60,
                         max_retries=5,
                         logger=self.glogger,
                         change_owner=1000 # set owner to gid 1000 => ojs-group
                         )


    def transferXML(self):
        tools.copy_files(source = self.ojs_metadata_dir,
                         dest = self.ojs_dest_dir,
                         transit=None,
                         delete_original=False,
                         wait_interval=60,
                         max_retries=5,
                         logger=self.glogger,
                         change_owner=1000 # set owner to gid 1000 => ojs-group
                         )

if __name__ == '__main__':
    
    UploadToOJS( ).begin()
