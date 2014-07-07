"""
Created on 19/06/2014

@author: jeel
"""

from step_job_processor import StepJobProcessor, StepJobQueue
from tcp_server import StepJobTCPServer, StepJobTCPHandler
import tools.logging.logger as logger
import signal
import sys

class ConvertServer():
    
    def signal_term_handler(self,signal, frame):
        self.logger.info('Processor terminated with SIGTERM. Closing gently down.')
        self.server.server_close()
        self.logger.info('Server closed.')
        self.logger.info('Closing step job processor.')
        self.sjp.stop()
        self.sjp.join()
        self.logger.info('Command step job processor stopped.')
        self.logger.info('Existing server.')
        self.logger.info('=============================')
        sys.exit(0)
    
    def __init__(self,config_path=None):
        '''
        Todo: Document this
        
        ''' 
        # Setup logger
        log_path = '/opt/digiverso/logs/step_server/' 
        log_level = 'INFO'
        self.logger = logger.setup(log_path,log_level)
        # Setup host and port for connection
        host = 'localhost'
        port = 37000
        self.address = (host, port)
        # Create one processor per core - tesseract 3.03 is not multithreaded
        # Todo: Add functionality so first thread will always take from non shared
        # queue, and the other always from the shared. E.g.
        self.core_num = 1
        self.step_job_processors = []
        
        self.job_queue = StepJobQueue(self.logger)
        # Create StepJobProcesser and StepJobServer 
        self.logger.info('Initiating {0} step job processor(s)...'.format(self.core_num))
        for i in range(self.core_num):
            self.logger.info('Initiating step job processor {0}...'.format(i+1))
            self.step_job_processors.append(StepJobProcessor(job_queue=self.job_queue,
                                                             logger=self.logger))
        self.logger.info('Step job processor started.')
        self.server = StepJobTCPServer(server_address = self.address,
                                       RequestHandlerClass = StepJobTCPHandler,
                                       bind_and_activate=True,
                                       step_job_queue= self.job_queue,
                                       logger=self.logger)
    
    def start(self):
        self.logger.info('Starting step job processor(s)...')
        for step_processor in self.step_job_processors:
            step_processor.start()
        self.logger.info('Step job processor(s) started.')
        self.logger.info('Starting step job server...')
        signal.signal(signal.SIGTERM, self.signal_term_handler)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            msg = 'KeyboardInterrupt called. Closing server gently.'
            self.logger.info(msg)
        except Exception as e:
            err = 'An error occured: {0}. Closing server gently.'
            err = err.format(str(e))
            self.logger.error(err)
        self.server.server_close()
        self.logger.info('Server closed.')
        self.logger.info('Closing {0} step job processor(s).'.format(len(self.step_job_processors)))
        for step_processor in self.step_job_processors:
            step_processor.stop()
            step_processor.join()
        self.logger.info('{0} step job processor(s) stopped.'.format(len(self.step_job_processors)))
        self.logger.info('Existing server.')
        self.logger.info('=============================')

if __name__ == "__main__":
    cs = ConvertServer()
    cs.start()
