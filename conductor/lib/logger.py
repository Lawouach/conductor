# -*- coding: utf-8 -*-
import sys
import os, os.path

import logging
from logging import handlers

__all_ = ['open_logger', 'close_logger']

def open_logger(log_base_dir=None, log_filename=None, 
                logger_name=None, stdout=False, level=logging.INFO):
    logger = logging.getLogger(logger_name or '')
    logger.setLevel(level)
    
    if log_base_dir and log_filename:
        log_base_dir = os.path.abspath(log_base_dir)
        if not os.path.exists(log_base_dir):
            os.makedirs(log_base_dir)
        
        path = os.path.join(log_base_dir, log_filename)
        h = handlers.RotatingFileHandler(path, maxBytes=10485760, backupCount=3)
        h.setLevel(level)
        h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
        logger.addHandler(h)

    if stdout:
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(level)
        h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
        logger.addHandler(h)

    return logger
               
def close_logger(logger_name):
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers:
        handler.flush()
        handler.close()
