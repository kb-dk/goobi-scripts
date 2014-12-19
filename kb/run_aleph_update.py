#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os, subprocess
import tools.goobi.metadata as goobi_tools
import tools.tools as tools
import tools.filesystem.fs as fs
from tools.errors import DataError
from tools.processing import processing


class RunAlephUpdate( Step ):

    def setup(self):
        self.name = 'Kald Aleph script'
        self.config_main_section = 'aleph'
        self.valid_exts_section = 'valid_file_exts'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section,
                                               self.valid_exts_section] )
        self.essential_commandlines = {
            "process_id" : "number",
            "process_path" : "folder",
            "process_title" : "string"
        }

    def step(self):
        try:
            self.getVariables()
            self.runImport()
        except DataError as e:
            return "Execution halted due to error {0}".format(e.strerror)
        except RuntimeError as e:
            return e
        return None

    def getVariables(self):

        # Collect parameters for aleph-script
        process_title = self.command_line.process_title
        process_path = self.command_line.process_path

        # Extract barcode from title 
        if '_' in process_title:
            self.barcode = process_title.split('_')[0]
        else:
            self.barcode = process_title

        # get color_pdf
        self.color_pdf = self.barcode+'_color'+'.pdf'
        
        # get color pdf size
        c_pdf_path = self.getConfigItem('doc_pdf_color_path',section=self.folder_structure_section)
        color_pdf_file = os.path.join(process_path, c_pdf_path)+self.color_pdf
        self.color_pdf_size = fs.getFileSize(color_pdf_file,mb=True)

        # get bw_pdf
        self.bw_pdf = self.barcode+'_bw'+'.pdf'
        
        # get bw_pdf_size
        bw_pdf_path = self.getConfigItem('doc_pdf_bw_path',section=self.folder_structure_section)
        bw_pdf_file = os.path.join(process_path, bw_pdf_path)+self.bw_pdf
        self.bw_pdf_size = fs.getFileSize(bw_pdf_file,mb=True)

        # Get multivolume - assume no if error or different from 'Ja/ja'
        is_multivolume = self.getSetting('is_multivolume',var_type = bool, default = False)
        if is_multivolume:
            self.multivolumes = 'multivolumes'
        else:
            self.multivolumes = ''

        # get user and server from config to run the script
        self.aleph_server_user = self.getSetting('aleph_server_user')
        self.aleph_server = self.getSetting('aleph_server')


    def runImport(self):
        '''
        NOTE - this script depends on the Goobi user (tomcat_user) being able to 
        ssh into the aleph server without password authentication, i.e. through a 
        public/private key setup. See the wiki for more details.
        '''

        # Build parameters to be send with call to aleph script
        barcode      = 'barcode={0} '.format(self.barcode)
        color        = 'color={0},{1} '.format(self.color_pdf, round(self.color_pdf_size))
        blackwhite   = 'blackwhite={0},{1} '.format(self.bw_pdf, round(self.bw_pdf_size))
        multivolumes = '{0}'.format(self.multivolumes) 
        login        = "{0}@{1}".format(self.aleph_server_user, self.aleph_server)
        script_path  = '/kb/bin/digitization_item.csh'
        parameters   = barcode+color+blackwhite+multivolumes
        cmd          = 'ssh {0} {1} {2}'.format(login,script_path,parameters)
        # Call aleph script
        result = processing.run_cmd(cmd,shell=True,print_output=False,raise_errors=False)
        if result['erred'] or 'error' in str(result['stderr']):
            err = ('Der opstod en fejl ved kald af aleph-scriptet '
                    ' ved koersel af kommandoen: {0}. '
                    'Fejlen er: {1}.')
            err = err.format(cmd,('stderr:'+result['output']+' output:'+result['output']))
            raise RuntimeError(err)
      

if __name__ == '__main__':
    
    RunAlephUpdate().begin()