'''
Created on 20/06/2014

@author: jeel
'''
import logging

import tools.filesystem.fs as fs
import os
import time

def setup(log_path,
          log_level = 'INFO',
          log_dateformat = '%Y-%m-%d %H:%M',
          log_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
          ):
    '''
    #http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python
    #Todo: document
    '''
    # Log_path must be a folder - e.g. to add rotating logs later
    fs.create_folder(log_path)
    current_date = time.strftime('%Y-%m-%d')
    log_path = os.path.join(log_path,current_date+'_'+__name__+'.log')
    
    log_levels = {'CRITICAL' : logging.CRITICAL,
                  'ERROR' : logging.ERROR,
                  'WARN' : logging.WARNING,
                  'WARNING' : logging.WARNING,
                  'INFO' : logging.INFO,
                  'DEBUG' : logging.DEBUG
                  }
    if (log_level not in log_levels):
        err = ('Log level {0} is not valid. '
               'Log level must be one of the following: {1}')
        err = err.format(log_level,
                         ', '.join(log_levels.keys()))
        raise ValueError(err)
    else:
        log_level = log_levels[log_level]
    
    logging.basicConfig(level=log_level,
                        format=log_format,
                        datefmt=log_dateformat,
                        filename=log_path,
                        filemode='a')
    logger = logging.getLogger(__name__)
    msg = 'Logger {0} initiated. Log level: {1}, log file path: {2}.'
    msg = msg.format(logger.name, logging.getLevelName(log_level), log_path)
    logger.debug(msg)
    return logger



