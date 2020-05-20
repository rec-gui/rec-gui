'''
Globally accessed parmeters
'''
import os
# import parallel
from constants import Constant as const, ConfigLabels
from file import File
from logger import logging
log = logging.getLogger(__name__)


class GlobalParams:
    def __init__(self):

        # initialize printer port
        # self.prt = parallel.Parallel()
        # self.prt.setData(0)

        # This can either be moved to default.conf or can remain as constant
        self.directories = {'data': const.DATA_DIR,
                            'logs': const.LOG_DIR,
                            'configuration': const.CONFIGURATION_DIR}

        # Configuration parameters for subject specific configuration
        self.subject_name = 'subject_default'
        self.subject_configuration_file = const.SUBJECT_DEFAULT_CONFIG_FILE
        self.subject_configuration = None

        self.gui_display = {}
        self.arbitrator_display = {}
        self.arbitrator_window_width = 0 #1280
        self.arbitrator_window_height = 0 #720
        self.drawing_object_on = 0
        self.drawing_object_number = 0
        self.drawing_object_pos = [[0,0],[0,0],[0,0],[0,0],[0,0]]
        self.drawing_object_color = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]

        # Experiment specific configuration
        self.config_param = None
        self.config_file_name = const.DEFAULT_CONFIG_FILE

        # read all the config parameters,
        # Subject specific config
        resp, msg = self.read_config(self.subject_configuration_file)
        if not resp:
            log.error(msg.format(self.subject_configuration_file))
            print(msg.format(self.subject_configuration_file))
            exit(1)
        self.update_subject_spcific_configuration(resp, self.subject_configuration_file)

        # application specific config
        resp, msg = self.read_config(self.config_file_name)
        if not resp:
            log.error(msg.format(self.config_file_name))
            print(msg.format(self.config_file_name))
            exit(1)
        self.update_application_configuration(resp, self.config_file_name)

        # GUI root widget place holder
        self.gui_root = None

        # Flag to check if programe has been stopped
        self.is_program_running = True

        # place holder for arbitrator sockets
        self.arbitrator_sock = None
        self.arbitrator_sock_addr = None

        # Raw Eye Data and task data is append when the task is run.
        # It is upto user when he attempts to write to the file and not let
        # this lise overgrow
        # Note: As soon as this data is written to file this would be reset to empty list []
        self.raw_eye_task_data = []
        self.last_raw_eye_data = [0, 0, 0, 0]

        # Eye data to which offset and gain is applied and is used for
        # display. This is stored in mm and co-ordinate (0,0) at centre
        # Where as eye link send this in reference to co-ordinate (0, 0)
        # at top left
        self.eye_data = [[0, 0], [0, 0]]             # Left [x, y] Right [x, y]
        self.latched_eye = 0
        self.caught = 0

        # Moving eye pos sample holds [Left(x, y), Right(x, y)]
        self.raw_eye_data_sample = [
            [[0] * 2] * self.constant['moving_eye_position_mean'],
            [[0] * 2] * self.constant['moving_eye_position_mean']]

        # place holder for eye interpreter
        self.eye_recording_method = self.analaog_input_output['eye_recording_method']
        self.eye_recording_method_name = self.analaog_input_output['eye_recording_method_name']
        self.eye_recording_method_obj = None

        # Since we log the messages from different thread, Sharing a common
        # list where the logs would be dumped and tkinter would run a
        # timer every s(can be changed) where it reads the events and dumps it
        # This is added to keep thread safe and running into infinite loops
        # Log would be appended to the list and as and when they are dumped they wouldbe
        # Log would be appended to the list and as and when they are dumped they wouldbe
        # removed
        self.dump_log = None

        # Vergence to plot on the display
        self.vergence_error_to_plot = [0, 0, 0]  # x, y
        # If this flag is set then display the vergence
        self.display_vergence = False

        # Eye in and out for Left and right
        self.eye_in_or_out = [1, 1]
        self.last_sent_eye_in_out = [0, 0]
        self.last_vergence_error_sent = 0

        # list of centre points with value [x, y, z, diameter] which is sent
        # from GUI to Matlab
        self.centre_of_windows = []
        self.depth = 0
        # This is required to redraw the window else everytime the window would be drawn
        # unncessarily
        self.centre_window_on = False

        # If there is any configuration that needs to be shared with arbitrator server
        # store in this dict or if in case sent directly then it not need be stored
        self.configuration_to_share = {}

        # State to check if 3rd party application is up and exchange the basic configuration
        self.connection_state = const.CONNECTION_START

        self.task_filename = None
        self.display_filename = None

        # Configuration from arbitrator
        self.displayable_config = {}

        self.load_subject_task_config_flag = False

        self.Shocked = 0
        self.ManualShock = 0
        self.DUMP_DATA_CONTINUALLY = 0

        # Xipppy connection with Ripple
        self.XIPPPY_CONNECTION = False
        self.XIPPPY_PARALLELOUT_IDX = int(4)
        # Command numbers for identification and interpretation
        #   Xipppy only allows for unsigned integers, so the actual values that follow
        #   these indentification numbers will be plus 100*value
        #       Example(X-Offset Left = 31,000 + 100*(15.2)
        #       Example(X-Offset Left = 31,000 + 100*(-15.2)
        #   This equation can be used to interpret the original values
        self.XIPPPY_PUPILSIZE_LEFT = 40000
        self.XIPPPY_PUPILSIZE_RIGHT = 41000
        self.XIPPPY_XGAIN_LEFT = 30000
        self.XIPPPY_XOFFSET_LEFT = 31000
        self.XIPPPY_YGAIN_LEFT = 32000
        self.XIPPPY_YOFFSET_LEFT = 33000
        self.XIPPPY_XGAIN_RIGHT = 34000
        self.XIPPPY_XOFFSET_RIGHT = 35000
        self.XIPPPY_YGAIN_RIGHT = 36000
        self.XIPPPY_YOFFSET_RIGHT = 37000

        # Auto offset flags
        self.auto_offset_flag = 0
        self.auto_offset_start_collect = 0
        self.auto_offset_stop_collect = 0
        self.auto_offset_dump_data = 0
        self.auto_offset_update_primer = 0
        self.auto_offset_update_flag = 0

        # Auto offset data
        self.auto_offset_data_LEyeX = []
        self.auto_offset_data_LEyeY = []
        self.auto_offset_data_REyeX = []
        self.auto_offset_data_REyeY = []
        self.auto_offset_tmpOffset_LEyeX = 0
        self.auto_offset_tmpOffset_LEyeY = 0
        self.auto_offset_tmpOffset_REyeX = 0
        self.auto_offset_tmpOffset_REyeY = 0

    def read_config(self, filename, directory_path=const.CUR_DIR_NAME):
        '''
        Read subject or task config
        :param filename:
        :param directory_path:
        :return:
        '''
        file_name_with_path = os.path.join(directory_path, filename)

        if not os.path.isfile(file_name_with_path):
            return None, 'Please check if file {} exist!!!'

        file = File()
        subject_configuration =  file.read(file_name_with_path)
        if not subject_configuration:
            return None, 'Error reading file {}!!!'

        return subject_configuration, "success"

    def update_subject_spcific_configuration(self, config, filename):
        '''
        subject specific configuation like offset, gain, pupil size screen constant
        :param config:
        :param filename:
        :return:
        '''
        self.subject_configuration = config
        self.subject_configuration_file = filename

        # global parameters for easy access
        # Screen parameters constant like
        self.arbitrator_display = self.subject_configuration['arbitrator_display_screen']

        self.offset_gain_config = self.subject_configuration['eye_offset_gain']
        self.pupil_size = self.subject_configuration['pupil_size']
        self.eye_selected = self.subject_configuration['selected_eye']
        self.arbitrator_window_width = self.arbitrator_display['window_width_pixel']
        self.arbitrator_window_height = self.arbitrator_display['window_height_pixel']

    def update_application_configuration(self, config, filename):
        '''
        Configuration required for running the experiment or task
        :param config:
        :param filename:
        :return:
        '''
        self.config_param = config
        self.config_file_name = filename
        self.analaog_input_output = self.config_param['analog_input_output']
        self.calibration_config = self.config_param['calibration']
        self.receptive_field_map = self.config_param['receptive_field_mapping']
        self.constant = self.config_param['constant']

    def update_configuration_file(self, file):
        '''
        Update task config file
        :param file:
        :return:
        '''
        self.config_file_name = file


    def save_subject_specifc_config(self, subjectname, directory):
        '''
        Save subject specific configuration
        :param filename:
        :param directory:
        :return:
        '''

        subject_filename = subjectname +'.conf'
        if subject_filename != const.SUBJECT_DEFAULT_CONFIG_FILE:
            self.subject_configuration_file = subject_filename
        self.update_subject_name(subjectname)
        # if the directory does not exist create one
        if not os.path.exists(self.subject_configuration_file):
            os.makedirs(self.subject_configuration_file)

        file_name_with_path = os.path.join(directory, self.subject_configuration_file)
        file = File()
        file.write(self.subject_configuration, file_name_with_path)

    def update_subject_name(self, subjectname):
        self.subject_name = subjectname

    def update_screen_config(self, cmd_arr):
        '''
        Update screen related parameters
        :param cmd_arr:
        :return:
        '''
        #print(cmd_arr[0][0],cmd_arr[0][1].get())
        # Step through the cmd_arr. First index is the field value to update, second index is the tkinter object which you need to 'get' the value of to save
        for c in cmd_arr:
            self.subject_configuration['arbitrator_display_screen'][c[0]] = float(c[1].get())

        self.arbitrator_display = self.subject_configuration['arbitrator_display_screen']

    def update_gui_parameters(self, root=None, gui_object=None):
        if root is not None:
            self.gui_root = root

        # Not required for now
        # if gui_object is not None:
        #     self.gui = gui_object

    def update_offset_gain_applied_eye_data(self, left_og_x, left_og_y, right_og_x, right_og_y):
        '''
        Update offset and gain
        :param left_og_x:
        :param left_og_y:
        :param right_og_x:
        :param right_og_y:
        :return:
        '''
        self.eye_data[const.LEFT] = [left_og_x, left_og_y]
        self.eye_data[const.RIGHT] = [right_og_x, right_og_y]

    def update_eye_recording_method_parameters(self, eye_recording_method=None, eye_recording_method_name=None,
                                               eye_coil_channels=None, eye_pos=None):
        '''
        Update eye recording method and channel
        :param eye_recording_method:
        :param eye_recording_method_name:
        :param eye_coil_channels:
        :param eye_pos:
        :return:
        '''
        if eye_recording_method is not None:
            self.eye_recording_method = eye_recording_method
            self.analaog_input_output['eye_recording_method'] = eye_recording_method

        if eye_recording_method_name is not None:
            self.eye_recording_method_name = eye_recording_method_name
            self.analaog_input_output['eye_recording_method_name'] = eye_recording_method_name

        if eye_coil_channels is not None:
            self.analaog_input_output['eye_coil_channels'] = eye_coil_channels

        if eye_pos is not None:
            self.analaog_input_output['analog_channel']['left_x'] =  eye_pos[0]
            self.analaog_input_output['analog_channel']['left_y'] = eye_pos[1]
            self.analaog_input_output['analog_channel']['left_z'] = eye_pos[2]
            self.analaog_input_output['analog_channel']['right_x'] = eye_pos[3]
            self.analaog_input_output['analog_channel']['right_y'] = eye_pos[4]
            self.analaog_input_output['analog_channel']['right_z'] = eye_pos[5]

    def update_eye_in_out(self, left_eye_in_out, right_eye_in_out):
        '''
        Update if eye is inside a particular window or out
        :param left_eye_in_out:
        :param right_eye_in_out:
        :return:
        '''
        self.eye_in_or_out = [left_eye_in_out, right_eye_in_out]

    def update_last_sent_eye_in_out(self, value):
        self.last_sent_eye_in_out = value

    def update_vergence_error_to_plot(self, vergence_error_x, vergence_error_y, vergence_window):
        '''
        Vergence error to display on the UI
        :param vergence_error_x:
        :param vergence_error_y:
        :return:
        '''
        self.vergence_error_to_plot[const.X] = vergence_error_x
        self.vergence_error_to_plot[const.Y] = vergence_error_y
        self.vergence_error_to_plot[2] = vergence_window

    def udpdate_vergence_display(self, value):
        self.display_vergence = value

    def update_last_sent_vergence_error(self, value):
        self.last_vergence_error_sent = value

    def update_raw_eye_data_sample(self, left_eye_x, left_eye_y, right_eye_x, right_eye_y, remove=False, append=False):
        '''
        Raw eye data updated to a list. A sample of data is used to calculate the mean
        :param left_eye_x:
        :param left_eye_y:
        :param right_eye_x:
        :param right_eye_y:
        :param remove:
        :param append:
        :return:
        '''
        if remove:
            # Delete the first entry in the list
            del self.raw_eye_data_sample[const.LEFT][0]
            del self.raw_eye_data_sample[const.RIGHT][0]

        if append:
            # Add the new values to the end
            self.raw_eye_data_sample[const.LEFT].append([left_eye_x, left_eye_y])
            self.raw_eye_data_sample[const.RIGHT].append([right_eye_x, right_eye_y])

    def update_centre_point(self, no_of_points, centre_of_windows):
        '''
        Update centre point
        :param x:
        :param y:
        :param diameter:
        :param index:
        '''
        if not no_of_points or no_of_points != self.centre_of_windows:
            self.centre_of_windows = []

        for i in range(no_of_points):
            # if present update it
            if i < len(self.centre_of_windows):
                self.centre_of_windows[i] = centre_of_windows[i]
            else:
                # if not present add it
                self.centre_of_windows.append(centre_of_windows[i])

    def update_centre_window_on_off(self, status=True):
        self.centre_window_on = status

    def update_log_dump_callback(self, log_to_text):
        '''
        Callback function to dump logs
        :param log_to_text:
        :return:
        '''
        self.dump_log = log_to_text

    def update_arbitrator_server_socket(self, sock, sock_eye):
        self.arbitrator_sock = sock
        self.arbitrator_sock_addr = (self.config_param['arbitrator_service']['server_ip'],
                                     self.config_param['arbitrator_service']['server_port'])
        self.arbitrator_sock_eye = sock_eye
        self.arbitrator_sock_addr_eye = (self.config_param['arbitrator_service']['server_ip'],
                                     self.config_param['arbitrator_service']['server_port_eye'])

    def update_task_display_filename(self, reset=None, task_file=None, display_file=None):
        if reset is not None:
            self.task_filename = None
            self.display_filename = None

        if task_file is not None:
            self.task_filename = task_file

        if display_file is not None:
            self.display_filename = display_file

    def update_arbitrator_server_screen_resolution(self, width=None, height=None):
        if width:
            self.arbitrator_window_width = width

        if height:
            self.arbitrator_window_height = height

        self.update_gui_scale_factor()
        # Update the subject configuration file since this is unlikely to change
        #self.subject_configuration['arbitrator_display_screen']['window_width_pixel'] = width
        #self.subject_configuration['arbitrator_display_screen']['window_height_pixel'] = height

    def update_gui_scale_factor(self):
        # Depending on the GUI display calculate the scale factor
        # scale factor width = 3rd part server width / (canvas relative width * canvas frame relative width * gui width)

        #self.arbitrator_display['x_scale_factor'] = self.arbitrator_window_width/self.eye_canvas_pix_w
        #self.arbitrator_display['y_scale_factor'] = self.arbitrator_window_height/self.eye_canvas_pix_h
        self.eye_canvas_width = (self.gui_display['canvas_width'] * self.gui_display['canvas_frame_width'] * self.gui_display['width'])
        self.eye_canvas_height = (self.gui_display['canvas_height'] * self.gui_display['canvas_frame_height'] * self.gui_display['height'])

        self.arbitrator_display['x_scale_factor'] = \
            self.arbitrator_window_width /self.eye_canvas_width


        # scale factor height = 3rd part server height / (canvas relative height * canvas frame relative height * gui height)
        self.arbitrator_display['y_scale_factor'] = \
            self.arbitrator_window_height /self.eye_canvas_height

        self.dump_log("Scale factor Number x: {} y: {}".format(self.arbitrator_display['x_scale_factor'], self.arbitrator_display['y_scale_factor']))
        #print(self.arbitrator_display['x_scale_factor'],self.arbitrator_display['y_scale_factor'])
        #print((self.gui_display['canvas_width'] * self.gui_display['canvas_frame_width'] * self.gui_display['width']),
              #(self.gui_display['canvas_height'] * self.gui_display['canvas_frame_height'] * self.gui_display['height']))
        #print(self.arbitrator_window_width,self.arbitrator_window_height)

    def update_gui_display_param(self, width, height, canvas_frame_width, canvas_frame_height,
                                 canvas_width, canvas_height):
        self.gui_display['width'] = width
        self.gui_display['height'] = height
        self.gui_display['canvas_frame_width'] = canvas_frame_width
        self.gui_display['canvas_frame_height'] = canvas_frame_height
        self.gui_display['canvas_width'] = canvas_width
        self.gui_display['canvas_height'] = canvas_height

    def update_displayable_config(self, config=None):
        if config:
            self.displayable_config[config[0]] = config[1]
            # print('Config 0:', self.displayable_config)
            # print('Config 1:', config)

        else:
            self.displayable_config = {}

    def update_depth(self, value):
        for tp in self.centre_of_windows:
            tp[2] = value
        self.depth = value

    def update_calibration_config(self, config):
        self.calibration_config = config

    def update_load_subject_task_config_flag(self, value):
        self.load_subject_task_config_flag = value

    def update_raw_eye_task_data(self, data):
        if len(data):
            self.raw_eye_task_data.append(data)
        else:
            self.raw_eye_task_data = []

    def update_last_raw_eye_data(self, lx, ly, rx, ry):
        self.last_raw_eye_data = [lx, ly, rx, ry]

    def update_drawing_object_on(self, value):
        self.drawing_object_on = value

    def update_drawing_object_pos(self, i, ii, value):
        self.drawing_object_pos[i][ii] = value

    def update_drawing_object_number(self, value):
        self.drawing_object_number = value

    def update_shock_flag(self, value):
        self.Shocked = value

    def get_shock_flag(self):
        Shock_flag = self.Shocked
        return Shock_flag

    def shock_on(self):
        # self.prt.setData(1)
        self.Shocked=1

    def shock_off(self):
        # self.prt.setData(0)
        self.Shocked=0

    def update_cont_data(self, value):
        self.DUMP_DATA_CONTINUALLY = value

Globals = GlobalParams()
