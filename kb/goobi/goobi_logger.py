# -*- coding: utf-8 -*-

import datetime
import sys
import time

from goobi.goobi_communicate import GoobiCommunicate


class GoobiLogger():
    """
        Use GoobiCommunicate to log messages to Goobi and to any other python like log you pass in.
    """
    log_format = "{date} PID {process_id:0>8} ({level}) - {message}"
    goobi_log_format = "PID {process_id:0>8} ({level}) - {message}" 
    debugging_on = False
    
    type_info = 'info'
    type_debug = 'debug'
    type_warning = 'warning'
    type_error = 'error'
    type_critical = 'critical'
    type_user = 'user'
    
    
    def __init__( self, 
                  host, 
                  password_token, 
                  process_id, 
                  pyLogger=None, 
                  use_goobi_communication = True,
                  intervals_between_alive_logs = 60*10):
        
        self.host = host
        self.password_token = password_token
        self.use_goobi_communication = use_goobi_communication
        if self.use_goobi_communication: self._com()
        self.process_id = process_id
        self.pyLogger = pyLogger
        self.last_alive_timestamp = time.time()
        # Interval should be configurable
        self.intervals_between_alive_logs = intervals_between_alive_logs
    
    def getLogger( self ):
        """
            Return initial logger
        """
        return self.pyLogger
    
    def debugging( self ) :
        self.debugging_on = True
        if self.use_goobi_communication:
            self._com()
    
    # Use this one if you only want to print with a specific interval,
    # e.g. to inform user that process is a alive
    def alive(self,message):
        if  ((time.time() - self.last_alive_timestamp) >= 
             self.intervals_between_alive_logs):
            alive_msg = 'Script is still alive and processing: {0}'.format(message) 
            self.info(alive_msg)
            self.last_alive_timestamp = time.time()
    
    # logger like interface to goobi.
    def info( self, message ) :
        return self._log( 'info', message )
        
    def debug( self, message ) :
        return self._log( 'debug', message )
    
    def exception( self, message ) :
        self._pyLog('exception', message)
        return self._log( 'error', str(message) )
        
    def warning( self, message ): # Not an actual goobi message but here to complete the set of logging functions. 
        return self._log( 'warning' , message )
        
    def error( self, message ) :
        return self._log( 'error', message )
        
    def critical( self, message ) :
        return self._log( 'critical', message )
        
    def user( self, message ): # Not part of the python logging but here for completeness.
        return self._log( 'user', message )
    
    def _com( self ):
        self.com = GoobiCommunicate( self.host, self.password_token, self.debugging_on )
        
    def _log( self, level, message ):
        
        self._pyLog( level, "(PID" + str(self.process_id).zfill(8) +") " + message )
        dt = datetime.datetime.utcnow().isoformat()
        formatted_message = self.log_format.format(date=dt,
                                                   process_id=self.process_id,
                                                   level=level,
                                                   message=message )
        
        goobi_message = self.goobi_log_format.format(process_id=self.process_id,
                                                     level=level,
                                                     message=message )
        
        #if self.debugging_on:
        #    print(formatted_message)
        
        if level == 'warning':
            level = 'info'
        elif level == 'critical' :
            level = 'error'
        elif level == 'exception' :
            level = 'error'
            
        
        # Push the error out to stderr, this will cause Goobi to pause the step if the script is an automatic one.
        if level == 'error' :
            sys.stderr.write( "stderr: " + formatted_message + "\n" )
        
        if (not (level == 'debug') or 
                (level == 'debug' and self.debugging_on)):
            if self.use_goobi_communication:
                return self.com.addToProcessLog(level,
                                                goobi_message,
                                                self.process_id )

        
    def _pyLog( self, level, message ):
    
        if self.pyLogger != None:
            if level == 'warning' :
                self.pyLogger.warning( message )
            elif level == 'debug' :
                self.pyLogger.debug( message )
            elif level == 'error' :
                self.pyLogger.error( message )
            elif level == 'critical' :
                self.pyLogger.critical( message )
            elif level == 'info':
                self.pyLogger.info( message )
            elif level == 'exception':
                self.pyLogger.exception( message )
            elif level == 'user' :
                self.pyLogger.info( "(Goobi User level) " + message )
                
    