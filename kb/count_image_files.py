#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 09/12/2014

@author: legr
'''
from goobi.goobi_step import Step
from goobi.goobi_communicate import GoobiCommunicate
from tools import tools
import os



class count_image_files( Step ):

    def setup(self):
        self.name = 'Find antal billeder og skriv resultat i Goobi'
        self.config_main_section = 'count_image_files'
        self.count_image_files_section = 'count_image_files'
        self.valid_exts_section = 'move_invalid_files'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.count_image_files_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            "process_path" : "folder",
            "process_title" : "string", # not used
            "process_id" : "number",
        }


    def step(self):
        error = None
        self.getVariables()
        # count the number of valid images
        number_of_images = tools.getFileCountWithExtension("input_files_dir", self.valid_exts)
        # write the number of images to the current process in Goobi
        GoobiCommunicate.addProperty(self.process_id, self.property_name, number_of_images, True)
        return None


    def getVariables(self):
        # Get process id from command line 
        self.process_id = self.command_line.process_id
        # Get process root folder from command line
        process_path_root_folder = self.command_line.process_path
        # Get relative path to images from config.ini
        relative_image_path = self.getConfigItem('img_master_path', None, self.folder_structure_section)
        # Build complete path to image files
        self.image_path = os.path.join(process_path_root_folder, relative_image_path)
        # Get a list of valid extensions we want to count from config.ini
        self.valid_exts = self.getConfigItem('valid_file_exts', None, self.valid_exts_section).split(';')
        # Get the property name we have defined in goobi_processProperties.xml from config.in
        self.property_name = self.getConfigItem('property_name', None, 'count_image_files')


if __name__ == '__main__':
    count_image_files( ).begin()