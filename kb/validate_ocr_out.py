#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
from tools import tools
from tools.errors import DataError
import tools.limb as limb_tools
import os
class ValidateOcrOutput( Step ):

    def setup(self):
        self.name = 'Validering af output-filer fra OCR'
        self.config_main_section = 'copy_from_ocr'
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'move_invalid_files'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            'process_title' : 'string',
            'process_path' : 'folder',
            'auto_report_problem' : 'string',
            'step_id' : 'string'
        }
    
    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
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
        pdf = self.getConfigItem('pdf')
        
        # join paths to create absolute paths on ocr-server
        self.ocr_dir = os.path.join(ocr, process_title)
        self.alto_dir = os.path.join(self.ocr_dir, alto)
        self.pdf_input_dir = os.path.join(self.ocr_dir, pdf)
        
        # get paths for output folder on goobi-server
        self.goobi_altos = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_alto_path', None, 'process_folder_structure'))
        self.goobi_pdf = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_pdf_color_path', None, 'process_folder_structure'))
        self.valid_exts = self.getConfigItem('valid_file_exts',None, self.valid_exts_section).split(';')
        # Set flag for ignore if files already have been copied to goobi
        self.ignore_goobi_folder = self.getSetting('ignore_goobi_folder', bool, default=False)
        
        # Get path for input-files in process folder
        process_path = self.command_line.process_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files_dir = os.path.join(process_path,input_files)
        
        # throw Error if one of our directories is missing
        
    
    def step(self):
        '''
        This class checks the output from a LIMB or OCR process
        to see if it matches certain criteria
        Require params process_title from command line
        Other values taken from config.ini
        In the case of errors a message will be returned
        and sent to the previous step.
        '''
        error = None
        try:
            self.getVariables()
            # Check files on goobi-server, if they already have been moved
            if (not self.ignore_goobi_folder and 
                limb_tools.alreadyMoved(self.goobi_toc,self.goobi_pdf,
                                        self.input_files_dir,self.goobi_altos,
                                          self.valid_exts)):
                return error
            tools.ensureDirsExist(self.ocr_dir, self.alto_dir,
                                  self.pdf_input_dir,self.input_files_dir)
            limb_tools.performValidations(self.pdf_input_dir,
                                          self.input_files_dir,self.alto_dir,
                                          self.valid_exts)
            return None
        except IOError as e:
            return "IOError - {0}".format(e.strerror)
        except DataError as e: 
            return "Validation error - {0}.".format(e.strerror)
        
if __name__ == '__main__':
    
    ValidateOcrOutput().begin()