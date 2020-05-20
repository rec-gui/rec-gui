'''
   constants
'''

import os


class Constant:
    # DUMP_DATA_CONTINUALLY = 0   # This should be in config file
    MAX_NO_OF_LINES_TO_DISPLAY = 500  # Maximum no of lines that can be written in text window

    # Files where it will be stored
    CUR_DIR_NAME = os.path.dirname(__file__)  # relative directory path
    DEFAULT_CONFIG_FILE = 'default.conf'
    SUBJECT_DEFAULT_CONFIG_FILE = "subject_default.conf"

    DATA_DIR = os.path.join(CUR_DIR_NAME, 'data')
    LOG_DIR = os.path.join(CUR_DIR_NAME, 'logs')
    CONFIGURATION_DIR = os.path.join(CUR_DIR_NAME, 'subject_configuration')

    # Timers:
    GUI_PERIODIC_CALL = 40   # ms
    MAXIMUM_CENTRE_OF_WINDOW = 30

    # X, Y, Z, index to grab from the data
    X = 0
    Y = 1
    Z = 2

    # Eye indexes
    LEFT = 0
    RIGHT = 1
    TWAIN = 2

    # Color constants to draw the widget
    LEFT_EYE_COLOR = '#09cc00'  # '#21762e'  # green
    RIGHT_EYE_COLOR = '#0000db'  # red

    # Constants related to messages, to be sent to and received from Arbitrator server
    # Command -1 to -100 used for internal use
    COMMAND_WORD_CONNECTION = -1
    CONNECTION_START = 8256
    CONNECTION_ACK = 8257

    COMMAND_WORD_CONTROL = -2
    CONTROL_START = 100
    CONTROL_STOP = 101
    CONTROL_PAUSE = 102
    CONTROL_EXIT = 103
    LOAD_SUBJECT = 104
    SAVE_SUBJECT = 105
    LOAD_TASK = 106
    SAVE_TASK = 107
    ACCEPT = 108
    CANCEL = 109
    CALIBRATE = 110
    CLEAR = 111

    SCREEN_HEIGHT = -3
    SCREEN_DISTANCE = -4
    SCREEN_WIDTH = -5
    SCREEN_IOD = -6

    TARGET_ON = -9
    TARGET_OFF = -10
    TARGET_X = -11
    TARGET_Y = -12
    TARGET_Z = -13

    LEFT_EYE_STATUS = -14
    RIGHT_EYE_STATUS = -15
    VERGENCE_STATUS = -16
    REWARD = -17

    RECEPTIVE_STIM = -18
    DOT_DENISTY = -19
    DOT_SIZE = -20
    DOT_DIRECTION = -21
    FIELD_SIZE = -22
    FIELD_DEPTH = -23
    GRATING_CONTRAST = -24
    ORIENTATION = -25
    TEMP_FREQ = -26
    SPAT_FREQ = -27
    DOT_SPEED = -28
    PULSE_DURA = -29
    PULSE_ITI = -30
    XFIX = -31
    YFIX = -32
    ZFIX = -33
    BAR_HEIGHT = -34
    BAR_WIDTH = -35
    BAR_COLOR_R = -36
    BAR_COLOR_G = -37
    BAR_COLOR_B = -38

    # Command from 3rd party server
    # Number 1 to 100 reserver for internal use
    DISPLAY_COMMAND_WORD = 1
    CLIENT_CALIBRATION_COMMAND = 2
    CALIBRATION_ACCEPTED_VALUES = 3

    EYE_IN_OUT_REQUEST = 4
    VERGENCE_REQUEST = 5
    EVENTS = 6
    EVENT_START = 111
    EVENT_STOP = 112
    '''This is your MATLAB window width and height in pixels'''
    SCREEN_WINDOW_WIDTH = 7
    SCREEN_WINDOW_HEIGHT = 8
    DRAW_EVENTS = 9

    # Keep 1 to 99 just for this
    CENTRE_OF_WINDOWS = 50
    WINDOW_ON = 51
    WINDOW_OFF = 52
    VERGENCE_ON = 53
    VERGENCE_OFF = 54
    REWARD_ON = 60
    REWARD_OFF = 61

class MessageType:
    DEBUG = "Debug"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"


class EyeRecordingMethods:
    EYE_LINK = 0
    EYE_COIL = 1
    EYE_NONE = 2

class Vergence:
    UNSELECTED = 0
    HORIZONTAL_VERTICAL = 1
    HORIZONTAL = 2

class MouseClick:
    FEEDBACK = 1
    DRAGGING = 2

class Task:
    CALIBRATION = 1
    RECEPTIVE_FIELD_MAPPING = 2

class Calibration:
    MANUAL = 1
    AUTO = 2

class FieldMapping:
    DOTS = 1
    GRATING = 2
    BAR = 3

class EyeCoilChannelId:
    C1 = 0
    C2 = 1
    C3 = 2
    C4 = 3
    C5 = 4
    C6 = 5
    C7 = 6
    C8 = 7
    C9 = 8
    C10 = 9
    C11 = 10
    C12 = 11
    C13 = 12
    C14 = 13
    C15 = 14
    C16 = 15


class TrialsStats:
    TRIAL_LABEL_1 = 0
    TRIAL_LABEL_2 = 1
    TRIAL_LABEL_3 = 2
    TRIAL_LABEL_4 = 3
    TRIAL_LABEL_5 = 4
    TRIAL_LABEL_6 = 5
    TRIAL_LABEL_7 = 6
    TRIAL_LABEL_8 = 7
    TRIAL_LABEL_9 = 8
    TRIAL_LABEL_10 = 9


class ConfigLabels:

    LEFT_EYE_GAIN_X = 'left_gain_x'
    LEFT_EYE_OFFSET_X = 'left_offset_x'
    LEFT_EYE_GAIN_Y = 'left_gain_y'
    LEFT_EYE_OFFSET_Y = 'left_offset_y'
    RIGHT_EYE_GAIN_X = 'right_gain_x'
    RIGHT_EYE_OFFSET_X = 'right_offset_x'
    RIGHT_EYE_GAIN_Y = 'right_gain_y'
    RIGHT_EYE_OFFSET_Y = 'right_offset_y'
    PUPIL_SIZE_L = 'left'
    PUPIL_SIZE_R = 'right'

    # Label + Scroll box
    NUMBER_OF_REPETITION = 'number_of_repetition'
    MOVING_SD_LIMIT = 'moving_sd_limit'
    MOVING_SD_TIME_LIMIT = 'moving_sd_time_limit'

    # check buttons
    LEFT = 'left_eye'
    RIGHT = 'right_eye'


CalibrationDirList = ['NW', 'N', "NE", 'W', 'C', 'E', 'SW', 'S', 'SE']
class CalibrationListIndex:
    NORTH_WEST = 0
    NORTH = 1
    NORTH_EAST = 2
    WEST = 3
    CENTER = 4
    EAST = 5
    SOUTH_WEST = 6
    SOUTH = 7
    SOUTH_EAST = 8




