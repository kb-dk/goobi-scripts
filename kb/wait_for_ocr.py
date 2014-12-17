#!/usr/bin/env python
# -*- coding: utf-8

from goobi.goobi_step import Step
import tools.tools as tools
import tools.limb as limb_tools
import os, time
from tools.filesystem import fs

class WaitForOcr( Step ):

    def setup(self):
        self.name = 'Vent på output-filer fra OCR'
        self.config_main_section = 'wait_for_ocr'
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'valid_file_exts'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            'process_path' : 'folder',
            'auto_report_problem' : 'string',
            'process_title' : 'string'
        }



    
    
    def step(self):
        '''
        This script's role is to wait until
        ocr processing is complete before finishing.
        In the event of a timeout, it reports back to 
        previous step before exiting.
        '''
        error = None
        try:
            #===================================================================
            # Get and set variables
            #===================================================================
            self.getVariables()
            #===================================================================
            # Delete existing bw-pdf file
            #===================================================================
            fs.clear_folder(self.goobi_pdf)
            #===================================================================
            # Wait for PDF-file to be ready on OCR-server
            #===================================================================
            self.waitForOcr()
        except IOError as e:
            # if we get an IO error we need to crash
            error = ('Error reading from directory {0}')
            error = error.format(e.strerror)
            return error
        except ValueError as e:
            # caused by conversion of non-numeric strings in config to nums
            error = "Invalid config data supplied, error: {0}"
            error = error.format(e.strerror)
            return error
        # if we've gotten this far, we've timed out and need to go back to the previous step
        return "Timed out waiting for ocr output."

    def waitForOcr(self):
        retry_counter = 0
        while retry_counter < self.retry_num:
            if self.ocrIsReady():
                msg = ('ocr output is ready - exiting.')
                self.debug_message(msg)
                return None # this is the only successful exit possible
            else:
                # if they haven't arrived, sit and wait for a while
                msg = ('ocr output not ready - sleeping for {0} seconds...')
                msg = msg.format(self.retry_wait)
                self.debug_message(msg)
                retry_counter += 1
                time.sleep(self.retry_wait)

    def getVariables(self):
        '''
        We need the ocr_output folder,
        the location of the toc file
        Throws error if any directories are missing
        or if our retry vals are not numbers
        '''
        process_title = self.command_line.process_title
        process_path = self.command_line.process_path
        # set ocr to current outputfolder - antikva or fraktur         
        try:
            ocr_workflow_type = self.getSetting('ocr_workflow_type').lower()
        except KeyError:
            self.error_message('{0} er ikke givet med som variabel til scriptet.'.format('ocr_workflow_type'))
        if ocr_workflow_type == 'antikva':
            # legr: currently antikva on ocr-01
            ocr = self.getConfigItem('ocr_antikva_outputfolder')
        elif ocr_workflow_type == 'fraktur':
            # legr: currently fraktur on ocr-02
            ocr = self.getConfigItem('ocr_fraktur_outputfolder')
        else:
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten være '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr_workflow_type',self.name,ocr_workflow_type)
            self.error_message(err)
        #=======================================================================
        # Join paths to create absolute paths
        #=======================================================================
        self.pdf_input_dir = os.path.join(ocr, process_title)
        #=======================================================================
        # Set destination for paths
        #=======================================================================
        bw_path = self.getConfigItem('doc_pdf_bw_path',
                                     section = self.folder_structure_section)
        self.goobi_pdf = os.path.join(process_path, bw_path)
        #=======================================================================
        # Get path for input-files in process folder
        #=======================================================================
        input_files = self.getConfigItem('img_pre_processed_path',
                                         section=self.folder_structure_section) 
        self.input_files = os.path.join(process_path,input_files)
        #=======================================================================
        # Get retry number and retry-wait time
        #=======================================================================
        self.retry_num = int(self.getConfigItem('retry_num'))
        self.retry_wait = int(self.getConfigItem('retry_wait'))
        #=======================================================================
        # Get valid extension for image files
        #=======================================================================
        v_exts = self.getConfigItem('valid_file_exts',
                                    section = self.valid_exts_section)
        self.valid_exts = v_exts.split(';')
        
    def ocrIsReady(self):
        '''
        Check to see if OCR is finished
        return boolean
        '''
        try: 
            # raises error if one of our directories is missing
            tools.ensureDirsExist(self.pdf_input_dir, self.input_files)
        except IOError as e:
            msg = ('One of the output folder from OCR is not yet created.'
                   ' Waiting for OCR to be ready. Error: {0}')
            msg = msg.format(e.strerror)
            self.debug_message(msg)
            return False
        # legr: we can use limb_tools generally - they are not Limb specific
        # we should rename them someday
        pdf_ok = limb_tools.pageCountMatches(self.pdf_input_dir,
                                             self.input_files,
                                             self.valid_exts)
        if pdf_ok:
            return True
        return False

if __name__ == '__main__':
    
    WaitForOcr( ).begin()
