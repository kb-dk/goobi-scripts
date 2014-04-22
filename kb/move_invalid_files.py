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
from goobi.goobi_step import Step


class Step_Tester( Step ) :

    def setup(self):
    
        self.name = "Move invalid files"
        
        self.config_main_section = "move_invalid_files"
        self.essential_config_sections = set( [] )
        self.essential_commandlines = {
            "process_id":"number", 
            "orig_image_path":"folder",
            "process_root_path":"folder"
        }
    
    def step(self):
    
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

    from config import config_ini
    Step_Tester( config_ini.file ).begin()
