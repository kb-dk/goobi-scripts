#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 20/06/2014

@author: jeel
'''

import logging
import os
import time

try:
    basestring
except NameError:  # python3
    basestring = str

class logger(object):
    '''
    Logger
    '''

    def __init__(self,log_folder,log_level='INFO',print_to_terminal=False,
                 print_to_file=True):
        '''
        Constructor
        '''
        self.last_alive_timestamp = time.time()
        self.intervals_between_alive_logs = 25
        self.log_level = logging.getLevelName(log_level)
        # create logger
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        # create formatter
        msg_format = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(msg_format)
        # create console handler and set level to debug
        if print_to_terminal:
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        # create timed rotating file handler
        if print_to_file:
            filename = self._get_filename(log_folder)
            fh = logging.FileHandler(filename)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        self.logger = logger
        msg = 'Logger {0} initiated. Log level: {1}, log file path: {2}.'
        msg = msg.format(logger.name, logging.getLevelName(log_level), filename)
        logger.debug(msg)
        
        
    def _get_filename(self,log_folder):
        if not os.path.exists(log_folder): os.makedirs(log_folder)
        this_day = time.strftime('%Y-%m-%d')
        filename =this_day+'.log'
        filename = os.path.join(log_folder,filename)
        return filename
    
    def log_section(self,msg,log_level=None,tabs=0):
        '''
        Log a message msg with section before and after message added to log. 
        :param msg:
        :param log_level:
        :param tabs:
        '''
        section = '========='
        self.log_msg(section,log_level,tabs=tabs)
        self.log_msg(msg,log_level,tabs=tabs)
        self.log_msg(section,log_level,tabs=tabs)
    
    # Use this one if you only want to print with a specific interval,
    # e.g. to inform user that process is a alive
    def alive(self,message):
        if  ((time.time() - self.last_alive_timestamp) >= 
             self.intervals_between_alive_logs):
            alive_msg = 'Script is still alive and processing: {0}'.format(message) 
            self.info(alive_msg)
            self.last_alive_timestamp = time.time()
    
    def info(self,msg,tabs=None):
        if tabs:self.log_msg(msg, 'INFO',tabs)
        else:self.log_msg(msg, 'INFO')
        
    def debug(self,msg,tabs=None):
        if tabs: self.log_msg(msg, 'DEBUG',tabs)
        else: self.log_msg(msg, 'DEBUG')
    
    def error(self,msg,tabs=None):
        if tabs: self.log_msg(msg, 'ERROR',tabs)
        else: self.log_msg(msg, 'ERROR')
    
    def warning(self,msg,tabs=None):
        if tabs: self.log_msg(msg, 'WARNING',tabs)
        else: self.log_msg(msg, 'WARNING')
    
    def log_msg(self,msg,log_level=None,tabs=1):
        '''
        Log str msg with optinal log_levl and numbers of tabs prefixed the
        message.
        
        If no log_level is set, 'INFO' will be used.
        
        If no tabs is set, one tab will be prefixed to message. 
        :param msg:
        :param log_level:
        :param tabs:
        '''
        levels = {'CRITICAL': 50,'ERROR': 40, 'WARNING': 30,
                  'INFO': 20, 'DEBUG': 10}
        if log_level == '' or log_level is None:
            log_level = levels['INFO']
        elif not log_level in levels:
                # Not a valid log_level
                t_msg = ('{0} is not a valid log_level. Setting log_level to default.')
                t_msg = t_msg.format(log_level)
                log_level = levels['WARNING']
                self.logger.log(log_level,t_msg)
        else:
            log_level = levels[log_level]
        if tabs > 0: msg = tabs*'\t'+msg
        self.logger.log(log_level,msg)
