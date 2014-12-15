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
        self.config_main_section = 'move_from_ocr'
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'valid_file_exts'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            'process_title' : 'string',
            'process_path' : 'folder',
        }
    
    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
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
            ocr = self.getSetting('ocr_antikva_outputfolder')
        elif ocr_workflow_type == 'fraktur':
            # legr: currently fraktur on ocr-02
            ocr = self.getSetting('ocr_fraktur_outputfolder')
        else:
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten være '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr_workflow_type',self.name,ocr_workflow_type)
            self.error_message(err)

        # join paths to create absolute paths on ocr-server
        self.bw_pdf_input_dir = os.path.join(ocr, process_title)
        
        c_pdf = self.getConfigItem('doc_pdf_color_path',
                                   section=self.folder_structure_section)
        self.color_pdf_input_dir = os.path.join(process_path,c_pdf)
        
        self.valid_exts = self.getConfigItem('valid_file_exts',None, self.valid_exts_section).split(';')
        
        # Get path for input-files in process folder
        process_path = self.command_line.process_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files_dir = os.path.join(process_path,input_files)
        
        pp_img = self.getConfigItem('img_pre_processed_path',
                                         section=self.folder_structure_section) 
        self.preprocessed_input_files = os.path.join(process_path,pp_img)

    
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
            tools.ensureDirsExist(self.bw_pdf_input_dir,
                                  self.color_pdf_input_dir,self.input_files_dir)
            # Check if color pdf is ok
            if not limb_tools.pageCountMatches(self.color_pdf_input_dir,self.input_files_dir,self.valid_exts):
                raise DataError('PDF page count does not match input picture count in "{0}"!'.format(self.color_pdf_input_dir))
            # Check if bw pdf is ok
            if not limb_tools.pageCountMatches(self.bw_pdf_input_dir,self.preprocessed_input_files,self.valid_exts):
                raise DataError('PDF page count does not match input picture count in "{0}"!'.format(self.bw_pdf_input_dir))
        except IOError as e:
            error = "IOError - {0}".format(e.strerror)
        except DataError as e: 
            error = "Validation error - {0}.".format(e.strerror)
        return error
        
if __name__ == '__main__':
    
    ValidateOcrOutput().begin()