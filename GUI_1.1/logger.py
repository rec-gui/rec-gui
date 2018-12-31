'''
Logging
'''
import logging
import os
from logging.config import dictConfig


CUR_DIR_NAME = os.path.dirname(__file__)
LOG_DIR_NAME = os.path.join(CUR_DIR_NAME, 'logs')
LOG_FILE_NAME = 'ui_log.log'
LOG_FILE = os.path.join(LOG_DIR_NAME, LOG_FILE_NAME)

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s: [%(filename)s:%(lineno)s - %(funcName)20s() ]: %(message)s'}
        },

    handlers = {
        'h': {'class': 'logging.handlers.RotatingFileHandler',
              'formatter': 'f',
              'filename': LOG_FILE,
              'maxBytes': 100000000,
              'level': logging.DEBUG,
              'backupCount': 3}
        },
    root = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        },
)

if not os.path.exists(LOG_DIR_NAME):
    os.mkdir(LOG_DIR_NAME)

dictConfig(logging_config)
