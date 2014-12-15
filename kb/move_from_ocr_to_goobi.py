#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os
from tools import tools
from tools.errors import TransferError, TransferTimedOut

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
            #===================================================================
            # Move BW-pdf file from OCR-server to Goobi
            #===================================================================
            self.moveFiles(self.ocr_pdf, self.goobi_pdf_bw)
            #===================================================================
            # Rename pdf from OCR-server to required name.
            # E.g. from 1234567890_Antikva.pdf to 1234567890_bw.pdf
            #===================================================================
            # A: get path for existing bw pdf just moved to Goobi
            old_bw_pdf_path = tools.getFirstFileWithExtension(self.goobi_pdf_bw, 'pdf')
            # B: Rename to new path created in "getVariables"
            os.rename(old_bw_pdf_path, self.new_bw_pdf_path)
            #===================================================================
            # Delete empty and now unused output folder on OCR-server 
            #===================================================================
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
        self.process_title = self.command_line.process_title
        process_path = self.command_line.process_path

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
        bw = self.getConfigItem('doc_pdf_bw_path',
                                section= self.folder_structure_section)
        self.goobi_pdf_bw = os.path.join(process_path, bw)

        self.retry_wait = int(self.getConfigItem('retry_wait'))
        self.retry_num = int(self.getConfigItem('retry_num'))
        #=======================================================================
        # Create new name for bw pdf
        #=======================================================================
        if '_' in self.process_title:
                barcode = self.process_title.split('_')[0]
        else: # process not generated with Antikva/Fraktur as suffix
            barcode = self.process_title
        bw_pdf_name = barcode+'_bw.pdf'
        self.new_bw_pdf_path = os.path.join(self.goobi_pdf_bw,bw_pdf_name)

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