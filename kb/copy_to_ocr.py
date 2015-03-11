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
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten vaere '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr_workflow_type',self.name,ocr_workflow_type)
            self.error_message(err)

        self.transit_dir = os.path.join(ocr_transitfolder,process_title)
        self.hotfolder_dir = os.path.join(ocr_hotfolder,process_title)
        #=======================================================================
        # Set retry wait time and retry count for copying files
        #=======================================================================
        self.retry_wait = int(self.getConfigItem('retry_wait'))
        self.retry_num = int(self.getConfigItem('retry_num'))
        #=======================================================================
        # Set valid extensions for image files to check as preprocessed
        #=======================================================================
        self.valid_exts = self.getConfigItem('valid_file_exts', None, self.valid_exts_section).split(';')
        #=======================================================================
        # Set variables for waiting for preprocessed images to be ready
        #=======================================================================
        self.pp_retry_wait = int(self.getConfigItem('preprocess_retry_wait'))
        self.pp_retry_num = int(self.getConfigItem('preprocess_retry_num'))
        img_list = fs.getFilesInFolderWithExts(self.master_folder, self.valid_exts)
        # Source images miunus first and last image
        self.expected_image_count = len(img_list)-2

    def waitForPreprocessedImages(self):
        retry = 0
        while retry <= self.pp_retry_num:
            # ==================================================================
            # Get current number of preprocessed images
            # ==================================================================
            pp_files = fs.getFilesInFolderWithExts(self.source_folder, self.valid_exts)
            # ==================================================================
            # Exit loop when preprocessed images are ready
            # ==================================================================
            if len(pp_files) == self.expected_image_count:
                # ==============================================================
                # Wait 30 sec to make sure images are completely copied
                # ==============================================================
                time.sleep(30)
                return True
            # ==================================================================
            # This shouldn't happen, but we have seen pdf's with duplicate pages, so better check
            # ==================================================================
            if len(pp_files) > self.expected_image_count:
                if len(pp_files) > 0:
                    self.error_message("Der er flere preprocesserede billeder ({}) end scannede billeder ({})"
                                       .format(pp_files, self.expected_image_count))
                    return False
            # ==================================================================
            # Wait "self.pp_retry_wait" seconds
            # ==================================================================
            retry += 1
            self.error_message("Preprocesserede billeder ikke klar, venter {} sek".format(self.pp_retry_wait))
            self.error_message("Retry {} of {}".format(retry, self.pp_retry_num))
            time.sleep(self.pp_retry_wait)
        return False
    
    def step(self):
        error = None
        try:
            self.getVariables()
            msg = 'Copying files from {0} to {1} via transit {2}.'
            msg = msg.format(self.source_folder, self.hotfolder_dir, self.transit_dir)
            self.debug_message(msg)
            self.error_message(msg)
            #===================================================================
            # Wait for preprocessed images to be ready
            # Returns false if it times out 
            #===================================================================
            if not self.waitForPreprocessedImages():
                pp_files = fs.getFilesInFolderWithExts(self.source_folder, self.valid_exts)
                raise Exception('Timed out or count error while waiting for pre-processing of '
                                'images. Current number of processed images: '
                                '{0}. Expected amount: {1}'.format(pp_files,self.expected_image_count))
            #===================================================================
            # Copy files to OCR-server
            #===================================================================
            self.error_message("Start copy of preprocessed images to OCR-server")
            tools.copy_files(source          = self.source_folder,
                             dest            = self.hotfolder_dir,
                             transit         = self.transit_dir,
                             delete_original = False,
                             wait_interval   = self.retry_wait,
                             max_retries     = self.retry_num,
                             logger          = self.glogger,
                             valid_exts      = self.valid_exts)
            self.error_message("Finished copy of preprocessed images to OCR-server")
        except errors.TransferError as e:
            error = e.strerror
        except errors.TransferTimedOut as e:
            error = e.strerror
        except Exception as e:
            error = str(e)
        return error

if __name__ == '__main__':    
    CopyToOcr().begin()