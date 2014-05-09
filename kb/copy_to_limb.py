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
        self.essential_config_sections = set( [] )
        self.essential_commandlines = {
            "process_id" : "number",
            "source" : "folder",
        }

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        self.files_not_copied  = True
        self.source_dir = self.command_line.source
        self.transit_dir = os.path.join(self.getConfigItem('limb_transit'),
                                   os.path.basename(self.source_dir))
        self.hotfolder_dir = self.getConfigItem('limb_hotfolder')
        self.sleep_interval = int(self.getConfigItem('sleep_interval'))
        self.retries = int(self.getConfigItem('retries'))

    def step(self):
        error = None
        self.getVariables()
        self.info_message("source_dir "+self.source_dir)
        try:
            tools.copy_files(self.source_dir,
                             self.hotfolder_dir,
                             self.transit_dir,
                             delete_original = False,
                             self.sleep_interval,
                             self.retries,
                             self.glogger)
        except errors.TransferError as e:
            if e.typeerror == 1:
                error = e.strerror
            elif e.typeerror == 2:
                error = e.strerror
            else:
                error = 'Unknown error type'
        return error

if __name__ == '__main__':    
    CopyToLimb().begin()
