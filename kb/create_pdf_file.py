#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools.imconvert import convert_options,pdf

class CreatePdfFile( Step ):

    def setup(self):
        self.config_main_section = 'create_pdf_file'
        self.folder_structure_section = 'process_folder_structure'
        self.convert_options_section = 'convert_options'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section,
                                               self.convert_options_section,
                                               self.convert_options_section] )
        self.essential_commandlines = {
            "process_id" : "number",
            "process_path" : "folder",
            "config_path" : "string",
            "step_name" : "string",
            "auto_report_problem" : "string",
            "process_title" : "string",
        }

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        process_path = self.command_line.process_path
        rel_master_image_path = self.getConfigItem('img_master_path',
                                                   section=self.folder_structure_section) 
        self.source_dir = os.path.join(process_path,rel_master_image_path)
        # Set location of convert options
        rel_co_folder = self.getConfigItem('metadata_convert_path',
                                           section=self.folder_structure_section)
        co_filename = self.getConfigItem('convert_options_filename',
                                         section=self.convert_options_section)
        self.co_file_path = os.path.join(process_path, rel_co_folder,co_filename)
        # Set file path for output pdf-file
        rel_pdf_folder = self.getConfigItem('doc_pdf_path',
                                            section=self.folder_structure_section) 
        pdf_file_name = self.command_line.process_title+'.pdf'
        self.pdf_file_path = os.path.join(process_path,rel_pdf_folder,pdf_file_name)
        # Set location for temp pdf files production
        rel_temp_folder = self.getConfigItem('temp_pdf_creation_path',
                                            section=self.folder_structure_section) 
        self.temp_folder = os.path.join(process_path,rel_temp_folder)
        
        self.max_batch_size = int(self.getConfigItem('max_batch_size'))
        self.log_count = int(self.getConfigItem('log_count'))
        
    def step(self):
        error = None
        try:
            self.getVariables()
            msg = ('Creating pdf file from images in {0} as defined in {1}.')
            msg = msg.format(self.source_dir,self.co_file_path)
            self.debug_message(msg)
            co = convert_options.load_convert_options(self.co_file_path)
            msg = ('Creating temp files for pdf in {0} Max batch size: {1}. '
                   'Log count: {2}')
            msg = msg.format(self.temp_folder,self.max_batch_size,self.log_count)
            self.debug_message(msg)
            temp_pdf_files = pdf.create_temp_pdf_files(co,
                                                       self.temp_folder,
                                                       self.max_batch_size,
                                                       self.log_count,
                                                       self.glogger)
            msg = ('Merging {0} temp files to pdf file {1}')
            msg = msg.format(str(len(temp_pdf_files)),self.pdf_file_path)
            self.debug_message(msg)
            pdf.merge_temp_pdf_files(self.temp_folder,
                                     temp_pdf_files,
                                     self.pdf_file_path)
            msg = ('Removing temp files in {0}')
            msg = msg.format(self.temp_folder)
            self.debug_message(msg)
            #pdf.clear_pdf_conversion(self.temp_folder)
        except Exception as e:
            error = str(e)
            self.glogger.exception(error)
        return error

if __name__ == '__main__':
    CreatePdfFile().begin()