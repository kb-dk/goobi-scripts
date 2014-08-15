#!/usr/bin/python
# -*- coding: utf-8
import sys, os, os.path, re, traceback, datetime, subprocess
import logging, logging.handlers
from tools import tools

from abc import abstractmethod, ABCMeta

from config.config_reader import ConfigReader
from cli.command_line import CommandLine
from goobi.goobi_communicate import GoobiCommunicate
from goobi.goobi_logger import GoobiLogger

        
class Step( object ):
    """
        Base class for all steps.
        
        This :
            Checks config
            Checks commandline 
            Creates loggers - goobi, file and email.
            
        Additional commandlines:
            detach - if true the step will detach from goobi after the basic 
                checks are done, the file continues to be run but Goobi 
                no longer watches it or moves to another step.
            auto_complete - if true and the step completes fine, the step will 
                be closed.
            auto_report_problem - auto return to another step if this step 
                fails. Equal to the stepname (step_id={stepid} is also needed 
                to report to a previous step)
            debug - override config debug value to display additional 
                information and output more information.
        
        First define the setup(s) function.
            give the step a name, 
            s.name="my step name"
        Then specify the default config section for this step, 
            s.config_main_section='uuid_insert'
        Then specify the set of essential config sections this step needs to 
            run, s.essential_config_sections=set( ["sec1","sec2"] )
        Then specify the dict of essential commandlin values with a type 
            (number, file, folder or string), 
            s.essential_commandlines = {"process_id" : "number", 
                                        "metafile" : "file",
                                        "tiff_path" : "folder",
                                        "step_name" : "string" }
            
        Now put your code in the step() function. 
            You can acess self.commandline and self.config. 
            Use error(), warning(), info() and debug() to log to the logger.
        
        You can use other commandline parameters for the process id and step 
            id by overwriting cli_process_id_arg and cli_step_id_arg in the 
            child class
    """
    
    # Types for commandlines
    type_string = "string"
    type_number = "number"
    type_file = "file"
    type_folder = "folder"
    type_ignore = "ignore"
    
    # TODO: Switch types to these: (Use with Step.CLTYPE.STRING
    class CLTYPE:
        STRING = "string"
        NUMBER = "number"
        FILE = "file"
        FOLDER = "folder"
        IGNORE = "ignore"

    
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def setup(self,_): pass
    
    @abstractmethod
    def step(self,_): pass
    
        
    def __init__( self ) :
    
        # Default names for essential settings
        self.cli_process_id_arg = "process_id"
        self.cli_step_id_arg = "step_id"
        self.cli_auto_complete_arg = 'auto_complete'
        self.cli_auto_report_problem_arg = "auto_report_problem"
        self.cli_detach_arg = "detach"
        self.cli_debug_arg = "debug"
        self.cli_step_name_arg = 'step_name'
        
        self.config_general_section = "general"
        self.config_goobi_section = 'goobi'
        
        self.name = ""
        self.system_config_path = ''
        self.config_path = ''
        self.config_main_section = "" # Info for this particular step
        
        # General section and goobi section must always be present
        # These are placed in a system specific config file
        self.essential_system_config_sections = set ([self.config_general_section,
                                                      self.config_goobi_section])
        # Config is specific for workflow scripts
        self.essential_config_sections = set( [] )
        # Process id must always be present
        self.essential_commandlines = {self.cli_process_id_arg: "number"}
        
        self.command_line = None
        self.config = None
        
        self.glogger = None
        self.glogger_handlers = {}
        
        self.debug = False
        
        #TODO: add this to config and load it in this init.
        self.print_debug = False # Whether to "print" debug msgs
        self.auto_complete = False
        self.detach = False
        
        # Run setup for specific workflow script
        self.setup()
        
        # Update 
        self.essential_config_sections.update( [self.config_main_section] ) 
        # We need to make sure we have a full path to our config file
        #if self.cli_config_path_arg not in self.essential_commandlines.keys() :
        #    self.essential_commandlines[self.cli_config_path_arg] = "file"
        
        #
        # Get command line parameters (want to pass process_id to log if we have it)        
        self.command_line, error_command_line = \
            self.getCommandLine( must_have=self.essential_commandlines )
        #
        # Load system configuration information
        if self.system_config_path == '':
            if not self.command_line.has("system_config_path"):
                self.system_config_path = '/opt/digiverso/goobi/scripts/kb/config/config.ini'
            else:
                self.system_config_path = self.command_line.system_config_path 
        self.getConfig(self.system_config_path,
                       must_have=self.essential_system_config_sections )
        
        # Load config specific for step
        if self.command_line.has("config_path"):
            # root is the one above the folder "goobi" where goobi_step.py 
            # is located
            cwd = os.path.dirname(os.path.realpath(__file__))
            root = os.path.split(cwd)[0]
            
            config_path = self.command_line.get('config_path')
            alt_config_path = os.path.join(root,config_path)
            if (os.path.exists(config_path) and os.path.isfile(config_path)):
                self.config_path = config_path
            elif (os.path.exists(alt_config_path) and
                  os.path.isfile(alt_config_path)):
                # config_path is a relative path from current working dir
                self.config_path = alt_config_path
            else:
                error = ('config_path from command line does not exist '
                         'or is not a valid file. Neither {0} or {1}.')
                error = error.format(config_path,alt_config_path)
                raise IOError(error)
        
        if not self.config_path == '':
            self.info_message('config_path: '+self.config_path)
            self.getConfig(self.config_path,
                           must_have=self.essential_config_sections )
        
        if self.command_line.has(self.cli_step_name_arg):
            self.name = self.command_line.get(self.cli_step_name_arg)
        #
        # Are we debugging?
        self.debug = self.debugging()
            
        if self.command_line and self.command_line.has(self.cli_debug_arg) :
            self.debug = not ( self.command_line.debug.lower() == "false" )
            # Override config setting at commandline. (if it says anything but false turn it on.)
        if self.debug:
            print(self.name + ": Debugging ON")
        # Create out logger
        logger_name = self.name.replace(' ','').lower()
        self.glogger, error = self.getLoggingSystems(self.config,
                                                     self.config_main_section,
                                                     self.command_line,
                                                     self.debug,
                                                     logger_name + "_logger")
        if error:
            self.exit( error,self.glogger )
        if self.command_line.has( self.cli_process_id_arg ):
            self.goobi_com = GoobiCommunicate(self.config.goobi.host,
                                              self.config.goobi.passcode,
                                              self.debug,
                                              process_id = self.command_line.get(self.cli_process_id_arg)
                                              )
            #
        # Check Commandline parameters
        if error_command_line:
            self.exit( error_command_line,self.glogger )
        #
        # Use auto_complete if script needs to output to goobi.
        # Goobi won't self complete automatic task if script outputs to goobi.
        if self.command_line.has(self.cli_auto_complete_arg):
            self.auto_complete = \
                (self.command_line.auto_complete.lower() == "true" )

        if self.command_line.has( self.cli_detach_arg ) :
            self.detach = ( self.command_line.detach.lower() == "true" )
        
        # If self.cli_auto_report_problem_arg is sit in command_line the value
        # is the step name that should be reported back to.
        if self.command_line.has(self.cli_auto_report_problem_arg):
            self.auto_report_problem = self.command_line.get(
                                            self.cli_auto_report_problem_arg )
        else:
            self.auto_report_problem = None
        #
        # Pass message back to Goobi to say everything looks fine and start process.
        update_message = "Basic checks complete, "
        update_message += 'beginning main process of step "' + self.name + '" - '
        update_message += 'DETACH:' + ( "ON" if self.detach else "OFF" )
        update_message += ', AUTO-COMPLETE:' + ( "ON" if self.auto_complete else "OFF" ) # if successful
        update_message += ', REPORT-PROBLEM:' + ( "ON" if self.auto_report_problem else "OFF" ) # if unsuccessful
        update_message += ', DEBUG:' + ( "ON" if self.debug else "OFF" ) + "."
        self.debug_message( update_message )


    def begin(self) :
        if self.detach:
            # Detach from goobi.
            self.detachSelf()
        error = None
        try:
            error = self.step()
        except Exception as e:
            try:
                trace = traceback.format_exc()
                self.error_message('Exception occured in ' + self.name +\
                                   ' :- ' + e.message + ". Trace: " + trace )
            except:
                self.error_message( 'Exception occured in ' + self.name  )
            raise
        if not error :
            self.info_message( 'Completed ' + self.name )
            if self.auto_complete:
                self.closeStep()
        else:
            if self.auto_report_problem:
                error_msg = ('Error occured in {0}. Sending task back to {1}')
                error_msg = error_msg.format(self.name,
                                             self.auto_report_problem) 
                self.error_message(error_msg)
                self.error_message(error)
                self.reportToStep( error )
            else:
                error_msg = ('{0} failed. Error message: "{1}"')
                error_msg = error_msg.format(self.name,error)
                self.error_message(error_msg)
        return (error == None)
    
    def reportToStep( self, message ):
        """
            Pass control back to a previous step
        """
        if self.auto_report_problem is None:
            return
        try:
            step_id = self.command_line.get(self.cli_step_id_arg)
        except KeyError:
            msg = 'Failed to report this problem to a previous step.'+\
                  ' In ' + self.name + ' ' + self.cli_step_id_arg +\
                  ' was not passed into command line.'
            self.error(msg)
            raise KeyError(msg)
        prev_step_name = self.auto_report_problem
        goobi_com = GoobiCommunicate(self.config.goobi.host,
                                     self.config.goobi.passcode,
                                     self.debug )
        goobi_com.reportToPrevStep(step_id,
                                   prev_step_name,
                                   message )
        
    def closeStep(self):
        '''
        TODO: Document method
        '''
        goobi_com = GoobiCommunicate(self.config.goobi.host,
                                     self.config.goobi.passcode,
                                     self.debug )
        
        if self.command_line.has( self.cli_process_id_arg ) :
            goobi_com.closeStepByProcessId( self.command_line.get( self.cli_process_id_arg ) )
        elif self.command_line.has( self.cli_step_id_arg ) :
            goobi_com.closeStep( self.command_line.get( self.cli_step_id_arg ) )
        else:
            self.info( 'Failed to close this step in ' + self.name + ". Neither " + self.cli_process_id_arg + " or " + self.cli_step_id_arg + " were passed into commandline." )
            
    def exit( self, message,log=None ) :
        # TODO: make this method a nice exit
        ''' Nice exit '''
        print "Exit being called with args: "
        print "Message is {0}".format(str( message))
        print "Log is {0}".format(str(log))
        if log.__class__.__name__  == 'Logger':
            log.error( message )
        else:
            self.glogger.error(message)
        sys.exit(1)
        
    def getConfig( self, config_file, must_have ) :
        # Add self.config so new config settings can be added to old.
        config = ConfigReader(config_file,
                              self.config,
                              overwrite_sections=True)
        does_not_have_sections = []
        for section in must_have:
            if len(section) > 0 and not config.hasSection( section ):
                print "section {0} not found".format(section)
                does_not_have_sections.append( section )
        if does_not_have_sections:
            error = "Error: Config file does not contain sections:- " + ", ".join( does_not_have_sections )
            raise ValueError(error)
        self.config = config
    
    def getConfigSection(self, section, config=None):
        """
           Return section as dictionary if it exists, otherwise raise key error
        """
        value = None
        if config == None:
            config = self.config
        if section in self.config.config.sections():
            value = dict(self.config.config.items(section))
        if value is None:
            error = 'Section {0} not defined in config file.'
            error = error.format(section)
            raise KeyError(error)
        else:
            return value
    
    def getConfigItem( self, key, config=None, section=None ):
        '''
        If section is given, return value for key
        If section is not give, sheck for value in the main section, then 
            fall back to general section
        If key can't be found, raise KeyError
        '''
        
        value = None
        
        if config == None:
            config = self.config
        
        if not section is None:
            if config.hasItem(section, key):
                value = config.item(section, key )
        else:
            if config.hasItem( self.config_main_section, key ) :
                value = config.item( self.config_main_section, key )
            elif config.hasItem( self.config_general_section, key ) :
                value = config.item( self.config_general_section, key )
        if value is None:
            error = '{0} not defined in section {1} in config file.'
            error = error.format(key,
                                 section)
            raise KeyError(error)
        else:
            return value

    def debugging( self) :
        debug = self.getConfigItem( "debug", self.config )
        if not debug:
            debug = False
        return debug
        
    def getCommandLine( self, must_have ) :

        command_line = CommandLine()
        error = None
        
        # check for process_id first as we use it to log - if we have problem report that first
        if not command_line.has( self.cli_process_id_arg ):
            error =     "Error: Command line does not contain a " + self.cli_process_id_arg + "=<VALUE>. This is needed for logging." 
        else :
            value = command_line.get( self.cli_process_id_arg )
            parameter_error = self.checkParameter( self.cli_process_id_arg, 'number', value )
            
            if parameter_error:
                # See if we can recover (so we can report the error )
                result = re.search( r'^\d+', value )
                if result:
                    process_id = result.group()
                    command_line.set( self.cli_process_id_arg, process_id )
                    
                    parameter_error += " Attempted to *guess* correct process_id, found " + str( process_id ) + ". "
                    
            error = parameter_error
                    
        
        # Check other commandlines
        must_have_keys = must_have.keys()
        does_not_have_parameters = []
        for parameter in must_have_keys:
            if parameter != self.cli_process_id_arg:
                if not command_line.has( parameter ):
                    does_not_have_parameters.append( parameter )
                
        if does_not_have_parameters:
            error = (error + " Also, " ) if error else "Error: "
            error += "Command line does not contain - " + "  ".join( [s + "=<VALUE>" for s in does_not_have_parameters] )
        
        else:
            for parameter in must_have_keys:
                if parameter != self.cli_process_id_arg :
                    var_type = must_have[parameter]
                    value = command_line.get( parameter )
                    parameter_error = self.checkParameter( parameter, var_type, value )
                    if parameter_error:
                        error = (error + " " ) if error else "Error: "
                        error += parameter_error + " "
        
        return command_line, error
    
    def checkParameter( self, parameter, var_type, value ) :
        parameter_error = None
        if not value:
            parameter_error = 'Error: Parameter "' + parameter + '" can not be empty.'
            
        else:
            if var_type == Step.type_folder :
                try: 
                    tools.check_folder( value )
                except Exception as e:
                    parameter_error = str(e) 
            elif var_type == Step.type_file :
                try:
                    tools.check_file( value )
                except Exception as e:
                    parameter_error = str(e)
            elif var_type == Step.type_number :
                try:
                    self.checkNumber( value )
                except Exception as e:
                    parameter_error = str(e)
            elif var_type == Step.type_string or var_type == Step.type_ignore:
                parameter_error = None # anything goes.
            else :
                parameter_error = "Command line var_type not recognised. Should be set to folder, file, number, string or ignore."
                
            if parameter_error :
                parameter_error = 'Error: Parameter "' + parameter + '" - ' + parameter_error
        return parameter_error
    
    def checkNumber( self, number ):
        error = None
        
        try:
            float( number )
        except ValueError:
            error = 'Number "' + number + '" is not a number.'

        return error
        
    def getLogger( self, config, id, debug ) :

        logger = logging.getLogger( id )
        
        if debug:
            logger.setLevel( logging.DEBUG )
        else:
            logger.setLevel( logging.INFO )
            
        return logger
            
            
        
    def addRotatingLog( self, config, config_main_section, command_line, logger, debug ):

        error = None
        
        try:
            log_max_bytes = int( self.getConfigItem( "log_max_bytes", config ) )
        except ValueError:
            log_max_bytes = 50000000
        
        try:    
            log_backup_count = int( self.getConfigItem( "log_backup_count", config ) )
        except ValueError:
            log_backup_count = 4
        
        log_file = None
        if self.getConfigItem('log'):
            log_file = self.getConfigItem('log')
        else:
            #TODO: Wrong error message
            return 'Error: Unable to locate log file: ' + log_file
        # Check and create log folder structure
        log_folder = os.path.dirname(log_file)
        parent_log_folder = os.path.dirname(log_folder)
        if not os.path.exists(log_folder):
            if os.path.exists(parent_log_folder):
                os.mkdir(log_folder)
            else:
                err = ('Parent folder ({0}) to log folder {1} does not exist. '
                       'Cannot create logger for log file {2}.')
                err = err.format(parent_log_folder,log_folder,log_file)
                raise IOError(err)
        try:
            rotating_logger_handler = logging.handlers.RotatingFileHandler( log_file, maxBytes=log_max_bytes, backupCount=log_backup_count )
            # Add Process ID to the log
            pid = "unknown"
            if command_line.has( self.cli_process_id_arg ) :
                pid = str( command_line.get(self.cli_process_id_arg) )
            
            rotating_logger_handler.setFormatter( logging.Formatter( "[PID " + pid + '] %(asctime)s (%(levelname)s)   %(message)s') )
            
            if debug :
                rotating_logger_handler.setLevel( logging.DEBUG )
            else:
                rotating_logger_handler.setLevel( logging.INFO )
                
            self.glogger_handlers["rotating"] = rotating_logger_handler
            logger.addHandler( rotating_logger_handler )
            
        except IOError:
            
            error = 'Error: Unable to open log file at : ' + log_file
        
        return error 
        
    def addEmailLog( self, config, config_main_section, logger ):
        
        log_email = self.getConfigItem( "log_email", config )
        
        if log_email :
            
            log_email_subject = self.getConfigItem( "log_email_subject", config )
            if not log_email_subject:
                log_email_subject = "Goobi Error " + self.name
                
            email_logger_handler = logging.handlers.SMTPHandler( "smtp.ox.ac.uk", logger.name + "@goobi.bodleian.ox.ac.uk", log_email, log_email_subject)
            email_logger_handler.setLevel( logging.WARNING )
            
            self.glogger_handlers["email"] = email_logger_handler
            logger.addHandler( email_logger_handler )
        
        
    def getGoobiLogger( self, config, command_line, logger, debug ):
        
        if command_line.has( self.cli_process_id_arg ):
            glogger = GoobiLogger( config.goobi.host, config.goobi.passcode, command_line.get(self.cli_process_id_arg), logger )

            if debug :
                glogger.debugging()
        else:
            glogger = logger
            
        return glogger
        
    def getLoggingSystems( self, config, config_main_section, command_line, debug, id):
        """
            Creating file, email and goobi logging.
            
            just_file is so we can recreate the file logger after we detach 
            the prcess, when we detach we need to close all the open files. 
            The other loggers are unaffected.
        """
        use_email = False
        if self.getConfigItem('log_use_email'):
            use_email = self.getConfigItem('log_use_email')
        use_goobi_gui_log = True
        if self.getConfigItem('log_use_gui_msg'):
            use_goobi_gui_log = self.getConfigItem('log_use_gui_msg')
    #
        # Create our base logger
        logger = self.getLogger( config, id, debug )
        #
        # Add e-mail log in configured
        if use_email:
            self.addEmailLog( config, config_main_section, logger )
        #
        # Add rotary file log if configured
        error = self.addRotatingLog( config, config_main_section, command_line, logger, debug )
        if error:
            return logger, error # Logger will log the error to the email log as the file handler has failed
        #
        # Add logging to process msg windows in goobi-gui if configured
        if use_goobi_gui_log:
            logger = self.getGoobiLogger( config, command_line, logger, debug )
        return logger, None    
    
    def error_message( self, message ):
        self.error( message )
    def error( self, message ):
        if self.glogger:
            self.glogger.error( message )
        self.debuggingPrint( "Error: " + str(message) )
        
    def warning_message( self, message ):
        self.warning( message )
    def warning( self, message ):
        if self.glogger:
            self.glogger.warning( message )
        self.debuggingPrint( "Warning: " + str(message) )
        
    def info_message( self, message ):
        self.info( message )
    def info( self, message ):
        if self.glogger:
            self.glogger.info( message )
        self.debuggingPrint("Info: " + str(message) )
    
    def debug_message( self, message ):
        if self.debug:
            self.debuggingPrint(message)
        
    def debuggingPrint( self, message ):
        if self.glogger:
            self.glogger.debug(message)
        if self.print_debug:
            print("Debug: " + str(message))
        
    def detachSelf(self):
        '''
        TODO: Document
        '''
        # Flush stdout
        sys.stdout.flush()
        
        # Push out error so that Goobi will pause the current step 
        # (if auto_complete was specified the step will continue when finished)
        #        
        sys.stderr.write('Step is continuing in background.'
                         '(This is not an error!).\n"')
        sys.stderr.flush()
        # Close log_handlers (The daemon closes all files, but the logger 
        # doesn't know it's been closed unless you tell it!)
        for log_handler in self.glogger_handlers :
            self.glogger_handlers[log_handler].close()
        # detach this process from whatever started it (probably Goobi, 
        #but could be a shell)
        self.createDaemon()

    def createDaemon(self):
        """
            Detach a process from the controlling terminal and run it in the background as a daemon.
            
            From: http://code.activestate.com/recipes/278731/
        """
        
        # Default daemon parameters.
        # File mode creation mask of the daemon.
        UMASK = 0
        
        # Default working directory for the daemon.
        WORKDIR = "/"

        # Default maximum for the number of available file descriptors.
        MAXFD = 1024

        # The standard I/O file descriptors are redirected to /dev/null by default.
        if ( hasattr(os, "devnull") ):
           REDIRECT_TO = os.devnull
        else:
           REDIRECT_TO = "/dev/null"

        try:
            # Fork a child process so the parent can exit.  This returns control to
            # the command-line or shell.  It also guarantees that the child will not
            # be a process group leader, since the child receives a new process ID
            # and inherits the parent's process group ID.  This step is required
            # to insure that the next call to os.setsid is successful.
            pid = os.fork()
            
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)

        if (pid == 0):    # The first child.
            # To become the session leader of this new session and the process group
            # leader of the new process group, we call os.setsid().  The process is
            # also guaranteed not to have a controlling terminal.
            os.setsid()

            # Is ignoring SIGHUP necessary?
            #
            # It's often suggested that the SIGHUP signal should be ignored before
            # the second fork to avoid premature termination of the process.  The
            # reason is that when the first child terminates, all processes, e.g.
            # the second child, in the orphaned group will be sent a SIGHUP.
            #
            # "However, as part of the session management system, there are exactly
            # two cases where SIGHUP is sent on the death of a process:
            #
            #   1) When the process that dies is the session leader of a session that
            #      is attached to a terminal device, SIGHUP is sent to all processes
            #      in the foreground process group of that terminal device.
            #   2) When the death of a process causes a process group to become
            #      orphaned, and one or more processes in the orphaned group are
            #      stopped, then SIGHUP and SIGCONT are sent to all members of the
            #      orphaned group." [2]
            #
            # The first case can be ignored since the child is guaranteed not to have
            # a controlling terminal.  The second case isn't so easy to dismiss.
            # The process group is orphaned when the first child terminates and
            # POSIX.1 requires that every STOPPED process in an orphaned process
            # group be sent a SIGHUP signal followed by a SIGCONT signal.  Since the
            # second child is not STOPPED though, we can safely forego ignoring the
            # SIGHUP signal.  In any case, there are no ill-effects if it is ignored.
            #
            # import signal           # Set handlers for asynchronous events.
            # signal.signal(signal.SIGHUP, signal.SIG_IGN)

            try:
               #     Fork a second child and exit immediately to prevent zombies.  This
                # causes the second child process to be orphaned, making the init
                # process responsible for its cleanup.  And, since the first child is
                # a session leader without a controlling terminal, it's possible for
                # it to acquire one by opening a terminal in the future (System V-
                # based systems).  This second fork guarantees that the child is no
                # longer a session leader, preventing the daemon from ever acquiring
                # a controlling terminal.
                
                pid = os.fork()    # Fork a second child.
                
            except OSError, e:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)

            if (pid == 0):    # The second child.
                # Since the current working directory may be a mounted filesystem, we
                # avoid the issue of not being able to unmount the filesystem at
                # shutdown time by changing it to the root directory.
                os.chdir(WORKDIR)
                # We probably don't want the file mode creation mask inherited from
                # the parent, so we give the child complete control over permissions.
                os.umask(UMASK)
            else:
                # exit() or _exit()?  See below.
                
                os._exit(0)    # Exit parent (the first child) of the second child.
        else:
        
            # exit() or _exit()?
            # _exit is like exit(), but it doesn't call any functions registered
            # with atexit (and on_exit) or any registered signal handlers.  It also
            # closes any open file descriptors.  Using exit() may cause all stdio
            # streams to be flushed twice and any temporary files may be unexpectedly
            # removed.  It's therefore recommended that child branches of a fork()
            # and the parent branch(es) of a daemon use _exit().
            
            os._exit(0)    # Exit parent of the first child.

        # Close all open file descriptors.  This prevents the child from keeping
        # open any file descriptors inherited from the parent.  There is a variety
        # of methods to accomplish this task.  Three are listed below.
        #
        # Try the system configuration variable, SC_OPEN_MAX, to obtain the maximum
        # number of open file descriptors to close.  If it doesn't exists, use
        # the default value (configurable).
        #
        # try:
        #    maxfd = os.sysconf("SC_OPEN_MAX")
          # except (AttributeError, ValueError):
        #    maxfd = MAXFD
        #
        # OR
        #
        # if (os.sysconf_names.has_key("SC_OPEN_MAX")):
        #    maxfd = os.sysconf("SC_OPEN_MAX")
        # else:
        #    maxfd = MAXFD
        #
        # OR
        #
        # Use the getrlimit method to retrieve the maximum file descriptor number
        # that can be opened by this process.  If there is not limit on the
        # resource, use the default value.
        #
        import resource        # Resource usage information.
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = MAXFD
      
        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:    # ERROR, fd wasn't open to begin with (ignored)
                pass
        
        
        # Redirect the standard I/O file descriptors to the specified file.  Since
        # the daemon has no controlling terminal, most daemons redirect stdin,
        # stdout, and stderr to /dev/null.  This is done to prevent side-effects
        # from reads and writes to the standard I/O file descriptors.

        # This call to open is guaranteed to return the lowest file descriptor,
        # which will be 0 (stdin), since it was closed above.
        #
        os.open(REDIRECT_TO, os.O_RDWR)    # standard input (0)

        # Duplicate standard input to standard output and standard error.
        os.dup2(0, 1)            # standard output (1)
        os.dup2(0, 2)            # standard error (2)
        
        return(0)
