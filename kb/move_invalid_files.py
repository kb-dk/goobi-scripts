#!/usr/bin/env python
# -*- coding: utf-8
'''
Created on 26/03/2014

@author: jeel
'''

from tools import tools
import os
from goobi.goobi_step import Step


class FileValidator( Step ) :

    def setup(self):
    
        self.name = "Validering af importerede filer"
        self.config_main_section = "validate_image_files"
        self.valid_file_exts_section = 'valid_file_exts'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections = set( [] )
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.valid_file_exts_section] )
        self.essential_commandlines = {
            "process_path":"folder"
        }

    def step(self):
        error = None
        self.getVariables()
        try:
            error_level, message = self.checkForErrors(self.image_path,
                                                       self.valid_exts)
        except Exception as e:
            error = str(e.with_traceback)
            return error
        if error_level > self.break_level:
            error = message
            self.debug_message(error)
            self.debug_message("Error level exceeds break level exiting...")
        if error_level > 0:
            self.moveInvalidFiles(self.invalid_path,self.valid_exts)
        return error
    
    def getVariables(self):
        '''
        Get all required vars from command line + config
        and confirm their existence.
        '''
        process_path = self.command_line.process_path
        self.break_level = self.getBreakLevel()
        v_exts = self.getConfigItem('valid_file_exts',
                                    section = self.valid_file_exts_section)
        self.valid_exts = v_exts.split(';')
        # TODO: Generalize this to take input from its own config section        
        inv_path = self.getConfigItem('img_invalid_path',
                                        section = self.folder_structure_section)
        self.invalid_path = os.path.join(process_path,inv_path)
        tools.find_or_create_dir(self.invalid_path)
        img_path = self.getConfigItem('img_master_path',
                                      section= self.folder_structure_section) 
        self.image_path = os.path.join(process_path,img_path)
        # Set list for storing paths for invalid files to move
        self.invalid_files = []
    
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
        msg = ('Valid file extensions are: {0}'.format(', '.join(valid_exts)))
        self.debug_message(msg)
        if len(os.listdir(folder)) == 0:
            message = 'Ingen filer er blevet uploadet til processen.'
            error_level= 2
        else:
            for f in os.listdir(folder):
                if os.path.isdir(os.path.join(folder,f)):
                    msg = ('Der er blevet uploadet en undermappe til "{0}" '
                           '({1}) hvilket ikke er tilladt.')
                    msg = msg.format(folder,f)
                    self.debug_message(msg)
                    message = msg
                    #('CRITICAL - Subdirectory {0} found in source folder.').format(folder + f)
                    error_level= 2
                    break
                elif tools.getFileExt(f,remove_dot=True) not in valid_exts:
                    if 'Thumbs.db' in f: # removing Thumbs.db is never an error
                        msg = ('Filen "Thumbs.db" er blevet fjernet fra '
                               'billedmappe og lagt i invalid-mappen.')
                        self.info_message(msg)
                        self.invalid_files.append(os.path.join(folder,f))
                        continue
                    #TODO: ��� gives error, decode/encode
                    #UnicodeEncodeError: 'ascii' codec can't encode character u'\xe6' in position 34: ordinal not in range(128)
                    msg = ('Den uploadede fil "{0}" er ikke en tilladt '
                           'filtype. Filen er flyttet til mappen "invalid". '
                           'Hvis filen ikke skal anvendes kan den slettes og '
                           'denne opgave kan afsluttes.')
                    msg = msg.format(f,tools.getFileExt(f,remove_dot=True))
                    self.debug_message(msg)
                    message =  msg
                    #('WARNING - Invalid extension {0} found in source folder').format(tools.getFileExt(f))
                    error_level = 1
                    self.invalid_files.append(os.path.join(folder,f))
                # legr: the following is added to prevent spaces in filenames - which causes trouble later on
                if " " in f:
                    msg = ("Der er mellemrum i filnavnet på de indskannede filer - det er ikke tilladt.")
                    self.debug_message(msg)
                    error_level= 2
                    break

        return error_level, message
    
    def moveInvalidFiles(self, dest, valid_exts):
        for f in self.invalid_files:
            if tools.getFileExt(f) not in valid_exts:
                self.debug_message("moving file {0}".format(os.path.basename(f)))
                tools.move_file(f, dest,self.glogger)
        
if __name__ == '__main__' :
    FileValidator().begin()
