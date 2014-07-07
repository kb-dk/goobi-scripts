#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools import errors
from tools.filesystem import fs

class CopyToLimb( Step ):

    def setup(self):
        self.name = 'Copy to LIMB'
        self.config_main_section = 'copy_to_limb'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            "process_id" : "number",
            "process_path" : "folder",
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
        self.source_folder = os.path.join(self.command_line.process_path,
                                       rel_master_image_path)
        self.transit_dir = os.path.join(self.getConfigItem('limb_transit'),
                                   self.command_line.process_title)
        self.hotfolder_dir = os.path.join(self.getConfigItem('limb_hotfolder'),
                                          self.command_line.process_title)
        self.sleep_interval = int(self.getConfigItem('sleep_interval'))
        if (self.command_line.has('overwrite_files') and 
            self.command_line.overwrite_files.lower() == True):
            self.overwrite_destination_files = True
        else:
            self.overwrite_destination_files = False
        self.retries = int(self.getConfigItem('retries'))

    def step(self):
        error = None
        self.getVariables()
        msg = ('Copying files from {0} to {1} via transit {2}.')
        msg = msg.format(self.source_folder, self.hotfolder_dir, self.transit_dir)
        self.debug_message(msg)
        try:
            if not self.overwrite_destination_files:
                if (tools.folderExist(self.hotfolder_dir) and
                    fs.compareDirectories(self.source_folder, self.hotfolder_dir)):
                    return error
            tools.copy_files(source = self.source_folder,
                             dest = self.hotfolder_dir,
                             transit = self.transit_dir,
                             delete_original = False,
                             wait_interval = self.sleep_interval,
                             max_retries = self.retries,
                             logger = self.glogger)
        except errors.TransferError as e:
            error = e.strerror
        except errors.TransferTimedOut as e:
            error = e.strerror
        except Exception as e:
            error = str(e)
        return error

if __name__ == '__main__':    
    CopyToLimb().begin()