#!/usr/bin/python
'''
Created on 28/04/2014

@author: jeel
'''
import os

from goobi.goobi_step import Step

class create_process_folder_structure( Step ) :

    def setup(self):
    
        self.name = "Create complete folder structure"
        self.config_main_section = "create_process_folder_structure"
    
    def step(self):
        pass
        
if __name__ == '__main__' :
    create_process_folder_structure().begin()