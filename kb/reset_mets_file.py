#!/usr/bin/env python
# -*- coding: utf-8

import os
from goobi.goobi_step import Step
from tools.mets import reset


class ResetMetsFile(Step):
    def setup(self):
        self.name = 'Nulstil METS-fil til initielle indstillinger'
        self.config_main_section = 'reset_mets_file'
        self.essential_config_sections = {'process_folder_structure', 'process_files'}
        self.essential_commandlines = {'process_path': 'folder'}

    def step(self):
        error = None
        try:
            self.get_variables()
            self.check_paths()
            self.reset_mets_file()
        except ValueError as e:
            error = e
        except IOError as e:
            error = e.strerror
        return error

    def get_variables(self):
        """
        This method pulls in all the variables
        from the command line and the config file
        that are necessary for its running.
        We need a path to our toc file, our meta.xml
        and a link to our DBC data service (eXist API).
        Errors in variables will lead to an
        Exception being thrown.
        """
        self.meta_file = os.path.join(
            self.command_line.process_path,
            self.getConfigItem('metadata_goobi_file', section='process_files')
        )

    def check_paths(self):
        """
        Check if the file meta.xml exist and check if there are files in
        master_orig folder.
        """
        if not os.path.exists(self.meta_file):
            err = '{0} does not exist.'.format(self.meta_file)
            raise OSError(err)

    def reset_mets_file(self):
        """
        Reset METS-file (Goobi's meta.xml) to initial state, so the process can be re-run
        """
        reset.reset_mets_file(self.command_line.process_path)

if __name__ == '__main__':
    ResetMetsFile().begin()
