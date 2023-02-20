# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/00_logging.ipynb.

# %% auto 0
__all__ = ['get_logger']

# %% ../notebooks/00_logging.ipynb 1
import logging
import sys

def get_logger(name   = None, 
               form   = '(%(levelname)s %(name)s) %(message)s', 
               level  = logging.INFO, 
               stream = None):
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(stream)    
    formatter = logging.Formatter(form)
    handler.setFormatter(formatter)
    
    logger.handlers.clear()
    logger.addHandler(handler)
    
    return logger