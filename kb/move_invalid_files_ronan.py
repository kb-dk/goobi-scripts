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
import os, sys
from goobi.goobi_step import Step


class FileValidator( Step ) :

    def setup(self):
    
        self.name = "Move invalid files"
        
        self.config_main_section = "move_invalid_files"
        self.essential_config_sections = set( [] )
        self.essential_commandlines = {
            "process_id":"number", 
            "image_path":"folder",
            "root_path":"folder"
        }

    def step(self):
        source_folder, sourceOk = tools.fix_path(self.command_line.image_path, True)
        dest_folder = self.getDestinationFolder()
        break_level = self.getBreakLevel()
        valid_exts = self.getValidExts()
        error_level, message = self.checkForErrors(source_folder, valid_exts)
        
        if error_level > break_level:
            self.error(message)
            self.error("Error level exceeds break level exiting...")
            sys.exit(1)
        else:
            self.moveInvalidFiles(source_folder, dest_folder, valid_exts)

    # Build the destination folder for invalid files
    # based on the command line arg + the config path
    # if dir does not exist, create it
    # exit if we can't create the dir for some reason
    # (probably permissions)
    def getDestinationFolder(self):
        invalid_root, rootOk = tools.fix_path(self.command_line.root_path, True)
        invalid_folder, folderOk = tools.fix_path(self.getConfigItem('invalid_folder'), True)
        invalid_destination, destOk = tools.fix_path(invalid_root + invalid_folder, True)
        destination_exists = tools.find_or_create_dir(invalid_destination)
        if not destination_exists: 
            self.error("could not create destination folder {0}".format(invalid_destination))
            exit(1)
        else: 
            return invalid_destination


    def getBreakLevel(self):
        return int(self.getConfigItem('break_on_errors'))

    # Check to see if source folder contains any errors
    # return 1 for minor errors, 2 for serious errors, 3 for critical errors
    def checkForErrors(self, folder, valid_exts):
        error_level = 0
        message = ''
        for f in os.listdir(folder):
            if os.path.isdir(folder + f):
                message = "CRITICAL - Subdirectory {0} found in source folder.".format(folder + f)
                error_level= 2
                break
            elif self.getFileExt(f) not in valid_exts:
                message = "WARNING - Invalid extension \"{0}\" found in source folder".format(self.getFileExt(f))
                error_level = 1
        
        return error_level, message

    # return array of valid file extensions
    def getValidExts(self):
        ext_str = self.getConfigItem('valid_file_exts')
        return ext_str.split(';')

    def getFileExt(self, name):
        return name.split('.')[-1]

    
    def moveInvalidFiles(self, source, dest, valid_exts):
        for f in os.listdir(source):
            if self.getFileExt(f) not in valid_exts:
                self.info("moving file {0}".format(f))
                tools.move_file(source + f, dest)
    
    def step_jeppe(self):
        """
            This just tests the step code
            
            Try using, debug, auto_complete, detach and report_problem on commandline
        """
        error = None
        
        # Load root and image path correctly
        root,error = tools.fix_path(self.command_line.process_root_path,
                                    True,
                                    self.glogger)
        if error:
            return error        
        orig_image_path,error = tools.fix_path(self.command_line.orig_image_path,
                                          True,
                                          self.glogger)
        if error:
            return error
        
        # Load path to invalid files 
        folder_for_invalid_files_var = 'folder_for_invalid_files'
        if self.getConfigItem(folder_for_invalid_files_var):
            folder_for_invalid_files = root + \
                self.getConfigItem(folder_for_invalid_files_var)
        else:
            msg = folder_for_invalid_files_var +\
                ' could not be found in config file.'
            return msg
        error = tools.create_folder(folder_for_invalid_files)
        if error: return error
        
        # Load valid file names from config file
        valid_file_exts_var = "valid_file_exts"
        if self.getConfigItem(valid_file_exts_var):
            valid_file_exts_str = self.getConfigItem(valid_file_exts_var)
        else:
            msg = valid_file_exts_var + ' could not be found in config file.'
            return msg
        # Parse valid file names: "jpeg;jpg" => ['jpeg','jpg']
        valid_file_exts = valid_file_exts_str.split(';')
        
        message = 'Validating image files.'
        self.info_message(message)
        for c in os.listdir(orig_image_path):
            #TODO: check if c is dir
            if os.path.isfile(orig_image_path+c) and \
                    c[c.rfind('.')+1:] not in valid_file_exts:
                error = tools.move_file(orig_image_path+c,folder_for_invalid_files)
                if error: return error
                message = 'File '+c+' not valid. Moved to invalid folder: '+\
                    folder_for_invalid_files
                self.info_message(message)
            else:
                message = 'File '+c+' is valid.'
                self.info_message(message)
        return error   
        
if __name__ == '__main__' :
    FileValidator().begin()
