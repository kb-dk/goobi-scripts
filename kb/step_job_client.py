#!/usr/bin/python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''
import socket
import sys
import tools.logging.logger as logger
import os

class StepJobClient() :
    
    def __init__(self):
        log_path = '/opt/digiverso/logs/step_client/' 
        log_level = 'INFO'
        self.logger = logger.setup(log_path,log_level)
        
        
        '''
        sys.argv should be formed with the following arguments
        0: filename for this script
        1: hostname for server: hostname=<string>
        2: port for server: port=<int>
        3: path to the python script to be executed by server
        4...: arguments to the python script to be executed by the server
        
        Lenght of sys.argv must thus be equal or larger than 4 
        '''
        if len(sys.argv) < 4:
            err = ('Arguments to step job server is too short. '
                   'Script call must consist of hostname, port, script to '
                   'execute and finally arguments to script. Call: {0}')
            err = err.format(sys.argv)
            self.logger.error(err)
        arg = sys.argv[1].split('=')
        if len(arg) == 2 and arg[0] == 'hostname':
            self.host =  arg[1]
        else:
            error = 'Step job calls first argument must be "hostname=<string>"'
            self.logger.error(error)
            raise ValueError(error)
        
        arg = sys.argv[2].split('=')
        if len(arg) == 2 and arg[0] == 'port':
            self.port =  int(arg[1])
        else:
            error = 'Step job calls second argument must be "port=<int>"'
            self.logger.error(error)
            raise ValueError(error)
        self.step_job_args = sys.argv[3:]
        self.logger.debug('Arguments: {0}'.format(self.step_job_args))
        
        # TODO: Check job/script: e.g. file exist
        self.step_job_filename = os.path.basename(sys.argv[4])
        msg = 'Sending step job {0} to server'.format(self.step_job_filename)
        self.logger.info(msg)
        
    def sendJobToServer(self):
        '''
        Todo: document this
        Todo: try-catch exceptions and return meaningful response
        '''
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = ' '.join(self.step_job_args)
        self.logger.debug('Send data: {0}'.format(data))
        try:
            # Connect to server and send data
            msg = 'Connecting to server {0}:{1}'
            msg = msg.format(self.host, self.port)
            self.logger.debug(msg)
            sock.connect((self.host, self.port))
            msg = 'Connected to server {0}:{1}'
            msg = msg.format(self.host, self.port)
            self.logger.debug(msg)
            sock.sendall(data + "\n")
            msg = 'Data sent to server {0}:{1} - {2}'
            msg = msg.format(self.host, self.port,data)
            self.logger.debug(msg)
            # Receive data from the server and shut down
            reciept = sock.recv(1024)
            msg = 'Reciept recieved from server {0}:{1} - {2}.'
            msg = msg.format(self.host,self.port,reciept)
            self.logger.debug(msg)
            msg = 'Step job {0} sent to server'.format(self.step_job_filename)
            self.logger.info(msg)
        except Exception as e:
            self.logger.error(str(e))
            return False
        finally:
            sock.close()
        return None
        return True

        #return reciept
if __name__ == '__main__' :
    StepJobClient().sendJobToServer()

    