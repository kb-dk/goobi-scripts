#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''

from tools import tools
import os
from goobi.goobi_step import Step
from tools.image_tools import misc as image_tools
from tools.pdf import misc as pdf_tools
from tools.filesystem import fs

class AddBindingsToBwPdf( Step ) :

    def setup(self):
    
        self.name = "Tilføj for- og bagside til BW PDF"
        self.config_main_section = "add_binding_to_bw_pdf"
        self.essential_config_sections = set( [] )
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'valid_file_exts'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            "process_path":"folder",
            'process_title':"string"
        }
    
    def step(self):
        error = None
        self.getVariables()
        try:
            self.addBindingsToPdf()
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
        root = self.command_line.process_path
        self.process_title = self.command_line.process_title
        
        self.valid_exts = self.getConfigItem('valid_file_exts',section=self.valid_exts_section).split(';')
        # Set path to input folder
        master_img_rel = self.getConfigItem('img_master_path',
                                            section = self.folder_structure_section) 
        self.img_master_path = os.path.join(root, master_img_rel)
        # Get/set path for the master bw pdf
        doc_pdf_bw_path = self.getConfigItem('doc_pdf_bw_path',
                                            section = self.folder_structure_section)
        doc_pdf_bw_path = os.path.join(root,doc_pdf_bw_path)
        self.pdf_bw_path = tools.getFirstFileWithExtension(doc_pdf_bw_path, 'pdf')
        # Get path for temp folder -> nb absolute
        self.temp_root = self.getConfigItem('temp_folder')
        # Get quality for output pdfs
        self.quality = int(self.getConfigItem('quality'))
        # Get resize pct for output pdf
        self.resize = int(self.getConfigItem('resize'))

    def addBindingsToPdf(self):
        # Create temp folder for temp pdf-files
        temp_folder = os.path.join(self.temp_root,self.process_title)
        tools.create_folder(temp_folder)
        # Get path for first and last image
        images = fs.getFilesInFolderWithExts(self.img_master_path,
                                             self.valid_exts,
                                             absolute=True)
        # Create PDF of bindings (first and last image in master image folder)
        front_image_path = images[0]
        end_image_path = images[-1]
        # Add front-binding to pdf
        front_pdf_path = os.path.join(temp_folder,'front.pdf')
        end_pdf_path = os.path.join(temp_folder,'end.pdf') 
        image_tools.compressFile(input_file     = front_image_path, 
                                 output_file    = front_pdf_path,
                                 quality        = self.quality,
                                 resize         = self.resize)
        image_tools.compressFile(input_file     = end_image_path, 
                                 output_file    = end_pdf_path,
                                 quality        = self.quality,
                                 resize         = self.resize)
        # Add back-binding to pdf
        pdf_list = [front_pdf_path,self.pdf_bw_path,end_pdf_path]
        temp_dest = os.path.join(temp_folder,self.process_title+'.pdf')
        pdf_tools.joinPdfFiles(pdf_list, temp_dest)
        os.rename(temp_dest, self.pdf_bw_path)
        # Delete temp_folder
        fs.clear_folder(temp_folder, also_folder=True)

if __name__ == '__main__' :
    AddBindingsToBwPdf().begin()
