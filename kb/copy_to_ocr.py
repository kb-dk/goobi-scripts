#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools import errors
from tools.filesystem import fs
import time

class CopyToOcr( Step ):

    def setup(self):
        self.name = 'Kopiering af billeder til OCR'
        self.config_main_section = 'copy_to_ocr'
        self.valid_exts_section = 'valid_file_exts'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.valid_exts_section] )
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
        
        process_title = self.command_line.process_title
        process_path = self.command_line.process_path
        #=======================================================================
        # Path to folder with master image files
        #=======================================================================
        # img_master_path = images/master_orig/
        mi_img = self.getConfigItem('img_master_path',
                                    section = self.folder_structure_section)
        self.master_folder = os.path.join(process_path,mi_img)
        #=======================================================================
        # Path to folder with preprocessed files
        #=======================================================================
        pp_img = self.getConfigItem('img_pre_processed_path',
                                    section = self.folder_structure_section)
        self.source_folder = os.path.join(process_path,pp_img)
        # ======================================================================
        # legr: Get the correct OCR server for the issue - antikva or fraktur
        # Break if argument somehow is missing or have an invalid name
        # ======================================================================
        try:
            ocr_workflow_type = self.getSetting('ocr_workflow_type').lower()
        except KeyError:
            self.error_message('{0} er ikke givet med som variabel til scriptet.'.format('ocr_workflow_type'))
            
        if ocr_workflow_type == 'antikva':
            # legr: currently antikva on ocr-01
            ocr_transitfolder = self.getSetting('ocr_antikva_transit')
            ocr_hotfolder = self.getSetting('ocr_antikva_hotfolder')
        elif ocr_workflow_type == 'fraktur':
            # legr: currently fraktur on ocr-02
            ocr_transitfolder = self.getSetting('ocr_fraktur_transit')
            ocr_hotfolder = self.getSetting('ocr_fraktur_hotfolder')
        else:
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten være '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr_workflow_type',self.name,ocr_workflow_type)
            self.error_message(err)

        self.transit_dir = os.path.join(ocr_transitfolder,process_title)
        self.hotfolder_dir = os.path.join(ocr_hotfolder,process_title)

        self.retry_wait = int(self.getConfigItem('retry_wait'))
        self.retry_num = int(self.getConfigItem('retry_num'))
        self.valid_exts = self.getConfigItem('valid_file_exts',None, self.valid_exts_section).split(';')
        #=======================================================================
        # Set variables for waiting for preprocessed images to be ready
        #=======================================================================
        self.pp_retry_wait = int(self.getConfigItem('preprocess_retry_wait'))
        self.pp_retry_num = int(self.getConfigItem('preprocess_retry_num'))
        img_list = fs.getFilesInFolderWithExts(self.master_folder, self.valid_exts)
        self.excepted_image_count = len(img_list-2) # Source images miunus first and last image

    def waitForPreprocessedImages(self):
        retry = 0
        while retry <= self.pp_retry_num:
            # Get current number of preprocessed images
            pp_files = fs.getFilesInFolderWithExts(self.source_folder, self.valid_exts)
            # Check if all files are preprocessed
            if len(pp_files) == self.excepted_image_count:
                break
            # Wait "self.pp_retry_wait" seconds
            time.sleep(self.pp_retry_wait)
            retry += 1
    
    def step(self):
        error = None
        msg = ('Copying files from {0} to {1} via transit {2}.')
        msg = msg.format(self.source_folder, self.hotfolder_dir, self.transit_dir)
        self.debug_message(msg)
        try:
            self.getVariables()
            #===================================================================
            # Wait for preprocessed images to be ready 
            #===================================================================
            self.waitForPreprocessedImages()
            #===================================================================
            # Copy files to OCR-server
            #===================================================================
            tools.copy_files(source          = self.source_folder,
                             dest            = self.hotfolder_dir,
                             transit         = self.transit_dir,
                             delete_original = False,
                             wait_interval   = self.retry_wait,
                             max_retries     = self.retry_num,
                             logger          = self.glogger,
                             valid_exts      = self.valid_exts)
        except errors.TransferError as e:
            error = e.strerror
        except errors.TransferTimedOut as e:
            error = e.strerror
        except Exception as e:
            error = str(e)
        return error

if __name__ == '__main__':    
    CopyToOcr().begin()