'''
Utility to send data to 3rd party server, convertion function
'''

import math
from constants import Constant as const
from logger import logging
log = logging.getLogger(__name__)
from global_parameters import Globals as globls


# Add padding to the data for sending
def data_padder(src_string, data_length=globls.constant['data_size_length'],
                padding_char=globls.constant['data_padding_character']):
    # cursize = sys.getsizeof(src_string)
    cursize = len(src_string)
    if cursize <= data_length:
        for i in range(data_length - cursize):
            src_string += padding_char
        return src_string
    else:
        return src_string


# Send data to any process provided socket and address is provided
def send_data(sock, dest_addr, data_string, msg=None):
    # data = data_string
    tmp_msg = ''
    if dest_addr:
        data_string = data_padder(data_string)
        data = data_string.encode()
        try:
            sock.sendto(data, dest_addr)
            if msg is not None:
                tmp_msg = tmp_msg + msg
                globls.dump_log('{}. length {}. Data {}'.format(tmp_msg, len(data_string), data_string))
            return  data
        except Exception as e:
            log.exception(e)
            tmp_msg = 'Exception Sending ' + msg if msg else ''
    else:
        tmp_msg = 'Matlab socket not initilized to Send ' + msg if msg else ''
    globls.dump_log('Error: {}'.format(tmp_msg))
    return data

def convert_bit_to_int(lst):
    num = 0
    for l in lst:
        t = 1 << l
        num |= t
    return num


# Get the list of bits that are set
def convert_int_to_bitlist(value):
    bit_set = []
    for i in range(16):
        if value & (1 << i):
            bit_set.append(i)
    return bit_set


# Functions which are used converting from one scale to another
def convert_deg_to_mm(x_deg=None, y_deg=None):
    x_mm = y_mm = 0
    if x_deg is not None:
        x_mm = math.tan(math.radians(x_deg)) * globls.arbitrator_display['screen_distance_mm']
    if y_deg is not None:
        y_mm = math.tan(math.radians(y_deg)) * globls.arbitrator_display['screen_distance_mm']
    return x_mm, y_mm


def convert_deg_to_pix(x_deg=None, y_deg=None):
    x_mm, y_mm = convert_deg_to_mm(x_deg, y_deg)
    x_pix, y_pix = convert_mm_to_pix(x_mm,  y_mm)
    return x_pix, y_pix


def convert_pix_to_mm(x_pix=None, y_pix=None):
    x_mm = y_mm = 0
    if x_pix:
        x_mm = x_pix / globls.arbitrator_display['xscale_mm']
    if y_pix:
        y_mm = y_pix / globls.arbitrator_display['yscale_mm']
    return x_mm, y_mm


def convert_pix_to_deg(x_pix=None, y_pix=None, screen_distance=None):
    x_deg = y_deg = 0
    x_mm, y_mm = convert_pix_to_mm(x_pix, y_pix)
    if x_pix is not None:
        x_deg = math.degrees(math.atan(x_mm / screen_distance))
    if y_pix is not None:
        y_deg = math.degrees(math.atan(y_mm / screen_distance))
    return x_deg, y_deg


# Cross check this this is not used as of now but needs to be checked
def convert_mm_to_deg(x_mm=None, y_mm=None):
    x_deg = y_deg = 0
    if x_mm is not None:
        x_deg = math.degrees(math.atan(x_mm / globls.arbitrator_display['screen_distance_mm']))
    if y_mm is not None:
        y_deg = math.degrees(math.atan(y_mm / globls.arbitrator_display['screen_distance_mm']))
    return x_deg, y_deg


def convert_mm_to_pix(x_mm=None, y_mm=None):
    x_pix = y_pix = 0
    if x_mm is not None:
        x_pix = x_mm * globls.arbitrator_display['xscale_mm']
    if y_mm is not None:
        y_pix = y_mm * globls.arbitrator_display['yscale_mm']
    return x_pix, y_pix


# UIConstants.WINDOW_WIDTH_IN_PIXEL / 2 -> (0, 0) is the centre of the screen
def shift_to_centre(x_pix, y_pix):
    new_x = x_pix - (globls.arbitrator_window_width / 2)
    new_y = (globls.arbitrator_window_height / 2) - y_pix
    return new_x, new_y


def shift_to_top_left(x_pix, y_pix):
    new_x = x_pix + (globls.arbitrator_window_width / 2)
    new_y = (globls.arbitrator_window_height / 2) - y_pix
    return new_x, new_y


def get_disparity_offset_applied_points(x, y, z):
    '''
    Update disparity offset
    :param index:
    :return:
    '''
    # [Left eye, right eye]

    disparity_x = [0, 0]
    y_offset = 0
    if z:
        eye_location = [-globls.arbitrator_display['iod_mm']/2, (globls.arbitrator_display['iod_mm']/2)]

        for eye in eye_location:
            disparity_x[eye_location.index(eye)] = ((eye - x)/(globls.arbitrator_display['screen_distance_mm'] + z))*z

        y_offset = y * (y + globls.arbitrator_display['screen_distance_mm']) / globls.arbitrator_display['screen_distance_mm'] - y

    left_x = x + disparity_x[0]
    left_y = y + y_offset
    right_x = x + disparity_x[1]
    right_y = y + y_offset


    return left_x, left_y, right_x, right_y

# disparity=zeros(1,2);
# EyeLocation = [-1,1]*(IOD/2);  %% EyeLocation(1) = left eye, EyeLocation(2) = right eye
# for i=1:length(EyeLocation)
#     disparity(i) = (EyeLocation(i)-XPos)/(ScDist+ZPos)*ZPos;
# end
# Yoffset = YPos*(ZPos+ScDist)/ScDist-YPos;

def send_screen_parameters():
    # send the subject specific configuration to 3rd party server
    data = '{} {}/{} {}/{} {}/{} {}/'.format(
        const.SCREEN_HEIGHT, globls.arbitrator_display['screen_height_mm'],
        const.SCREEN_DISTANCE, globls.arbitrator_display['screen_distance_mm'],
        const.SCREEN_WIDTH, globls.arbitrator_display['screen_width_mm'],
        const.SCREEN_IOD, globls.arbitrator_display['iod_mm']
    )
    send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr,
                   data, 'Screen configuration sent to 3rd party server')
