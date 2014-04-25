#!/usr/bin/python
'''
Created on 24/04/2014

@author: jeel
'''
import os

from goobi.goobi_step import Step

class Step_Tester( Step ) :

    def setup(self):
    
        self.name = "Print CLI arguments"
        self.config_main_section = "list_arguments"
    
    def step(self):
        print('Printing argument names and their values:')
        for key,value in self.command_line._parameters.items():
            print('%s = %s'%(key,value))
        print('Current working directory: '+os.getcwd())
if __name__ == '__main__' :
    Step_Tester().begin()