'''
   Code that process the thridy party server request
'''

import socket
import time
import copy
import utility as util
# from digitalIO import DIO
from constants import Constant as const
from vergence_version import ValidateVergenceVersion
from global_parameters import Globals as globls
from data_collection import DataFileObj
from constants import Constant
from logger import logging

log = logging.getLogger(__name__)


class ArbitratorServer:
    def __init__(self):

        # self.DIO_obj = DIO()

        # for programing printer port

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', globls.config_param['arbitrator_service']['local_port']))

        sock_eye = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_eye.bind(('', globls.config_param['arbitrator_service']['local_port_eye']))
        # sock.settimeout(30)
        globls.update_arbitrator_server_socket(sock, sock_eye)

        self.eye_check = ValidateVergenceVersion()

        # send the UDP packet to initiate the connection
        data = '{} {}/'.format(Constant.COMMAND_WORD_CONNECTION, Constant.CONNECTION_START)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data, 'Connection Initiation Message')
        self.receiver()

    def receiver(self):
        '''
        Receiver loop to check the incoming packets
        :return:
        '''
        # globls.dump_log("Running Matlab thread")
        globls.dump_log('Listening to 3rd party messages')
        while globls.is_program_running:
            try:
                data, addr = globls.arbitrator_sock.recvfrom(globls.constant['data_size_length'])
                data_recv_ts = time.time()

                # process the variables
                if len(data):
                    # Check if there is any delimiter in the message '/' if yes then split
                    cmd_lists = data.split(globls.constant['message_delimiter'])

                    # Data before / is valid data read and remove the space
                    cmd_list = cmd_lists[0].split()

                    if int(cmd_list[0]) == Constant.COMMAND_WORD_CONNECTION:
                        if int(cmd_list[1]) == Constant.CONNECTION_START:

                            # send the UDP packet to initiate the connection
                            data = '{} {}/{} {}/{} {}/{} {}/{} {}/'.format(Constant.COMMAND_WORD_CONNECTION,
                                                                           Constant.CONNECTION_ACK,
                                                                           const.SCREEN_HEIGHT,
                                                                           globls.arbitrator_display[
                                                                               'screen_height_mm'],
                                                                           const.SCREEN_DISTANCE,
                                                                           globls.arbitrator_display[
                                                                               'screen_distance_mm'],
                                                                           const.SCREEN_WIDTH,
                                                                           globls.arbitrator_display['screen_width_mm'],
                                                                           const.SCREEN_IOD,
                                                                           globls.arbitrator_display['iod_mm'])
                            util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                                           'Connection Ack Message')
                            globls.update_load_subject_task_config_flag(True)
                        elif int(cmd_list[1]) == Constant.CONNECTION_ACK:
                            globls.connection_state = Constant.CONNECTION_ACK
                            # Update this flag to ensure that the user knows what is the next step after connection is up
                            globls.update_load_subject_task_config_flag(True)

                            # util.send_screen_parameters()
                            # print cmd_list
                    elif int(cmd_list[0]) == Constant.DISPLAY_COMMAND_WORD:
                        config = [int(cmd_list[1]), cmd_list[2]]
                        globls.update_displayable_config(config)

                    # Process the exit call
                    elif (int(cmd_list[0]) == Constant.COMMAND_WORD_CONTROL and
                                  int(cmd_list[1]) == Constant.CONTROL_EXIT):
                        break

                    elif int(cmd_list[0]) == Constant.EYE_IN_OUT_REQUEST:

                        eye_in_out = copy.copy(globls.eye_in_or_out)

                        # if (eye_in_out[0] != globls.last_sent_eye_in_out[0]
                        #     or eye_in_out[1] != globls.last_sent_eye_in_out[1]):
                        data = '{} {}/{} {}/'.format(Constant.LEFT_EYE_STATUS, globls.eye_in_or_out[0],
                                                     Constant.RIGHT_EYE_STATUS, globls.eye_in_or_out[1])
                        util.send_data(globls.arbitrator_sock_eye, globls.arbitrator_sock_addr_eye, data)
                        # print "EYE in or out ", data

                        globls.update_last_sent_eye_in_out(eye_in_out)

                    elif int(cmd_list[0]) == Constant.VERGENCE_REQUEST:
                        points = map(float, cmd_list[1:6])

                        value = self.eye_check.vergence_error(points)
                        # if value != globls.last_vergence_error_sent:
                        data = '{} {}/'.format(Constant.VERGENCE_STATUS, value)
                        util.send_data(globls.arbitrator_sock_eye, globls.arbitrator_sock_addr_eye, data)
                        # print "Vergence error ", data
                        globls.update_last_sent_vergence_error(value)

                    elif int(cmd_list[0]) == Constant.SCREEN_WINDOW_WIDTH:
                        globls.update_arbitrator_server_screen_resolution(width=int(cmd_list[1]))
                        globls.dump_log('Received the screen width and scale factor to display on GUI: {}'.
                                        format(globls.arbitrator_display['x_scale_factor']))

                    elif int(cmd_list[0]) == Constant.SCREEN_WINDOW_HEIGHT:
                        globls.update_arbitrator_server_screen_resolution(height=int(cmd_list[1]))
                        globls.dump_log('Received the screen Height and scale factor to display on GUI: {}'.
                                        format(globls.arbitrator_display['y_scale_factor']))

                    elif int(cmd_list[0]) == Constant.CENTRE_OF_WINDOWS:
                        # print cmd_list
                        # 100 number list of X Y Z diameter
                        # Maximum 30 points
                        no_of_points = int(cmd_list[1])
                        config = []
                        lst = cmd_list[2:]
                        # pair the data and give it to UI for updation
                        for i in range(0, len(lst), 6):
                            config.append([float(lst[i]), float(lst[i + 1]), float(lst[i + 2]),
                                           float(lst[i + 3]), lst[i + 4], lst[i + 5]])

                            if len(config) == Constant.MAXIMUM_CENTRE_OF_WINDOW:
                                break
                        globls.dump_log('Points to draw {}'.format(cmd_list))
                        globls.update_centre_point(no_of_points, config)

                    elif int(cmd_list[0]) == Constant.WINDOW_ON:
                        # print cmd_list
                        globls.update_centre_window_on_off(True)
                        globls.dump_log('Window On')

                    elif int(cmd_list[0]) == Constant.WINDOW_OFF:
                        # print cmd_list
                        globls.update_centre_window_on_off(False)
                        globls.dump_log('Window Off')
                        # Reset this to -1, -1 so that next time this is queried from
                        # Arbitrator server new values are sent
                        globls.update_last_sent_eye_in_out([-1, -1])
                    # elif int(cmd_list[0]) == Constant.REWARD_ON:
                    #     # print cmd_list
                    #     self.DIO_obj.write_digital_bit(1)
                    #     #self.DIO_obj.reward_on()
                    #     globls.dump_log('Reward On')
                    # elif int(cmd_list[0]) == Constant.REWARD_OFF:
                    #     # print cmd_list
                    #     self.DIO_obj.write_digital_bit(0)
                    #     #self.DIO_obj.reward_off()
                    #     globls.dump_log('Reward Off')
                    elif int(cmd_list[0]) == Constant.VERGENCE_ON:
                        # print cmd_list
                        globls.udpdate_vergence_display(True)
                        globls.dump_log('Vergence On')

                    elif int(cmd_list[0]) == Constant.VERGENCE_OFF:
                        # print cmd_list
                        globls.udpdate_vergence_display(False)
                        globls.dump_log('Vergence Off')
                        # Reset this to -1 so that next time this is queried from
                        # Arbitrator server new values are sent
                        globls.update_last_sent_vergence_error(-1)

                    elif int(cmd_list[0]) == Constant.DRAW_EVENTS:
                        tempnum = len(cmd_lists)-1
                        globls.update_drawing_object_on(1)
                        globls.update_drawing_object_number(tempnum)

                        for i in range(0, tempnum):
                            templist = cmd_lists[i].split()
                            if i == 0:
                                tempx = float(templist[2])
                                tempy = float(templist[3])

                                data_str = '6 9 /'
                                temp_data = data_str+"""{}""".format('q'*( 1024 - len(data_str.encode())))
                                DataFileObj.save_raw_eye_taskdata(data_recv_ts, 0,0,0,0, task_data=temp_data)

                            else:
                                tempx = float(templist[1])
                                tempy = float(templist[2])
                            globls.update_drawing_object_pos(i, 0, tempx)
                            globls.update_drawing_object_pos(i, 1, tempy)


                    # elif int(cmd_list[0]) == Constant.EVENTS:
                    #     globls.dump_log('event {}'.format(cmd_list))
                    #     if not globls.DUMP_DATA_CONTINUALLY:
                    #         if int(cmd_list[1]) == Constant.EVENT_START:
                    #             # Start the data save
                    #             DataFileObj.update_data_collect_flag(True)
                    #
                    #         elif int(cmd_list[1]) == Constant.EVENT_STOP:
                    #             # This needs to be saved here as we dump the saved data to file
                    #             # And data collection falg will be reset
                    #             DataFileObj.save_raw_eye_taskdata(
                    #                 data_recv_ts,
                    #                 globls.last_raw_eye_data[0], globls.last_raw_eye_data[1],
                    #                 globls.last_raw_eye_data[2], globls.last_raw_eye_data[3],
                    #                 task_data=data)
                    #
                    #             # Stop saving the data and dump tp file
                    #             # Flag to stop saving the data is set inside this function
                    #             DataFileObj.dump_data_to_file()
                    #             globls.update_last_sent_vergence_error(-1)
                    #             globls.update_last_sent_eye_in_out([-1, -1])

                    # Save the data from 3rd party server
                    if globls.DUMP_DATA_CONTINUALLY:
                        DataFileObj.dump_data_continually(data_recv_ts, data)
            # except socket.timeout:
            #     pass
            except Exception as e:
                log.exception(e)
        globls.arbitrator_sock.close()
