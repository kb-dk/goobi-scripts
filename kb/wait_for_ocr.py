#!/usr/bin/env python
# -*- coding: utf-8

from goobi.goobi_step import Step
import tools.tools as tools
import tools.limb as limb_tools
import os, time

class WaitForOcr( Step ):

    def setup(self):
        self.name = 'Vent på output-filer fra OCR'
        self.config_main_section = 'copy_from_ocr'
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'move_invalid_files'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            'process_id' : 'number',
            'process_path' : 'folder',
            'auto_report_problem' : 'string',
            'step_id' : 'number'
        }
    def getVariables(self):
        '''
        We need the ocr_output folder,
        the location of the toc file
        Throws error if any directories are missing
        or if our retry vals are not numbers
        '''
        process_title = self.command_line.process_title

        # set ocr to current outputfolder - antikva or fraktur         
        try:
            ocr = self.getSetting('ocr_workflow_type').lower()
        except KeyError:
            self.error_message('{0} er ikke givet med som variabel til scriptet.'.format('ocr'))
        if ocr == 'antikva':
            # legr: currently antikva on ocr-01
            ocr_transitfolder = self.getSetting('ocr_antikva_transit')
            ocr_hotfolder = self.getSetting('ocr_antikva_hotfolder')
        elif ocr == 'fraktur':
            # legr: currently fraktur on ocr-02
            ocr_transitfolder = self.getSetting('ocr_fraktur_transit')
            ocr_hotfolder = self.getSetting('ocr_fraktur_hotfolder')
        else:
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten være '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr',self.name,ocr)
            self.error_message(err)

        alto = self.getConfigItem('alto')
        toc = self.getConfigItem('toc')
        pdf = self.getConfigItem('pdf')
        
        # join paths to create absolute paths
        self.ocr_dir = os.path.join(ocr, process_title)
        self.alto_dir = os.path.join(self.ocr_dir, alto)
        self.toc_dir = os.path.join(self.ocr_dir, toc)
        self.pdf_input_dir = os.path.join(self.ocr_dir, pdf)
        
        # Set destination for paths
        self.goobi_altos = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_alto_path', None, 'process_folder_structure'))
        self.goobi_pdf = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_pdf_color_path', None, 'process_folder_structure'))
        self.valid_exts = self.getConfigItem('valid_file_exts',None, self.valid_exts_section).split(';')
        # Get path for input-files in process folder
        process_path = self.command_line.process_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files = os.path.join(process_path,input_files)
        
        # Get retry number and retry-wait time
        self.retry_num = int(self.getConfigItem('retry_num'))
        self.retry_wait = int(self.getConfigItem('retry_wait'))
        
        # Set flag for ignore if files already have been copied to goobi
        self.ignore_goobi_folder = self.getSetting('ignore_goobi_folder', bool, default=False)
        
    def step(self):
        '''
        This script's role is to wait until
        ocr processing is complete before finishing.
        In the event of a timeout, it reports back to 
        previous step before exiting.
        '''
        error = None
        retry_counter = 0
        try:
            self.getVariables()
            # First check if files already have been copied to goobi
            if (not self.ignore_goobi_folder and 
                limb_tools.alreadyMoved(self.goobi_pdf,self.input_files,
                                        self.goobi_altos,self.valid_exts)):
                return error
            # keep on retrying for the given number of attempts
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


        
    def ocrIsReady(self):
        '''
        Check to see if OCR is finished
        return boolean
        '''
        try: 
            # raises error if one of our directories is missing
            tools.ensureDirsExist(self.ocr_dir, self.alto_dir, \
                self.toc_dir, self.pdf_input_dir, self.input_files)
        except IOError as e:
            msg = ('One of the output folder from OCR is not yet created.'
                   ' Waiting for OCR to be ready. Error: {0}')
            msg = msg.format(e.strerror)
            self.debug_message(msg)
            return False
        # legr: we can use limb_tools generally - they are not Limb specific
        # we should rename them someday
        if limb_tools.tocExists(self.toc_dir):
            return True
        if limb_tools.altoFileCountMatches(self.alto_dir, self.input_files):
            return True
        return False

if __name__ == '__main__':
    
    WaitForOcr( ).begin()
