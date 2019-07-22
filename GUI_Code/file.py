'''
General function to read configuration
'''

import os
import json
from logger import logging
log = logging.getLogger(__name__)


class File:
    def read(self, filename):
        if filename:
            if os.path.isfile(filename):
                with open(filename) as json_data_file:
                    return json.load(json_data_file)
        return None

    def write(self, data, filename):
        try:
            if filename is None:
                return False

            with open(filename, 'w') as outfile:
                json.dump(data, outfile, indent=4)

            return True
        except Exception as e:
            log.exception(e)
            return False

