#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on 09/12/2014
@author: legr
"""
from goobi.goobi_step import Step
from tools import tools
import os


class CountImageFiles(Step):
    def setup(self, _):
        self.name = 'Find antal billeder og skriv resultat i Goobi'
        self.config_main_section = 'count_image_files'
        self.valid_exts_section = 'valid_file_exts'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, self.valid_exts_section])
        self.essential_commandlines = {"process_path": "folder", "process_id": "number"}

    def getVariables(self):
        # Build path to images - get process path (from command line) and image path (from config.ini)
        self.image_path = os.path.join(self.command_line.process_path,
                                       self.getConfigItem('img_master_path', section=self.folder_structure_section))
        # Get a list of valid extensions (from config.ini)
        self.valid_exts = self.getConfigItem('valid_file_exts', section=self.valid_exts_section).split(";")
        # Get the property name we have defined in goobi_processProperties.xml (from config.ini)
        self.property_name = self.getConfigItem('property_name')

    def step(self, _):
        error = None
        try:
            self.getVariables()
            # count the number of valid images
            number_of_images = tools.getFileCountWithExtension(self.image_path, self.valid_exts)
            # write the number of images to a Goobi property
            if self.goobi_com.addProperty(self.property_name, number_of_images, True):
                self.debug_message("Antal billeder fundet:")
                self.debug_message("Property={}, and image count={}".format(self.property_name, number_of_images))
            else:
                self.debug_message("Advarsel: antal billeder blev muligvis ikke gemt korrekt")
                self.debug_message("Property={}, and image count={}".format(self.property_name, number_of_images))
        # not sure which exceptions to expect...
        except ValueError as e:
            error = str(e.with_traceback)
        return error


if __name__ == '__main__':
    CountImageFiles().begin()