#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''
import socket
from goobi.goobi_step import Step
import os
import sys

class StepJobClient( Step ) :
    
    def setup(self):
        self.config_main_section = 'step_server'
        self.essential_commandlines = {
        }
        
    def step(self):
        '''
        Todo: document this
        Todo: try-catch exceptions and return meaningful response
        '''
        error = None
        try:
            self.getVariables()
            self.send_job_to_server()
            print('Step job placed in queue on step processing server and '
                  'will finish this step when done.')
        except Exception as e:
            error = str(e)
            self.glogger.exception(error)
        return error
        
    def send_job_to_server(self):
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.glogger.debug('Send data: {0}'.format(self.step_job_cmd))
        # Connect to server
        msg = 'Connecting to server {0}:{1}'
        msg = msg.format(self.host, self.port)
        self.glogger.debug(msg)
        sock.connect((self.host, self.port))
        msg = 'Connected to server {0}:{1}'
        msg = msg.format(self.host, self.port)
        self.glogger.debug(msg)
        # Send data to server
        sock.sendall((self.step_job_cmd + "\n").encode()) # Convert to bytes
        msg = 'Data sent to server {0}:{1} - {2}'
        msg = msg.format(self.host, self.port,self.step_job_cmd)
        self.glogger.debug(msg)
        # Receive reciept from the server
        reciept = sock.recv(1024).decode() # comes as bytes
        msg = 'Reciept recieved from server {0}:{1} - {2}.'
        msg = msg.format(self.host,self.port,reciept)
        self.glogger.debug(msg)
        msg = 'Step job {0} sent to server'.format(self.step_job_filename)
        self.glogger.debug(msg)
        # Close socket
        sock.close()
        msg = 'Connection to socket server {0}:{1} has been closed.'
        msg = msg.format(self.host,self.port)
        self.glogger.debug(msg)

    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        
        self.host = self.getConfigItem('host') 
        self.port = int(self.getConfigItem('port'))
        
        # sys.argv consist of 
        #    0: this path to this script
        #    1: "python"
        #    2: path to step job to execute
        #    3: arguments to step job
        step_job_args = sys.argv[1:]
        # First arg must be python, second must be a script that exists
        if len(step_job_args) < 3:
            err = ('Step job command must contain at least python and path to '
                   'script to be executed. Step job command contains: {0}')
            err = err.format(step_job_args)
            raise ValueError(err)
        if not step_job_args[0] == 'python':
            err = ('Step job command must start with "python", but starts with {0}.')
            err = err.format(step_job_args[0])
            raise ValueError(err)
        if not os.path.exists(step_job_args[1]):
            err = ('Second argument in step job command must be a script that '
                   'exist on the goobi server. "{0}" is not a file and/or does '
                   ' not exist.')
            err = err.format(step_job_args[1])
            raise ValueError(err)
        self.step_job_filename = step_job_args[1]
        self.step_job_cmd = ' '.join(step_job_args)
        if 'add_auto_complete=true' in self.step_job_cmd:
            self.step_job_cmd = self.step_job_cmd.replace('add_auto_complete=true',
                                                          'auto_complete=true')
        # Add "auto_complete" to step command
        # Do it this way to avoid "send_job_to_server" to do the auto complete
        
        
if __name__ == '__main__' :
    StepJobClient().begin()
    