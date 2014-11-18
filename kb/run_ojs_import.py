#!/usr/bin/env python
# -*- coding: utf-8
from goobi.goobi_step import Step
import os, subprocess
import tools.goobi.metadata as goobi_tools
import tools.tools as tools
from tools.mets import mets_tools
from tools.errors import DataError
from tools.processing import processing



class RunOJSImport( Step ):

    def setup(self):
        self.step_name = 'Publicer på www.tidsskrift.dk'
        self.config_main_section = 'ojs'
        self.essential_config_sections = set( ['ojs'] )
        self.essential_commandlines = {
            'process_id' : 'number',
            'process_path' : 'folder',
            'process_title' : 'string'
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
        except RuntimeError as e:
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


        process_path = self.command_line.process_path
        mets_file_name = self.getConfigItem('metadata_goobi_file', None, 'process_files')
        mets_file = os.path.join(process_path, mets_file_name)
        issue_data = mets_tools.getIssueData(mets_file)
        
        # Get path to generate ojs_dir -> system means "define it from system variables"
        self.ojs_journal_path = self.getSetting('ojs_journal_path', default='system')
        if self.ojs_journal_path == 'system':
            self.volume_title = tools.parseTitle(issue_data['TitleDocMain'])
            # TODO: write this one back as a property?
            #self.goobi_com.addProperty(self.process_id, 'ojs_journal_path', self.volume_title, overwrite=True)
        else:
            self.volume_title = self.ojs_journal_path
        
        #self.volume_title = tools.parseTitle(issue_data['TitleDocMain'])

        # build the path to the ojs xml file based in the form 
        # <upload_dir>/<journal_name>/<process_name>/<process_name>.xml
        upload_dir = self.getConfigItem('upload_dir').\
            format(self.volume_title, self.command_line.process_title)

        xml_name = "{0}.xml".format(self.command_line.process_title)
        self.xml_path = os.path.join(upload_dir,  xml_name)

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
        result = processing.run_cmd(cmd,shell=True,print_output=False,raise_errors=False)
        if result['erred'] or 'error' in str(result['stderr']):
            err = ('Der opstod en fejl ved import af OJS-xml-filen på '
                   ' www.tidsskrift.dk ved kørsel af kommandoen: {0}. '
                   'Fejlen er: {1}.')
            err = err.format(cmd,('stderr:'+result['output']+' output:'+result['output']))
            raise RuntimeError(err)
        #subprocess.check_call(['ssh', login, 'sudo', 'php', self.tool_path, 
        #    'NativeImportExportPlugin', 'import', self.xml_path, self.volume_title, self.ojs_app_user])
        

if __name__ == '__main__':
    
    RunOJSImport().begin()