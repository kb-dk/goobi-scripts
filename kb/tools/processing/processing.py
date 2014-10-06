#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 20/06/2014

@author: jeel
'''
import subprocess
import time
import signal
import os
import shlex

class TimeoutError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class processExe():
    def __init__(self,
                 cmd,
                 shell= False,
                 print_output=False,
                 timeout=None,
                 raise_errors=True):
        self.cmd = cmd
        self.shell = shell
        self.print_output = print_output
        self.timeout=timeout
        self.raise_errors = raise_errors
    
    def _start_process(self):
        return subprocess.Popen(self.cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                preexec_fn=os.setsid, #to call sigterm to process
                                shell=self.shell)

    def run(self):
        # Todo add this one to get better output from run
        retval = {'output': None,
                  'timedout': False,
                  'erred': False,
                  'stdout': None,
                  'stderr':None,
                  'cmd':self.cmd}
        try:
            process = self._start_process()
        except Exception as e:
            raise e
        try:
            error_code = process.wait(self.timeout)
        except subprocess.TimeoutExpired:
            # Kill whole group - needed because shell is true
            # Works in linux 
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate()
            msg = 'Process "{0}" timeout after {1} sec. Stdout: {2}. Stderr: {3}'
            msg = msg.format(shlex.split(self.cmd)[0],self.timeout,stdout,stderr)
            if self.raise_errors:
                raise TimeoutError(msg)
            else:
                retval['timedout'] = True
                retval['output'] = msg
                return retval
        stdout, stderr = process.communicate()
        output = 'Stdout: {0}. Stderr: {1}'.format(stdout, stderr)
        if error_code > 0:
            err = 'Process "{0}" failed with error code {1}. Process output was: {2}.'
            err = err.format(self.cmd,error_code,output)
            if self.raise_errors:
                raise IOError(err)
            else:
                retval['erred'] = True
                retval['output'] = err
        retval['output'] = output
        retval['stdout'] = stdout
        retval['stderr'] = stderr
        if self.print_output:
            print(output)
        return retval

    
def run_cmd(cmd,shell=False,print_output=False,timeout=None,raise_errors=True):
    pe = processExe(cmd,shell,print_output,timeout,raise_errors)
    return pe.run()

