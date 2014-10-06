#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 28/04/2014

@author: jeel
'''
import os
from tools import tools
from goobi.goobi_step import Step

class create_process_folder_structure( Step ) :

    def setup(self):
    
        self.name = "Create complete folder structure"
        self.config_main_section = "create_process_folder_structure"
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            "process_path":"folder"
        }
    
    def step(self):
        
        try:
            self.setVariables()
            tools.check_folder(self.process_path)
            self.createFolders(self.process_path,
                               self.folder_structure.items())
        except Exception as e:
            error = str(e)
            self.error_message(error)
            raise e
    
    def setVariables(self):
        self.folder_structure = self.getConfigSection(self.folder_structure_section)
        self.process_path = self.command_line.process_path
                
    def createFolders(self,root,folderStructure):
        '''
        root is where the folder structure shall be created
        folderStructure is a list of tuples of names and relative paths, e.g.
            [("doc_pdf_path","documents/pdf/"),
            ("doc_invalid_path","documents/invalid/")]
        The relative paths will be created in root and the names will be printed
        as debug info with logger
        '''
        for name,rel_path in folderStructure:
            path = os.path.join(root,rel_path)
            if not os.path.exists(path):
                tools.find_or_create_dir(path)
                self.debug_message('Created {0}'.format(path))
            else:
                self.debug_message('{0} already exists as {1}.'.format(name,path))
if __name__ == '__main__' :
    create_process_folder_structure().begin()