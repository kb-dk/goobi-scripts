#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
from tools import ojs


class ValidateIssn(Step):
    """
    This Step calls the Journal Path method
    It will return an error message if ISSN
    is invalid or is not found
    """
    def setup(self):
        self.name = 'Validate ISSN'
        self.config_main_section = 'ojs'
        self.essential_config_sections = set( ['ojs'] )

    def step(self):
        try:
            self.getVariables()
            self.validateIssn()
        except Exception as e:
            return e


    def getVariables(self):
        self.server = self.getConfigItem('ojs_server', section='ojs')
        self.issn = self.command_line.issn

    def validateIssn(self):
        self.debug_message("Calling journal_path API with server {0} and issn {1}".format(self.server, self.issn))
        path = ojs.getJournalPath(self.server, self.issn)
        self.debug_message("Journal path %s found!" % path)


if __name__ == '__main__':
    ValidateIssn().begin()
