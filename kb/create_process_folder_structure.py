#!/usr/bin/python
'''
Created on 28/04/2014

@author: jeel
'''
import os
import sys
import tools

from goobi.goobi_step import Step

class create_process_folder_structure( Step ) :

    def setup(self):
    
        self.name = "Create complete folder structure"
        self.config_main_section = "create_process_folder_structure"
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        
    
    def step(self):
        folder_structure = self.config.config.items(
                                self.folder_structure_section)
        process_root_path = self.command_line.process_root_path
        error = tools.check_folder(process_root_path)
        if error:
            self.error(error)
            sys.exit(1)
        for name,rel_path in folder_structure:
            path = os.path.join(process_root_path,rel_path)
            if not os.path.exists(path):
                created,error = tools.find_or_create_dir(path)
                if not created:
                    self.error(error)
                    return error
                else:
                    self.debug_message('Created {0}'.format(path))
            else:
                self.debug_message('{0} already exists as {1}.'.format(name,path))
    
if __name__ == '__main__' :
    create_process_folder_structure().begin()