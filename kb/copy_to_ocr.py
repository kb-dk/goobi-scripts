#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools import errors
from tools.filesystem import fs
import tools.limb as limb_tools



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
        # img_master_path = images/master_orig/
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

        # legr:
        # We could define pdf, inputfile and ext-variables for use if we want to test if files already is present:
        # self.goobi_pdf_color = os.path.join(process_path, 
        #    self.getConfigItem('doc_pdf_color_path', None, 'process_folder_structure'))
        # self.goobi_pdf_bw = os.path.join(process_path, 
        #    self.getConfigItem('doc_pdf_bw_path', None, 'process_folder_structure'))
        # input_files = self.getConfigItem('img_master_path',None, self.folder_structure_section) 
        # self.input_files = os.path.join(process_path,input_files)


    def step(self):
        error = None
        self.getVariables()
        msg = ('Copying files from {0} to {1} via transit {2}.')
        msg = msg.format(self.source_folder, self.hotfolder_dir, self.transit_dir)
        self.debug_message(msg)
        try:
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