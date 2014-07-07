#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools.img_convert import convert_options

class CreateConvertOptions( Step ):

    def setup(self):
        self.config_main_section = 'create_convert_options'
        self.default_convert_options = 'default_convert_options'
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
        }

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        # Get path to image files
        rel_master_image_path = self.getConfigItem('img_master_path',
                                                   section=self.folder_structure_section) 
        self.source_folder = os.path.join(self.command_line.process_path,
                                       rel_master_image_path)
        # Get path to store json file with convert options
        rel_co_folder = self.getConfigItem('metadata_convert_path',
                                           section=self.folder_structure_section)
        co_folder = os.path.join(self.command_line.process_path,
                                      rel_co_folder) 
        co_filename = self.getConfigItem('convert_options_filename',
                                         section=self.convert_options_section)
        self.co_file_path = os.path.join(co_folder,co_filename)
        # Load default convert options from config 
        self.default_options = self.getConfigSection(self.default_convert_options)

    def step(self):
        error = None
        try:
            self.getVariables()
            msg = ('Creating convert options for {0}.')
            msg = msg.format(self.source_folder)
            self.debug_message(msg)
            default_options = convert_options.parse_options(self.default_options)
            co = convert_options.create_convert_options(self.source_folder,
                                                        default_options)
            convert_options.save_json_file(co,self.co_file_path)
        except Exception as e:
            error = str(e)
            self.glogger.exception(error)
        return error

if __name__ == '__main__':
    CreateConvertOptions().begin()