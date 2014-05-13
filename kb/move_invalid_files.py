#!/usr/bin/python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''

'''
    Tester
    
    Test the python step code.
    
    Command line:
        needs: process_id,  and tiff_folder
        optional: auto_complete, step_id, correction_step_name
    
    Relies on steps:
        none
    
    Example run : 
        In Goobi:  
            /usr/bin/python /opt/digiverso/goobi/scripts/bdlss/step_tester.py process_id={processid} tiff_folder={tifpath}
        From command line:
            sudo -u tomcat6 python step_tester.py process_id=54 tiff_folder=/opt/digiverso/goobi/metadata/54/images/_7654321_tif

'''
from tools import tools
import os
from goobi.goobi_step import Step


class FileValidator( Step ) :

    def setup(self):
    
        self.name = "Move invalid files"
        self.config_main_section = "move_invalid_files"
        self.essential_config_sections = set( [] )
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            "process_root_path":"folder"
        }

    def step(self):
        error = None
        self.getVariables()
        error_level, message = self.checkForErrors(self.image_path,
                                                   self.valid_exts)
        
        if error_level > self.break_level:
            error = message
            self.debug_message(error)
            self.debug_message("Error level exceeds break level exiting...")
        if error_level > 0:
            self.moveInvalidFiles(self.image_path,
                                  self.invalid_path,
                                  self.valid_exts)
        return error
    
    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        self.break_level = self.getBreakLevel()
        self.err_msg_no_files_added = self.getConfigItem('err_msg_no_files_added')
        self.err_msg_invalid_files = self.getConfigItem('err_msg_invalid_files')
        self.err_msg_contains_folders = self.getConfigItem('err_msg_contains_folders')
        self.valid_exts = self.getConfigItem('valid_file_exts').split(';')
        
        rel_invalid_path = self.getConfigItem('img_invalid_path',
                                                   None,
                                                   self.folder_structure_section)
        self.invalid_path = os.path.join(self.command_line.process_root_path,
                                         rel_invalid_path)
        tools.find_or_create_dir(self.invalid_path)
        
        rel_image_path = self.getConfigItem('img_master_path',
                                            None,
                                            self.folder_structure_section) 
        self.image_path = os.path.join(self.command_line.process_root_path,
                                       rel_image_path)
    
    def getBreakLevel(self):
        '''Our break level is used to figure out what errors to tolerate'''
        return int(self.getConfigItem('break_on_errors'))
    
    def checkForErrors(self, folder, valid_exts):
        '''
        Check to see if source folder contains any errors
        return 1 for minor errors, 2 for serious errors, 3 for critical errors
        '''
        error_level = 0
        message = ''
        if len(os.listdir(folder)) == 0:
            message = self.err_msg_no_files_added
            error_level= 2
        else:
            for f in os.listdir(folder):
                if os.path.isdir(folder + f):
                    message = self.err_msg_contains_folder
                    #('CRITICAL - Subdirectory {0} found in source folder.').format(folder + f)
                    error_level= 2
                    break
                elif tools.getFileExt(f) not in valid_exts:
                    #TODO: ��� gives error, decode/encode
                    #UnicodeEncodeError: 'ascii' codec can't encode character u'\xe6' in position 34: ordinal not in range(128)
                    err_file_msg = '{0} is not a valid file and will be removed.'.format(f)
                    self.debug_message(err_file_msg)
                    message =  self.err_msg_invalid_files
                    #('WARNING - Invalid extension {0} found in source folder').format(tools.getFileExt(f))
                    error_level = 1
        return error_level, message
    
    def moveInvalidFiles(self, source_root, dest, valid_exts):
        for f in os.listdir(source_root):
            if tools.getFileExt(f) not in valid_exts:
                self.debug_message("moving file {0}".format(f))
                source_path = os.path.join(source_root,f)
                tools.move_file(source_path, dest,self.glogger)
        
if __name__ == '__main__' :
    FileValidator().begin()
