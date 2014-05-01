#!/usr/bin/python
# -*- coding: utf-8
'''
Created on 28/04/2014

@author: jeel
'''
import os
import sys
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
            "process_root_path":"folder"
        }
        
    
    def step(self):
        
        folder_structure = self.getConfigSection(self.folder_structure_section)
        process_root_path = self.command_line.process_root_path
        tools.check_folder(process_root_path)
        for name,rel_path in folder_structure.items():
            path = os.path.join(process_root_path,rel_path)
            if not os.path.exists(path):
                tools.find_or_create_dir(path)
                self.debug_message('Created {0}'.format(path))
            else:
                self.debug_message('{0} already exists as {1}.'.format(name,path))
    
if __name__ == '__main__' :
    create_process_folder_structure().begin()