#!/usr/bin/python
'''
Created on 24/04/2014

@author: jeel
'''
import os

from goobi.goobi_step import Step
import tools


class Step_Tester( Step ) :

    def setup(self):
    
        self.name = "List Goobi arguments"
        self.config_main_section = "list_goobi_files"
    
    def step(self):
        for key,value in self.command_line._parameters.items():
            print('%s = %s'%(key,value))
if __name__ == '__main__' :
    Step_Tester().begin()