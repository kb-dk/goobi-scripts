#!/usr/bin/python
# -*- coding: utf-8
#Send a log message: 'http://127.0.0.1/goobi/wi?command=addToProcessLog&processId='+processId+'&value=Beginning&jpeg2000&conversion&type=error&token=Xasheax7ai'
# close a step automatically: 'http://127.0.0.1/goobi/wi?command=closeStep&stepId='+stepId+'&token=Xasheax7ai'
import urllib2


class GoobiCommunicate() :
    """
        Simplfy the communication between python and Goobi.
        
    """
    protocol = "http"
    url_base = "{protocol}://{host}/goobi/wi?"
    url_token = "&token={token}"
    url_command = "command={command}"
    
    def __init__( self, host, password_token, debugging=False ) :
    
        self.host = host if host is not None else '127.0.0.1'
        self.token = password_token
        self.debugging = debugging
        
        self._update_url_base()
    
    def addToProcessLog( self, level, message, process_id ) :
        '''
        TODO: Document method
        '''
        goobi_levels = ['info', 'error', 'debug', 'user']
        
        if level not in goobi_levels:
            print "Level not recognised, use one of " + ",".join( goobi_levels )
            return False
        
        additional = {
            'processId' : process_id,
            'type' : level,
            'value' : message
        }
        return self._send( "addToProcessLog", additional )
    
    def closeStep( self, step_id=None, process_id=None ) :
        '''
        TODO: Document method
        '''
        if not step_id and not process_id:
            print "Must have either a step id or a process id!"
        
        if step_id:
            additional = { "stepId" : step_id }
            
            return self._send( "closeStep", additional )
            
        if process_id:
            return self.closeStepByProcessId( process_id )
            
        return False
            
    def closeStepByStepId( self, step_id ) :
        '''
        TODO: Document method
        '''
        return self.closeStep( step_id )
        
    def closeStepByProcessId( self, process_id ) :
        '''
        TODO: Document method
        '''
        additional = { "processId" : process_id }
        
        return self._send( "closeStepByProcessId", additional )
    
    def reportToPrevStep(self,step_id,prev_step_name,error_message=None):
        '''
        TODO: Document method
        '''
        error_message = error_message if error_message else "No error given"
        additional = {"stepId" : step_id,
                      "destinationStepName" : prev_step_name,
                      "errorMessage" : error_message 
                      }
        return self._send( "reportProblem", additional )
    
    def addProperty( self, process_id, name, value ):
        '''
        TODO: Document method
        '''
        additional = {
            "processId" : process_id,  
            "property" : name,
            "value" : value
        }
        
        return self._send( "AddProperty", additional )
    
    def _update_url_base( self ):
        '''
        TODO: Document method
        '''
        self.url_base = self.url_base.format( protocol=self.protocol, host=self.host )
        
    def _quote( self, string ):
        '''
        TODO: Document method
        '''
        return urllib2.quote( str(string), safe="" )
    
    def _send( self, command, additional=None ) :
        '''
        TODO: Document method
        '''
        url = self.url_base
        url += self.url_command.format( command=command )
        
        if additional and len( additional ) > 0 :
            equals = [ k+"="+self._quote( additional[k] ) for k in additional ]
            url += "&" + "&".join( equals )
            
        url += self.url_token.format( token=self.token )
        
        if self.debugging:
            print "Debug: GoobiCommunicate() URL:", url
        
        # TODO: Tidy this up. Need to catch exceptions properly and ensure 
        # request is closed (although python handles that too)
        try:
            response = urllib2.urlopen( url )
            
            if response.code == 200:
            
                return True
                
            else:
                
                if self.debugging:
                    print "Debug: GoobiCommunicate() None OK response from Goobi:", response.msg, response.code
            response.close()        
        except:
            pass
        return False
if __name__ == '__main__' :

    comm = GoobiCommunicate( "127.0.0.1", "Xasheax7ai", True )
    
    #comm.addToProcessLog( "info", "A test message", 53 )
    
    comm.addProperty( 54, "test_property", "test_property_value" )
    
    
