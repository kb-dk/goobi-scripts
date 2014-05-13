#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools import errors

class CopyToLimb( Step ):

    def setup(self):
        self.name = 'Copy to LIMB'
        self.config_main_section = 'copy_to_limb'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            "process_id" : "number",
            "process_root_path" : "folder",
            "process_title" : "string"
        }

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        rel_master_image_path = self.getConfigItem('img_master_path',
                                                   None,
                                                   self.folder_structure_section) 
        self.source_dir = os.path.join(self.command_line.process_root_path,
                                       rel_master_image_path)
        self.transit_dir = os.path.join(self.getConfigItem('limb_transit'),
                                   self.command_line.process_title)
        self.hotfolder_dir = os.path.join(self.getConfigItem('limb_hotfolder'),
                                          self.command_line.process_title)
        self.sleep_interval = int(self.getConfigItem('sleep_interval'))
        self.retries = int(self.getConfigItem('retries'))

    def step(self):
        error = None
        self.getVariables()
        msg = ('Copying files from {0} to {1} via transit {2}.')
        msg = msg.format(self.source_dir, self.hotfolder_dir, self.transit_dir)
        self.debug_message(msg)
        try:
            tools.copy_files(source = self.source_dir,
                             dest = self.hotfolder_dir,
                             transit = self.transit_dir,
                             delete_original = False,
                             wait_interval = self.sleep_interval,
                             max_retries = self.retries,
                             logger = self.glogger,
                             debug = True)
        except errors.TransferError as e:
            error = e.strerror
        except errors.TransferTimedOut as e:
            error = e.strerror
        return error

if __name__ == '__main__':    
    CopyToLimb().begin()