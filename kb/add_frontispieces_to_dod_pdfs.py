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

class AddFrontispiecesToPdfs( Step ) :

    def setup(self):
    
        self.name = "Tilføj frontispieces til begge PDFer"
        self.config_main_section = "add_frontispieces_to_pdfs"
        self.essential_config_sections = set( [] )
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section] )
        self.essential_commandlines = {
            "process_path":"folder",
            'process_title':"string"
        }
    
    def step(self):
        error = None
        self.getVariables()
        try:
            self.addFrontispiecesToPdfs()
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
        # Set path to input folder
        master_img_rel = self.getConfigItem('img_master_path',
                                            section = self.folder_structure_section) 
        self.img_master_path = os.path.join(root, master_img_rel)
        # Get/set path for the master bw pdf
        doc_pdf_bw_path = self.getConfigItem('doc_pdf_bw_path',
                                            section = self.folder_structure_section)
        doc_pdf_bw_path = os.path.join(root,doc_pdf_bw_path)
        self.pdf_bw_path = tools.getFirstFileWithExtension(doc_pdf_bw_path, 'pdf')
        # Get/set path for the master bw pdf
        doc_pdf_color_path = self.getConfigItem('doc_pdf_color_path',
                                            section = self.folder_structure_section)
        doc_pdf_color_path = os.path.join(root,doc_pdf_color_path)
        self.pdf_color_path = tools.getFirstFileWithExtension(doc_pdf_color_path, 'pdf')
        # Get path for temp folder -> nb absolute
        self.temp_root = self.getConfigItem('temp_folder')
        # Get quality for output pdfs
        self.frontispieces = int(self.getConfigItem('frontispieces'))

    def addFrontispiecesToPdfs(self):
        # Create temp folder for temp pdf-files
        temp_folder = os.path.join(self.temp_root,self.process_title)
        tools.create_folder(temp_folder)
        self.addFrontispiecesToPdf(self.pdf_bw_path,temp_folder)
        self.addFrontispiecesToPdf(self.pdf_color_path,temp_folder)
        # Delete temp_folder
        fs.clear_folder(temp_folder, also_folder=True)

    def addFrontispiecesToPdf(self,pdf,temp_folder):
        pdf_list = [self.frontispieces,pdf]
        temp_dest = os.path.join(temp_folder,self.process_title+'.pdf')
        pdf_tools.joinPdfFiles(pdf_list, temp_dest)
        os.rename(temp_dest, pdf)
        

if __name__ == '__main__' :
    AddFrontispiecesToPdfs().begin()
