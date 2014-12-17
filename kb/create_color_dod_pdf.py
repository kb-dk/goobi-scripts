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
from tools.filesystem import fs

class CreateColorPdf( Step ) :

    def setup(self):
    
        self.name = "Opret farve-pdf ud fra skannede billeder"
        self.config_main_section = "create_color_pdf"
        self.essential_config_sections = set( [] )
        self.folder_structure_section = 'process_folder_structure'
        self.valid_file_exts_section = 'valid_file_exts'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.valid_file_exts_section] )
        self.essential_commandlines = {
            "process_path":"folder",
            "auto_complete":"string"}
    
    def step(self):
        error = None
        try:
            #===================================================================
            # Get and set variables
            #===================================================================
            self.getVariables()
            #===================================================================
            # Create folder for temporary pdf-files
            #===================================================================
            fs.create_folder(self.temp_folder)
            #===================================================================
            # Delete previously created color pdf
            #===================================================================
            fs.clear_folder(self.pdf_color_folder_path)
            #===================================================================
            # Convert input images to one pdf
            #===================================================================
            convert.createPdfFromFolder(src         = self.input_folder, 
                                        file_dest   = self.color_pdf_path, 
                                        temp_folder = self.temp_folder, 
                                        quality     = self.quality, 
                                        resize_pct  = self.resize, 
                                        valid_exts  = self.valid_exts)
        except image_tools.ConvertError as e:
            error = str(e)
        return error

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        root = self.command_line.process_path
        process_title = self.command_line.process_title
        # Set path to input folder
        master_img_rel = self.getConfigItem('img_master_path',
                                            section = self.folder_structure_section) 
        self.input_folder = os.path.join(root, master_img_rel)
        # Get/set path for the master bw pdf
        doc_pdf_color_path = self.getConfigItem('doc_pdf_color_path',
                                            section = self.folder_structure_section)
        self.pdf_color_folder_path = os.path.join(root,doc_pdf_color_path)
        #=======================================================================
        # Set the name for the output color pdf file
        # Assumed process title: [barcode]_[Antiqkva/Fraktur]
        # Required name: [barcode]_color.pdf
        #=======================================================================
        if '_' in process_title:
            color_pdf_name = process_title.split('_')[0]
        else:
            color_pdf_name = process_title
        color_pdf_name = color_pdf_name+'_color.pdf'
        self.color_pdf_path = os.path.join(self.pdf_color_folder_path,color_pdf_name)
        # Get quality and resize options for image conversion
        self.quality = self.getConfigItem('quality') 
        self.resize = self.getConfigItem('resize')
        self.valid_exts = self.getConfigItem('valid_file_exts',
                                             section = self.valid_file_exts_section).split(';')
        temp_root = self.getConfigItem('temp_folder')
        self.temp_folder = os.path.join(temp_root,process_title) 

if __name__ == '__main__' :
    CreateColorPdf().begin()
