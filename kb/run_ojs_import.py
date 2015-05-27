#!/usr/bin/env python
# -*- coding: utf-8
import os

from goobi.goobi_step import Step
import tools.tools as tools
from tools.mets import mets_tools
from tools.errors import DataError
from tools.processing import processing
from tools import ojs


# noinspection PyPep8Naming
class RunOJSImport(Step):

    def setup(self):
        self.name = 'Publicer på www.tidsskrift.dk'
        self.config_main_section = 'ojs'
        self.essential_config_sections = {'ojs'}
        self.essential_commandlines = {
            'process_id': 'number',
            'process_path': 'folder',
            'process_title': 'string'
            # 'issn': 'string' #  Temporay: issn can't be mandatory until existing processes is finished.
        }

    def step(self):
        """
        This script logs into the OJS server
        and runs the PHP script for import
        of a journal using the OJS XML generated
        """
        try:
            self.getVariables()
            self.runImport()
        except DataError as e:
            return "Execution halted due to error {0}".format(e.strerror)
        except (RuntimeError, Exception) as e:
            return e
        return None

    def getVariables(self):
        """
        This script pulls in all the variables
        from the command line and the config file
        that are necessary for its running.
        Errors in variables will lead to an
        Exception being thrown.
        We need the ojs server, and user
        path to the correct dir for the import tool
        path to the correct dir for the xml
        name of the journal and an OJS admin user
        """
        self.ojs_server = self.getConfigItem('ojs_server')
        self.ojs_server_user = self.getConfigItem('ojs_server_user')
        self.ojs_app_user = self.getConfigItem('ojs_app_user')
        self.tool_path = self.getConfigItem('tool_path')

        # Temporary, new processes should always have issn, so check should be in essential section
        # Initially assume we have an ISSN on the command line
        self.issn_missing = False
        issn = ""
        try:
            # Get path to generate ojs_dir using ISSN API on Tidsskrift.dk
            issn = self.command_line.issn
        except AttributeError as e:
            self.debug_message("Warning, missing attribute. Details: {0}".format(e))
            # We dont have an ISSN on the commandline, so use old code
            self.issn_missing = True

        if self.issn_missing:
            # Old method: generate ojs path from title, or: use property if different from 'system'
            process_path = self.command_line.process_path
            mets_file_name = self.getConfigItem('metadata_goobi_file', None, 'process_files')
            mets_file = os.path.join(process_path, mets_file_name)
            issue_data = mets_tools.getIssueData(mets_file)
            self.ojs_journal_path = self.getSetting('ojs_journal_path', default='system')
            if self.ojs_journal_path == 'system':
                self.volume_title = tools.parseTitle(issue_data['TitleDocMain'])
            else:
                self.volume_title = self.ojs_journal_path
        else:
            # New method: use issn to lookup journal path
            self.ojs_journal_path = ojs.getJournalPath(self.ojs_server, issn)
            self.debug_message("Journal path is %s" % self.ojs_journal_path)

        # build the path to the ojs xml file based in the form
        # <upload_dir>/<journal_name>/<process_name>/<process_name>.xml
        if self.issn_missing:
            # Old Method:
            upload_dir = self.getConfigItem('upload_dir').format(self.volume_title, self.command_line.process_title)
        else:
            # New method:
            upload_dir = self.getConfigItem('upload_dir').format(self.ojs_journal_path, self.command_line.process_title)

        xml_name = "{0}.xml".format(self.command_line.process_title)
        self.xml_path = os.path.join(upload_dir,  xml_name)
        self.debug_message("XML path is %s" % self.xml_path)

    def runImport(self):
        """
        Using the supplied variables - call the script on the OJS server through ssh
        throws a CalledProcessError if the script failed.

        NOTE - this script depends on the Goobi user (tomcat_user) being able to
        ssh into the OJS server without password authentication, i.e. through a
        public/private key setup. See the wiki for more details.

        On the ojs server, disable 'requiretty' in visudo, otherwise, ssh user@server sudo ..., won't work
        """
        login = "{0}@{1}".format(self.ojs_server_user, self.ojs_server)
        cmd = 'ssh {0} sudo php {1} NativeImportExportPlugin import {2} {3} {4}'
        if self.issn_missing:
            # Old method:
            cmd = cmd.format(login, self.tool_path, self.xml_path, self.volume_title, self.ojs_app_user)
        else:
            # New method:
            cmd = cmd.format(login, self.tool_path, self.xml_path, self.ojs_journal_path, self.ojs_app_user)
        self.debug_message(cmd)
        result = processing.run_cmd(cmd, shell=True, print_output=False, raise_errors=False)
        if (result['erred']) or ('error' in str(result['stderr'])) or ('FEJL' in str(result['stderr'])):
            err = ('Der opstod en fejl ved import af OJS-xml-filen på '
                   ' www.tidsskrift.dk ved kørsel af kommandoen: {0}. '
                   'Fejlen er: {1}.')
            err = err.format(cmd, ('stderr:'+result['output']+' output:'+result['output']))
            raise RuntimeError(err)


if __name__ == '__main__':
    RunOJSImport().begin()
