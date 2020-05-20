import os
from constants import Constant
from file import File

class ReadTaskParameters:
    def __init__(self):
        self.file = File()
        self.editable_task_config = []
        self.displayable_task_config = []

    def read(self, filename):
        '''
        Read the configuration parameters that are editable from a file
        for a task
        :param filename:
        :return: None if filename is not present or if data could not be read
        '''
        CURDIR = Constant.CUR_DIR_NAME
        file = os.path.join(CURDIR, filename)
        data = file.read(file)
        if not data:
            return None

        self.editable_task_config = data['config_to_send']
        self.displayable_task_config = data['config_to_display']

    def write(self, filename):
        '''
        Read the configuration parameters that are editable from a file
        for a task
        :param filename:
        :return:
        '''
        data = file.read(file)
        if not data:
            return None


ReadTaskParameterObj = ReadTaskParameters()