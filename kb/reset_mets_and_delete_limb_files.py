#!/usr/bin/env python
# -*- coding: utf-8

import os
from goobi.goobi_step import Step
from tools.mets import reset
from tools.filesystem import fs


class ResetMetsAndDeleteLimbFiles(Step):
    def setup(self):
        self.name = 'Reset METS-fil og fjern Limb-producerede filer'
        self.config_main_section = 'reset_mets_file'
        self.essential_config_sections = {'process_folder_structure', 'process_files'}
        self.essential_commandlines = {'process_path': 'folder'}

    def step(self):
        error = None
        try:
            self.get_variables()
            # Check if we have a METS file (meta.xml)
            self.check_paths()
            # Clean up the METS file (meta.xml)
            reset.reset_mets_file(self.command_line.process_path)
            # Clear files from Limb (if any)
            fs.clear_folder(self.goobi_altos)
            fs.clear_folder(self.goobi_toc)
            fs.clear_folder(self.goobi_pdf)
        except ValueError as e:
            error = e
        except IOError as e:
            error = e.strerror
        return error

    def get_variables(self):
        # Path to the meta.xml file
        self.meta_file = os.path.join(
            self.command_line.process_path,
            self.getConfigItem('metadata_goobi_file', section='process_files'))
        # Path to the alto files produced by Limb
        self.goobi_altos = os.path.join(
            self.command_line.process_path,
            self.getConfigItem('metadata_alto_path', section='process_folder_structure'))
        # Path to the TOC file produced by Limb
        self.goobi_toc = os.path.join(
            self.command_line.process_path,
            self.getConfigItem('metadata_toc_path', section='process_folder_structure'))
        # Path to the PDF file produced by Limb
        self.goobi_pdf = os.path.join(
            self.command_line.process_path,
            self.getConfigItem('doc_limbpdf_path', section='process_folder_structure'))

    def check_paths(self):
        # Check if the file meta.xml exist
        if not os.path.exists(self.meta_file):
            err = '{0} does not exist.'.format(self.meta_file)
            raise OSError(err)

if __name__ == '__main__':
    ResetMetsAndDeleteLimbFiles().begin()
