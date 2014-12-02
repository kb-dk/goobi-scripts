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
        self.ocr_output_section = 'copy_from_ocr'
        self.valid_exts_section = 'move_invalid_files'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section,
                                               self.ocr_output_section,
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
        rel_master_image_path = self.getConfigItem('img_master_path',None,self.folder_structure_section)

        # img_master_path = images/master_orig/
        self.source_folder = os.path.join(process_path,rel_master_image_path)

        # ======================================================================
        # legr: Get the correct OCR server for the issue - antikva or fraktur
        # ======================================================================
        ocr_workflow_type = self.getSetting('ocr_workflow_type') # legr: how do I get this from Goobi?
        if ocr_workflow_type == 'antikva':
            # legr: currently antikva on ocr-01
            ocr_transitfolder = self.getSetting('ocr_antikva_transit')
            ocr_hotfolder = self.getSetting('ocr_antikva_hotfolder')
        elif ocr_workflow_type == 'fraktur':
            # legr: currently fraktur on ocr-02
            ocr_transitfolder = self.getSetting('ocr_fraktur_transit')
            ocr_hotfolder = self.getSetting('ocr_fraktur_hotfolder')
        self.transit_dir = os.path.join(ocr_transitfolder,process_title)
        self.hotfolder_dir = os.path.join(ocr_hotfolder,process_title)

        self.sleep_interval = int(self.getConfigItem('sleep_interval'))
        self.retries = int(self.getConfigItem('retries'))
        
        self.goobi_pdf = os.path.join(process_path, 
            self.getConfigItem('doc_limbpdf_path', None, 'process_folder_structure'))
        self.valid_exts = self.getConfigItem('valid_file_exts',None, self.valid_exts_section).split(';')
        input_files = self.getConfigItem('img_master_path',None, self.folder_structure_section) 
        self.input_files = os.path.join(process_path,input_files)
        
        #=======================================================================
        # Get the correct LIMB workflow hotfolder for the issue - BW or Color
        #=======================================================================
        #limb_workflow_type = self.getSetting('limb_workflow_type')
        #if limb_workflow_type == 'bw':
        #    limb_hotfolder = self.getSetting('limb_bw_hotfolder')
        #elif limb_workflow_type == 'color':
        #    limb_hotfolder = self.getSetting('limb_color_hotfolder')
        #self.hotfolder_dir = os.path.join(limb_hotfolder,process_title)

    def step(self):
        error = None
        self.getVariables()
        msg = ('Copying files from {0} to {1} via transit {2}.')
        msg = msg.format(self.source_folder, self.hotfolder_dir, self.transit_dir)
        self.debug_message(msg)
        try:
            """
            legr:
            source = {processpath} + "images/master_orig/"
            transit = "/tmp/ocr-02/InputFolder/dod-transit/" + {processtitle} # tmp to replaced with mnt when prod-ready
            dest =
            """
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
    CopyToOcr().begin()