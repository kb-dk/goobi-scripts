#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os, subprocess
import tools.goobi.metadata as goobi_tools
import tools.tools as tools
from tools.mets import mets_tools
from tools.errors import DataError
from tools.processing import processing
from tools import ojs


class RunOJSImport( Step ):

    def setup(self):
        self.name = 'Publicer på www.tidsskrift.dk'
        self.config_main_section = 'ojs'
        self.essential_config_sections = set( ['ojs'] )
        self.essential_commandlines = {
            'process_id' : 'number',
            'process_path' : 'folder',
            'process_title' : 'string',
            'issn' : 'string'
        }

    def step(self):
        '''
        This script logs into the OJS server
        and runs the PHP script for import 
        of a journal using the OJS XML generated
        '''
        try:
            self.getVariables()
            self.runImport()
        except DataError as e:
            return "Execution halted due to error {0}".format(e.strerror)
        except (RuntimeError, Exception) as e:
            return e
        return None

    def getVariables(self):
        '''
        This script pulls in all the variables
        from the command line and the config file 
        that are necessary for its running.
        Errors in variables will lead to an 
        Exception being thrown.
        We need the ojs server, and user 
        path to the correct dir for the import tool
        path to the correct dir for the xml
        name of the journal and an OJS admin user
        '''
        self.ojs_server = self.getConfigItem('ojs_server')
        self.ojs_server_user = self.getConfigItem('ojs_server_user')
        self.ojs_app_user = self.getConfigItem('ojs_app_user')
        self.tool_path = self.getConfigItem('tool_path')

        # Get path to generate ojs_dir using ISSN API on Tidsskrift.dk
        issn = self.command_line.issn
        self.ojs_journal_path = ojs.getJournalPath(self.ojs_server, issn)
        self.debug_message("Journal path is %s" % self.ojs_journal_path)

        process_path = self.command_line.process_path
        mets_file_name = self.getConfigItem('metadata_goobi_file', None, 'process_files')
        mets_file = os.path.join(process_path, mets_file_name)
        issue_data = mets_tools.getIssueData(mets_file)
        self.volume_title = tools.parseTitle(issue_data['TitleDocMain'])
        self.debug_message("Volume title is %s" % self.volume_title)

        # build the path to the ojs xml file based in the form 
        # <upload_dir>/<journal_name>/<process_name>/<process_name>.xml
        upload_dir = self.getConfigItem('upload_dir').\
            format(self.volume_title, self.command_line.process_title)

        xml_name = "{0}.xml".format(self.command_line.process_title)
        self.xml_path = os.path.join(upload_dir,  xml_name)
        self.debug_message("XML path is %s" % self.xml_path)

    def runImport(self):
        '''
        Using the supplied variables - call the script on the OJS server through ssh
        throws a CalledProcessError if the script failed.

        NOTE - this script depends on the Goobi user (tomcat_user) being able to 
        ssh into the OJS server without password authentication, i.e. through a 
        public/private key setup. See the wiki for more details.
        '''
        login = "{0}@{1}".format(self.ojs_server_user, self.ojs_server)
        cmd = 'ssh {0} sudo php {1} NativeImportExportPlugin import {2} {3} {4}'
        cmd = cmd.format(login,self.tool_path,self.xml_path, self.volume_title, self.ojs_app_user)
        self.debug_message(cmd)
        result = processing.run_cmd(cmd,shell=True,print_output=False,raise_errors=False)
        if (result['erred']) or ('error' in str(result['stderr'])) or ('FEJL' in str(result['stderr'])):
            err = ('Der opstod en fejl ved import af OJS-xml-filen på '
                   ' www.tidsskrift.dk ved kørsel af kommandoen: {0}. '
                   'Fejlen er: {1}.')
            err = err.format(cmd,('stderr:'+result['output']+' output:'+result['output']))
            raise RuntimeError(err)


if __name__ == '__main__':
    
    RunOJSImport().begin()