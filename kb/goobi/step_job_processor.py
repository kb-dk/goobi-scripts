'''
Created on 20/06/2014

@author: jeel
'''
import sys
import os
import queue
from threading import Thread
import time

# I dont like it, http://stackoverflow.com/a/4284378
lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../')
sys.path.append(lib_path)
from tools.processing import processing

class StepJobqueue():
    
    def __init__(self,logger):
        self.step_job_queue = queue.Queue()
        self.logger = logger
    
    def get_queue(self):
        return self.step_job_queue
    
    def get(self,block=True, timeout=0.5):
        return self.step_job_queue.get(block, timeout)
    
    def add(self, data):
        data = ' '.join(data)
        self.step_job_queue.put(data)
        msg = ('{0} placed in queue. Approx. {1} in queue.')
        msg = msg.format(data,self.step_job_queue.qsize())
        self.logger.info(msg)

class StepJobProcessor(Thread):
    '''
    Todo: Document
    '''
    def __init__(self,logger=None,shared_job_queue=None):
        super(StepJobProcessor, self).__init__()
        if shared_job_queue is not None:
            self.shared_job_queue = shared_job_queue
        self.step_job_queue = queue.Queue()
        self.running = True
        self.logger = logger
 
    def add(self, data):
        data = ' '.join(data)
        self.step_job_queue.put(data)
        msg = ('{0} placed in queue. Approx. {1} in queue.')
        msg = msg.format(data,self.step_job_queue.qsize())
        self.logger.info(msg)
 
    def stop(self):
        self.running = False
 
    def run(self):
        while self.running:
            try:
                time.sleep(4.5)
                # block until items is placed in queue:
                if self.step_job_queue.qsize() > 0:
                    msg = 'Approx. step jobs in non-shared queue: {0}'
                    msg = msg.format(self.step_job_queue.qsize())
                    self.logger.info(msg)
                    job = self.step_job_queue.get(block=True, timeout=0.5)
                elif self.shared_job_queue is not None:
                    # shared_job_queue is shared between multiple process
                    # and thus makes multiprocessing possible
                    job = self.shared_job_queue.get(block=True, timeout=0.5)
                else:
                    # Try anyway
                    job = self.step_job_queue.get(block=True, timeout=0.5)
                self.process(job)
            except queue.Empty:
                pass
                #sys.stdout.write('.')
                #sys.stdout.flush()
        if not self.step_job_queue.empty():
            if self.logger: 
                step_jobs_left = []
                while not self.step_job_queue.empty():
                    step_jobs_left.append(self.step_job_queue.get())
                msg = 'Step jobs left in the queue: {0}'
                msg = msg.format(', '.join(step_jobs_left))
                self.logger.info(msg)
        msg = 'Step job processor closed.'
        if self.logger: self.logger.info(msg)
                
    def process(self,cmd):
        """
        cmds is simply the of arguments from sys.arg.
        The first element is the filename of the calling client.
        The second argument is the path to the python script to be called and
        the arguments to this call.
        """
        cmd_list = cmd.split()
        if len(cmd_list) >= 1:
            step_job_filename = os.path.basename(cmd_list[1])
            msg = 'Starting step job: {0}'.format(step_job_filename)
            self.logger.info(msg)
            try:
                result = processing.run_cmd(cmd, shell=True, print_output=False)
            except Exception as e:
                err = 'An error occured when processing step job {0}'
                err = err.format(cmd)
                if self.logger: self.logger.error(err)
                err = 'Error from failed step job: {0}'
                err = err.format(str(e))
                if self.logger: self.logger.error(err)
                return
            msg = 'Step job {0} completed with result{1}.'
            msg = msg.format(step_job_filename,result['output'])
            self.logger.info(msg)
        else:
            if self.logger: self.logger.error('An empty job placed on queue.')