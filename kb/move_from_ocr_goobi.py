#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
import tools.limb as limb_tools
from tools.errors import DataError, TransferError, TransferTimedOut

class MoveFromOcrToGoobi( Step ):

    def setup(self):
        self.name = 'Flyt filer fra OCR til Goobi'
        self.config_main_section = 'copy_from_ocr'
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'move_invalid_files'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            "process_path" : "folder",
            "process_title" : "string",
            'auto_report_problem' : 'string'
        }

    def step(self):
        '''
        Move pfd's and/or alto's from ocr to goobi
        ''' 
        error = None   
        try:
            self.getVariables()
            # check if files already have been copied:
            if not self.ignore_goobi_folder:
                if self.has_alto:
                    if (limb_tools.alreadyMoved(self.goobi_pdf,self.input_files,
                                                self.goobi_altos,self.valid_exts)):
                        return error
                else:
                    if (limb_tools.alreadyMoved(self.goobi_pdf,self.input_files,
                                                self.valid_exts)):
                        return error

            tools.ensureDirsExist(self.ocr_pdf)
            self.moveFiles(self.ocr_pdf, self.goobi_pdf)

            if self.has_alto:
                tools.ensureDirsExist(self.ocr_altos)
                self.moveFiles(self.ocr_altos, self.goobi_altos)

            # legr: don't think we need similar for ocr - it auto-deletes folders, yes?
            """
            # Delete the empty process folder in LIMBs output folder
            try:
                os.rmdir(self.limb_process_root)
            except OSError:
                msg = 'Process folder "{0}" on LIMB could not be deleted.'
                msg = msg.format(self.limb_process_root)
                self.info_message(msg)
            """
        except ValueError as e:
            return e.strerror
            #return "Could not convert string to int - check config file."
        except (TransferError, TransferTimedOut, IOError) as e:
            return e.strerror
        return None

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        Throws ValueError if config strings cannot be converted to input_files
        Throws IOError if necessary directories could not be found
        '''

        self.has_alto = False
        # legr: Set "ocr_process_root" to correct server (antikva or fraktur), and flag for alto's if it's fraktur
        try:
            ocr_workflow_type = self.getSetting('ocr_workflow_type').lower()
        except KeyError:
            self.error_message('{0} er ikke givet med som variabel til scriptet.'.format('ocr_workflow_type'))
        if ocr_workflow_type == 'antikva':
            # legr: currently antikva on ocr-01
            self.ocr_process_root = os.path.join(self.getConfigItem('ocr_antikva_outputfolder'), self.command_line.process_title)
        elif ocr_workflow_type == 'fraktur':
            # legr: currently fraktur on ocr-02
            self.ocr_process_root = os.path.join(self.getConfigItem('ocr_fraktur_outputfolder'), self.command_line.process_title)
            self.has_alto = True
        else:
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten være '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr_workflow_type',self.name,ocr_workflow_type)
            self.error_message(err)

        # legr: if we do have alto's, define their paths on ocr and goobi server
        if self.has_alto:
            self.ocr_altos = os.path.join(self.ocr_process_root, self.getConfigItem('alto'))
            self.goobi_altos = os.path.join(self.command_line.process_path, 
                self.getConfigItem('metadata_alto_path', None, 'process_folder_structure'))

        # legr: path to pdf's on correct ocr-server
        self.ocr_pdf = os.path.join(self.ocr_process_root, self.getConfigItem('pdf'))

        # legr: paths to optimized bw pdf's and normal color pdf's on goobi-server
        self.goobi_pdf_bw = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_pdf_bw_path', None, 'process_folder_structure'))
        self.goobi_pdf_color = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_pdf_color_path', None, 'process_folder_structure'))

        # legr: we only accepts extensions defined in this list
        self.valid_exts = self.getConfigItem('valid_file_exts',None, self.valid_exts_section).split(';')

        # Get path for input-files in process folder
        process_path = self.command_line.process_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files = os.path.join(process_path,input_files)
        
        # Set flag for ignore if files already have been copied to goobi
        self.ignore_goobi_folder = self.getSetting('ignore_goobi_folder', bool, default=False)
        
        self.retry_wait = int(self.getConfigItem('retry_wait', None, 'copy_from_ocr'))
        self.retry_num = int(self.getConfigItem('retry_num', None, 'copy_from_ocr'))

        # legr: raises an error if a folder doesn't exists ...better to put this in step()?
        if self.has_alto:
            tools.ensureDirsExist(self.goobi_altos, self.goobi_pdf_bw, self.goobi_pdf_color)
        else:
            tools.ensureDirsExist(self.goobi_pdf_bw, self.goobi_pdf_color)

    def moveFiles(self, source_dir, dest_dir):
        '''
        Wrapper around tools method
        Throws TransferError, TransferTimedOut
        '''
        tools.copy_files(source = source_dir,
                         dest = dest_dir,
                         transit = None,
                         delete_original = True,
                         wait_interval = self.retry_wait,
                         max_retries = self.retry_num,
                         logger = self.glogger)
if __name__ == '__main__':    
    MoveFromOcrToGoobi().begin()