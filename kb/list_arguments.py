#!/usr/bin/python
'''
Created on 24/04/2014

@author: jeel
'''
import os

from goobi.goobi_step import Step

class list_arguments( Step ) :

    def setup(self):
    
        self.name = "Print CLI arguments"
        self.config_main_section = "list_arguments"
    
    def step(self):
        debug = self.getConfigItem('debug')
        msg = 'Printing argument names and their values:'
        if debug:
            print(msg)
        self.info(msg)
        for key,value in self.command_line._parameters.items():
            msg = '%s = %s'%(key,value)
            if debug: print(msg)
            self.info(msg)
        msg = 'Current working directory: '+os.getcwd()
        if debug: print(msg)
        self.info(msg)
if __name__ == '__main__' :
    list_arguments().begin()