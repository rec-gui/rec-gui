from global_parameters import Globals as globls
from data_collection import DataFileObj
from arbitrator_server import ArbitratorServer
from constants import Constant as const, ConfigLabels

import time

class button_module:
    def __init__(self):

        self.linker_list = [
            self.button_1_callback,
            self.button_2_callback,
            self.button_3_callback,
            self.button_4_callback,
            self.button_5_callback,
            self.button_6_callback
            ]

    def button_1_callback(self):
        '''Write your function here if it's simple. If it is more complex, you might want to import it from a separate
        document and call it here.'''
        if not DataFileObj.data_collect_flag:
            if not DataFileObj.is_data_file_created():
                # Create the file
                DataFileObj.update_file_name(globls.subject_name)
                DataFileObj.update_header_into_data_file()

            globls.dump_log('start saving data')
            globls.custom_button[0].configure(text = "Stop Save")
            globls.update_cont_data(1)
            DataFileObj.update_data_collect_flag(True)
            # print(globls.DUMP_DATA_CONTINUALLY)

        else:
            globls.dump_log('stop saving data')
            globls.DUMP_DATA_CONTINUALLY = 0
            DataFileObj.update_data_collect_flag(False)
            globls.update_cont_data(0)
            globls.custom_button[0].configure(text="Start Save")
            # DataFileObj.dump_data_to_file()
            # DataFileObj.total_data_dumped_to_file()
            DataFileObj.reset_file_name()

        return

    def button_2_callback(self):
        globls.dump_log('Gate is opened')
        data_str = '6 100 /'
        data_recv_ts = time.time()
        data = data_str+"""{}""".format('q'*( 1024 - len(data_str.encode())))
        DataFileObj.save_raw_eye_taskdata(data_recv_ts,0,0,0,0,task_data=data)

        return

    def button_3_callback(self):

        if globls.Shocked:
            globls.update_shock_flag(0)
            globls.ManualShock = 0
            globls.shock_off()
            globls.custom_button[2].configure(text = "Shock Off")
            globls.dump_log('Shock Stopped')

            data_str = '6 200 /'
            data_recv_ts = time.time()
            data = data_str+"""{}""".format('q'*( 1024 - len(data_str.encode())))
            DataFileObj.save_raw_eye_taskdata(data_recv_ts,0,0,0,0,task_data=data)

        else:
            globls.update_shock_flag(1)
            globls.ManualShock = 1
            globls.shock_on()
            globls.custom_button[2].configure(text = "Shock On")
            globls.dump_log('Shock Started')
            data_str = '6 201 /'
            data_recv_ts = time.time()
            data = data_str+"""{}""".format('q'*( 1024 - len(data_str.encode())))
            DataFileObj.save_raw_eye_taskdata(data_recv_ts,0,0,0,0,task_data=data)

        return

    def button_4_callback(self):
        globls.dump_log('Add a custom button function in button_funs.py for the correct button callback!')
        return

    def button_5_callback(self):
        globls.dump_log('Add a custom button function in button_funs.py for the correct button callback!')
        return

    def button_6_callback(self):
        globls.dump_log('Add a custom button function in button_funs.py for the correct button callback!')
        return

