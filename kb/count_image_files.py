#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on 09/12/2014
@author: legr
"""
from goobi.goobi_step import Step
from tools import tools
import os
import time


class CountImageFiles(Step):
    def setup(self):
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

    def step(self):
        error = None
        try:
            self.getVariables()
            # Get the number of valid images
            image_count = tools.getFileCountWithExtension(self.image_path, self.valid_exts)
            self.error_message("Der blev optalt {} billeder".format(image_count))
            # write the number of images to a Goobi property. It sometimes fail, hence the retry stuff
            max_retry = 10
            retry = 0
            ok = False
            while not ok:
                ok = self.goobi_com.addProperty(name=self.property_name, value=image_count, overwrite=True)
                retry += 1
                if not ok:
                    self.error_message("Billedantallet kunne ikke gemmes! Proever igen... (retry={})".format(retry))
                    time.sleep(5)
                    if retry > max_retry:
                        self.error_message("Kunne ikke gemme billedantallet!")
                        return False
            self.error_message("Billedantallet ({}) blev gemt korrekt i forsoeg nr {}".format(image_count, retry))
        # not sure which exceptions to expect...
        except ValueError as e:
            error = str(e.with_traceback)
        return error

if __name__ == '__main__':
    CountImageFiles().begin()