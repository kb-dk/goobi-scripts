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
        self.config_main_section = 'move_from_ocr'
        self.folder_structure_section = 'process_folder_structure'
        self.valid_exts_section = 'valid_file_exts'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            "process_path" : "folder",
            "process_title" : "string",
            #'auto_report_problem' : 'string'
        }

    def step(self):
        '''
        Move pfd's and/or alto's from ocr to goobi
        ''' 
        error = None   
        try:
            self.getVariables()

            tools.ensureDirsExist(self.ocr_pdf)
            self.moveFiles(self.ocr_pdf, self.goobi_pdf_bw)
            print('moveFrom ', self.ocr_pdf ,' moveTo ', self.goobi_pdf_bw)

            # legr: don't think we need similar for ocr - it auto-deletes folders, yes?

            # Delete the empty process folder in OCRs output folder
            try:
                os.rmdir(self.ocr_pdf)
            except OSError:
                msg = 'Process folder "{0}" on ocr could not be deleted.'
                msg = msg.format(self.ocr_pdf)
                self.info_message(msg)
        except ValueError as e:
            error = str(e)
            #return "Could not convert string to int - check config file."
        except (TransferError, TransferTimedOut, IOError) as e:
            error = str(e)
        except Exception as e:
            error = str(e)
        return error

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        Throws ValueError if config strings cannot be converted to input_files
        Throws IOError if necessary directories could not be found
        '''

        # legr: Choose correct ocr server
        # Antikva server: /mnt/ocr-01/OutFolder/dod-output/(process_title)
        # Fraktur server: /mnt/ocr-02/OutFolder/dod-output/(process_title)
        try:
            ocr_workflow_type = self.getSetting('ocr_workflow_type').lower()
        except KeyError:
            self.error_message('{0} er ikke givet med som variabel til scriptet.'.format('ocr_workflow_type'))
        if ocr_workflow_type == 'antikva':
            # legr: currently antikva on ocr-01
            self.ocr_process_root = self.getConfigItem('ocr_antikva_outputfolder')
        elif ocr_workflow_type == 'fraktur':
            # legr: currently fraktur on ocr-02
            self.ocr_process_root = self.getConfigItem('ocr_fraktur_outputfolder')
        else:
            err = ('Variablen "{0}" fra kaldet af "{1}" skal enten være '
                   '"fraktur" eller "antikva", men er pt. "{2}".')
            err = err.format('ocr_workflow_type',self.name,ocr_workflow_type)
            raise Exception(err)
        self.ocr_pdf = os.path.join(self.ocr_process_root, self.command_line.process_title)

        # legr: paths to pdf'son goobi-server
        self.goobi_pdf_bw = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_pdf_bw_path', None, 'process_folder_structure'))

        self.retry_wait = int(self.getConfigItem('retry_wait'))
        self.retry_num = int(self.getConfigItem('retry_num'))

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