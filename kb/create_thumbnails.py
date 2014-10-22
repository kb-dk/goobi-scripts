#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''

from tools import tools
import os
from goobi.goobi_step import Step
import tools.img_convert.convert_folder as convert
from tools.filesystem import fs


class CreateThumbnails( Step ) :

    def setup(self):
    
        self.name = "Oprettelse af thumbnails"
        self.config_main_section = "create_thumbnails"
        self.essential_config_sections = set( [] )
        self.folder_structure_section = 'process_folder_structure'
        self.move_invalid_files= 'move_invalid_files'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.move_invalid_files] )
        self.essential_commandlines = {
            "process_path":"folder",
            "auto_complete":"string"
        }
    
    def step(self):
        error = None
        self.getVariables()
        try:
            image_ext = fs.detectImagesExts(self.input_folder,self.valid_exts)
            convert.convert_folder(input_folder    = self.input_folder,
                                   output_folder   = self.output_folder,
                                   quality         = self.quality,
                                   resize_type     = self.resize_type,
                                   resize          = self.resize,
                                   input_ext       = image_ext)
        except convert.ConvertError as e:
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
        self.valid_exts = self.getConfigItem('valid_file_exts',
                                             section = self.move_invalid_files).split(';')

if __name__ == '__main__' :
    CreateThumbnails().begin()
