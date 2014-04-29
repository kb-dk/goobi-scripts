#!/usr/bin/python
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
import tools
import os
import sys
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
        try:
            image_path = self.getImageFolder()
            invalid_path = self.getInvalidFolder()
        except LookupError as e:
            return str(e)
        break_level = self.getBreakLevel()
        valid_exts = self.getValidExts()
        error_level, message = self.checkForErrors(image_path, valid_exts)
        if error_level > 0:
            err_msg = self.moveInvalidFiles(image_path,
                                            invalid_path,
                                            valid_exts)
            if err_msg: error = err_msg
        if error_level > break_level:
            error = message
            if self.debug:
                self.error(message)
                self.error("Error level exceeds break level exiting...")
        return error
    
    def getFolderPath(self,name):
        # TODO: Decide how to return error message to method above
        # E.g. raise exception or tuple (err-bool,err-string,path)
        folder_structure = dict(self.config.config.items(
                                self.folder_structure_section))
        if name not in folder_structure:
            error = '{0} not defined in section {1} in config file {2}'
            error = error.format(name,
                                 self.folder_structure_section,
                                 self.command_line.config_path)
            raise LookupError(error)
        else:
            return folder_structure[name]
                
    def getInvalidFolder(self):
        '''
        Build the destination folder for invalid files
        based on the command line arg + the config path
        if dir does not exist, create it
        exit if we can't create the dir for some reason
        (probably permissions)
        '''
        process_root_path = self.command_line.process_root_path
        #TODO: handle error from getFolerPath. Here or above
        rel_invalid_path = self.getFolderPath('img_invalid_path')
        invalid_path = os.path.join(process_root_path,rel_invalid_path)
        path_exists,error = tools.find_or_create_dir(invalid_path)
        if not path_exists: 
            self.error(error)
            #TODO: raise error correct, so error can be send to prev step
            exit(1)
        else: 
            return invalid_path
    
    def getImageFolder(self):
        '''
        Build the image folder for based on the command line arg 
        + the config path 
        If dir does not exist raise error.
        '''
        process_root_path = self.command_line.process_root_path
        #TODO: handle error from getFolerPath. Here or above
        rel_image_path = self.getFolderPath('img_master_path')
        image_path = os.path.join(process_root_path,rel_image_path)
        if not os.path.exists(image_path): 
            error = '{0} does not exist.'.format(image_path)
            self.error(error)
            #TODO: raise error correct, so error can be send to prev step
            exit(1)
        else: 
            return image_path

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
        for f in os.listdir(folder):
            if os.path.isdir(folder + f):
                message = ('CRITICAL - Subdirectory {0}' 
                            'found in source folder.').format(folder + f)
                error_level= 2
                break
            elif tools.getFileExt(f) not in valid_exts:
                message = ('WARNING - Invalid extension {0} '
                           'found in source folder').format(tools.getFileExt(f))
                error_level = 1
        return error_level, message
    
    def getValidExts(self):
        '''return array of valid file extensions'''
        ext_str = self.getConfigItem('valid_file_exts')
        return ext_str.split(';')
    
    def moveInvalidFiles(self, source_root, dest, valid_exts):
        for f in os.listdir(source_root):
            if tools.getFileExt(f) not in valid_exts:
                self.debug_message("moving file {0}".format(f))
                source_path = os.path.join(source_root,f)
                error = tools.move_file(source_path, dest)
                if error: return error
                #TODO: add to log: names of invalid and moved files 
    
        
if __name__ == '__main__' :
    FileValidator().begin()
