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



class CountImageFiles( Step ):

    def setup(self):
        self.name = 'Find antal billeder og skriv resultat i Goobi'
        self.config_main_section = 'count_image_files'
        self.valid_exts_section = 'valid_file_exts'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            "process_path" : "folder",
            "process_id" : "number",
        }


    def step(self):
        error = None
        try:
            #===================================================================
            # Set/get variables
            #===================================================================
            self.getVariables()
            #===================================================================
            # count the number of valid images
            #===================================================================
            number_of_images = tools.getFileCountWithExtension(self.image_path, self.valid_exts)
            #===================================================================
            # write the number of images to the current process in Goobi
            #===================================================================
            sent_correctly = self.goobi_com.addProperty(self.property_name, number_of_images, True)
            if not sent_correctly:
                self.goobi_com.addProperty(self.property_name, number_of_images, True)
        except ValueError as e: # not sure which exceptions expectedly would occur here
            error = str(e.with_traceback)
        return error


    def getVariables(self):
        #=======================================================================
        # # Get process root folder from command line
        #=======================================================================
        process_path = self.command_line.process_path
        #=======================================================================
        # # Get relative path to images from config.ini
        #=======================================================================
        image_path = self.getConfigItem('img_master_path',
                                        section=self.folder_structure_section)
        #=======================================================================
        # # Build complete path to image files
        #=======================================================================
        self.image_path = os.path.join(process_path, image_path)
        #=======================================================================
        # # Get a list of valid extensions we want to count from config.ini
        #=======================================================================
        v_exts = self.getConfigItem('valid_file_exts', 
                                    section=self.valid_exts_section)
        self.valid_exts = v_exts.split(';')
        #=======================================================================
        # # Get the property name we have defined in goobi_processProperties.xml from config.in
        #=======================================================================
        self.property_name = self.getConfigItem('property_name')


if __name__ == '__main__':
    CountImageFiles( ).begin()