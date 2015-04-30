#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''

from tools import tools
import os
import time
from goobi.goobi_step import Step
import tools.image_tools.convert_folder as convert
from tools.image_tools import misc as image_tools

class CreateThumbnails( Step ) :

    def setup(self):
    
        self.name = "Oprettelse af thumbnails"
        self.config_main_section = "create_thumbnails"
        self.essential_config_sections = set( [] )
        self.folder_structure_section = 'process_folder_structure'
        self.valid_file_exts_section = 'valid_file_exts'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.valid_file_exts_section] )
        self.essential_commandlines = {
            "process_path":"folder",
            "auto_complete":"string"
        }
    
    def step(self):
        """
        legr: create JPEGs from TIFFs
        legr: These JPEGS are for use as thumbnails in Goobi's METS-editor
        """
        error = None
        self.getVariables()
        try:
            t = time.time()
            convert.convertFolder(input_folder    = self.input_folder,
                                  output_folder   = self.output_folder,
                                  quality         = self.quality,
                                  resize_type     = self.resize_type,
                                  resize          = self.resize,
                                  valid_exts      = self.valid_exts)
            time_used = tools.get_delta_time(time.time()-t)
            self.debug_message('Thumbsnails of images for process {0} '
                               'converted in {1}'.format(self.process_id,time_used))
        except image_tools.ConvertError as e:
            error = str(e)
        except Exception as e:
            self.glogger.exception(e)
            error = str(e)
        return error
    
    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        process_root = self.command_line.process_path
        # Set path to input folder
        master_img_rel = self.getConfigItem('img_master_path',
                                            section = self.folder_structure_section) 
        self.input_folder = os.path.join(process_root, master_img_rel)
        # Set path to output folder 
        master_jpeg_rel = self.getConfigItem('img_master_jpeg_path',
                                             section = self.folder_structure_section) 
        self.output_folder = os.path.join(process_root, master_jpeg_rel)
        tools.find_or_create_dir(self.output_folder)
        # Get quality and resize options for image conversion
        self.quality = self.getConfigItem('quality') 
        self.resize_type = self.getConfigItem('resize_type')
        self.resize = self.getConfigItem('resize')
        exts = self.getConfigItem('valid_file_exts',section = self.valid_file_exts_section)
        self.valid_exts = exts.split(';')

if __name__ == '__main__' :
    CreateThumbnails().begin()
