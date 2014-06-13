from goobi.goobi_step import Step
import tools.tools as tools
import tools.limb as limb_tools
import os, time

class WaitForLimb( Step ):

    def setup(self):
        self.name = 'Wait for LIMB'
        self.config_main_section = 'limb_output'
        self.folder_structure_section = 'process_folder_structure'
        self.essential_config_sections.update([self.folder_structure_section, 
                                               self.folder_structure_section] )
        self.essential_commandlines = {
            'process_id' : 'number',
            'process_path' : 'folder',
            'auto_report_problem' : 'string',
            'step_id' : 'number'
        }
    
        
    def step(self):
        '''
        This script's role is to wait until
        LIMB processing is complete before finishing.
        In the event of a timeout, it reports back to 
        previous step before exiting.
        '''
        error = None
        retry_counter = 0
        try:
            self.getVariables()
            # First check if files already have been copied to dest
            if (not self.ignore_dest and 
                limb_tools.alreadyMoved(self.goobi_toc,self.goobi_pdf,
                                        self.input_files,self.goobi_altos)):
                return error
            # keep on retrying for the given number of attempts
            while retry_counter < self.retry_num:
                
                if self.limbIsReady():
                    msg = ('LIMB output is ready - exiting.')
                    self.debug_message(msg)
                    return None # this is the only successful exit possible
                else:
                    # if they haven't arrived, sit and wait for a while
                    msg = ('LIMB output not ready - sleeping for {0} seconds...')
                    msg = msg.format(self.retry_wait)
                    self.debug_message(msg)
                    retry_counter += 1
                    time.sleep(self.retry_wait)
        except IOError as e:
            # if we get an IO error we need to crash
            error = ('Error reading from directory {0}')
            error = error.format(e.strerror)
            return error
        except ValueError as e:
            # caused by conversion of non-numeric strings in config to nums
            error = "Invalid config data supplied, error: {0}"
            error = error.format(e.strerror)
            return error
        # if we've gotten this far, we've timed out and need to go back to the previous step
        return "Timed out waiting for LIMB output."

    def getVariables(self):
        '''
        We need the limb_output folder,
        the location of the toc file
        Throws error if any directories are missing
        or if our retry vals are not numbers
        '''
        process_title = self.command_line.process_title
        limb = self.getConfigItem('limb_output')
        alto = self.getConfigItem('alto')
        toc = self.getConfigItem('toc')
        pdf = self.getConfigItem('pdf')
        
        # join paths to create absolute paths
        self.limb_dir = os.path.join(limb, process_title)
        self.alto_dir = os.path.join(self.limb_dir, alto)
        self.toc_dir = os.path.join(self.limb_dir, toc)
        self.pdf_input_dir = os.path.join(self.limb_dir, pdf)
        
        # Set destination for paths
        self.goobi_altos = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_alto_path', None, 'process_folder_structure'))
        self.goobi_toc = os.path.join(self.command_line.process_path, 
            self.getConfigItem('metadata_toc_path', None, 'process_folder_structure'))
        self.goobi_pdf = os.path.join(self.command_line.process_path, 
            self.getConfigItem('doc_limbpdf_path', None, 'process_folder_structure'))
                
        # Get path for input-files in process folder
        process_path = self.command_line.process_path
        input_files = self.getConfigItem('img_master_path',
                                         section= self.folder_structure_section) 
        self.input_files = os.path.join(process_path,input_files)
        
        # Get retry number and retry-wait time
        self.retry_num = int(self.getConfigItem('retry_num'))
        self.retry_wait = int(self.getConfigItem('retry_wait'))
        
        # Set flag for ignore if files already have been copied
        if (self.command_line.has('ignore_dest') and 
            self.command_line.ignore_dest.lower() == True):
            self.ignore_dest = True
        else:
            self.ignore_dest = False
            
        
    def limbIsReady(self):
        '''
        Check to see if LIMB is finished
        return boolean
        '''
        try: 
            # raises error if one of our directories is missing
            tools.ensureDirsExist(self.limb_dir, self.alto_dir, \
                self.toc_dir, self.pdf_input_dir, self.input_files)
        except IOError as e:
            msg = ('One of the output folder from LIMB is not yet created.'
                   ' Waiting for LIMB to be ready. Error: {0}')
            msg = msg.format(e.strerror)
            self.debug_message(msg)
            return False
        if limb_tools.tocExists(self.toc_dir):
            return True
        if limb_tools.altoFileCountMatches(self.alto_dir, self.input_files):
            return True
        return False

if __name__ == '__main__':
    
    WaitForLimb( ).begin()
