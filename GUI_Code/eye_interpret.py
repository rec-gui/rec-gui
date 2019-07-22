'''
Code to read eye data from eyelink or analog input
'''
import importlib
import time
import numpy as np
import utility as util
from constants import Constant as const, ConfigLabels, EyeRecordingMethods
from vergence_version import ValidateVergenceVersion
from calibration import Calibration as calibration
from data_collection import DataFileObj
from logger import logging
log = logging.getLogger(__name__)

from global_parameters import Globals as globls

class EyeInterpret:
    def __init__(self):
        #   globls.dump_log("Initiated eye data reader thread")
        self.EyeTrack = None
        self.eye_recording_thread = None
        self.analog_reader_obj = None
        self.calibration = calibration()
        self.eye_check = ValidateVergenceVersion()

        # Initialize based on the recording method selection
        if globls.eye_recording_method == EyeRecordingMethods.EYE_LINK:
            self.digital_reader()
        elif globls.eye_recording_method == EyeRecordingMethods.EYE_COIL:
            self.analog_reader()

    def digital_reader(self):
        pylink = importlib.import_module('pylink')

        '''
        Read the eye data from eyelink
        :return:
        '''
        try:
            self.EyeTrack = pylink.EyeLink(globls.config_param['eyelink_service']['ip'])
            self.EyeTrack.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,AREA")
            self.EyeTrack.startRecording(0, 0, 1, 1)
            globls.dump_log("Initiated digital eye data reader")

            last_read_eye_time = 0

            while globls.is_program_running:
                # Sleep for 1 ms
                time.sleep(.001)

                dt = self.EyeTrack.getNewestSample()  # check for new sample update
                eye_recv_data_ts = time.time()
                if dt is not None:
                    cur_eye_time = dt.getTime()
                    if float(cur_eye_time) != float(last_read_eye_time):
                        eye_closed = False
                        lx = ly = rx = ry = 0

                        if dt.getRightEye() and dt.getLeftEye():
                            lx, ly = dt.getLeftEye().getGaze()
                            rx, ry = dt.getRightEye().getGaze()
                        elif dt.getRightEye() and not dt.getLeftEye():
                            rx, ry = dt.getRightEye().getGaze()
                            lx, ly = rx, ry
                        elif dt.getLeftEye() and not dt.getRightEye():
                            lx, ly = dt.getLeftEye().getGaze()
                            rx, ry = lx, ly

                        pupilsize_left = dt.getLeftEye().getPupilSize()
                        pupilsize_right = dt.getRightEye().getPupilSize()

                        # # Do not update values if eye is closed or if eye is not avaialble
                        # if (pupilsize_left < globls.pupil_size['left'] or
                        #             pupilsize_right > globls.pupil_size['right']):
                        #     eye_closed = True
                        # print pupilsize_left, globls.pupil_size['right']

                        # convert this to coordinate (0, 0) at center
                        eyepos_lx, eyepos_ly = util.shift_to_centre(lx, ly)
                        eyepos_lx, eyepos_ly = util.convert_pix_to_mm(eyepos_lx, eyepos_ly)

                        # convert this to coordinate (0, 0) at center
                        eyepos_rx, eyepos_ry = util.shift_to_centre(rx, ry)
                        eyepos_rx, eyepos_ry = util.convert_pix_to_mm(eyepos_rx, eyepos_ry)

                        # Write eye data to list storing left and right X, Y and Z data
                        # data that we get from eyelink has only left and right eye
                        globls.update_last_raw_eye_data(eyepos_lx, eyepos_ly, eyepos_rx, eyepos_ry)
                        DataFileObj.save_raw_eye_taskdata(eye_recv_data_ts, eyepos_lx, eyepos_ly, eyepos_rx, eyepos_ry)


                        # Get the mean of the raw eye data and later apply offset gain for the mean data
                        left_mean_x, left_mean_y, right_mean_x, right_mean_y = \
                            self.update_getmean_eye_sample(eyepos_lx, eyepos_ly,
                                                           eyepos_rx, eyepos_ry, eye_closed)

                        # apply offset and gain
                        left_og_x, left_og_y, right_og_x, right_og_y = \
                            self.get_offset_gain_applied_eye_data(left_mean_x, left_mean_y, right_mean_x,
                                                                              right_mean_y)

                        # update the offset and gain applied for drawing eye on canvas
                        globls.update_offset_gain_applied_eye_data(left_og_x, left_og_y, right_og_x,
                                                                                     right_og_y)

                        # If eye closed, then do not check eye in out or vergence error
                        if eye_closed:
                            return

                        # Validate the eye is in or out depending on the task
                        self.eye_check.eye_in_out()

                        # print "Eye position ", eyepos_lx, left_mean_x, left_og_x


                    last_read_eye_time = cur_eye_time
        except Exception as e:
            log.exception(e)
            globls.dump_log('Exception reading eye link data from eyelink tracker {}'.format(e))


    def analog_reader(self):
        analog_module = importlib.import_module('analog')
        analog = getattr(module, 'Analog')

        '''
        Read the eye data from Analog device
        :return:
        '''
        try:
            globls.dump_log("Initiated Analog eye data reader")
            self.analog_reader_obj = analog()
            while globls.is_program_running:
                time.sleep(.001)
                eye_closed = False

                pupilsize_left, pupilsize_right = 2000, 2000
                temp_eye_data = []

                temp_eye_pos_channel_data = globls.eye_recording_method_obj.get_eye_positions_channel()
                for channel in temp_eye_pos_channel_data:
                    temp_eye_data.append(self.analog_reader_obj.get_channel_analog_value(int(channel)))
                eye_recv_data_ts = time.time()

                eyepos_lx, eyepos_ly = temp_eye_data[0], temp_eye_data[1]
                eyepos_rx, eyepos_ry = temp_eye_data[0], temp_eye_data[1]

                # Do not update values if eye is closed or if eye is not avaialble
                if (pupilsize_left < globls.pupil_size['left'] or
                            pupilsize_right < globls.pupil_size['right']):
                    eye_closed = True

                # Write eye data to list storing left and right X, Y and Z data
                # data that we get from eyelink has only left and right eye
                globls.update_last_raw_eye_data(eyepos_lx, eyepos_ly, eyepos_rx, eyepos_ry)
                DataFileObj.save_raw_eye_taskdata(eye_recv_data_ts, eyepos_lx, eyepos_ly, eyepos_rx, eyepos_ry)

                # Get the mean of the raw eye data and later apply offset gain for the mean data
                left_mean_x, left_mean_y, right_mean_x, right_mean_y = \
                    self.update_getmean_eye_sample(eyepos_lx, eyepos_ly,
                                                   eyepos_rx, eyepos_ry, eye_closed)

                # apply offset and gain
                left_og_x, left_og_y, right_og_x, right_og_y = \
                    self.get_offset_gain_applied_eye_data(left_mean_x, left_mean_y, right_mean_x,
                                                                      right_mean_y)

                globls.update_offset_gain_applied_eye_data(left_og_x, left_og_y, right_og_x,
                                                                             right_og_y)

                # If eye closed, then do not check eye in out
                if eye_closed:
                    return

                # Validate the eye is in or out depending on the task
                self.eye_check.eye_in_out()

        except Exception as e:
            log.exception(e)
            # globls.dump_log('Exception reading eye link data from eyelink tracker {}'.format(e),
            #          const.MessageType.ERROR)

    def update_getmean_eye_sample(self, left_eye_x, left_eye_y, right_eye_x, right_eye_y, eye_closed):
        '''
        Update the eye sample to get the mean
        :param left_eye_x:
        :param left_eye_y:
        :param right_eye_x:
        :param right_eye_y:
        :param eye_closed:
        :return:
        '''
        if eye_closed:
            return [0, 0, 0, 0]

        # update the raw eye sample to global variable
        globls.update_raw_eye_data_sample(left_eye_x, left_eye_y, right_eye_x, right_eye_y, remove=True, append=True)

        # calculate the mean and return the mean value
        eye_data_array = np.array(globls.raw_eye_data_sample)
        left_mean = np.mean(eye_data_array[const.LEFT], axis=0).tolist()
        right_mean = np.mean(eye_data_array[const.RIGHT], axis=0).tolist()

        # return left (x, y) mean right (x, y) mean
        return left_mean[0], left_mean[1], right_mean[0], right_mean[1]

    def get_offset_gain_applied_eye_data(self, left_mean_x, left_mean_y, right_mean_x, right_mean_y):
        '''
        Apply offset and gain to the raw eye data
        '''
        # LEFT Eye
        left_eye_x = float(left_mean_x * globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_X] +
                           globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_X])

        left_eye_y = float(left_mean_y * globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_Y] +
                           globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_Y])

        # RIGHT Eye
        right_eye_x = float(right_mean_x * globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_X] +
                            globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_X])

        right_eye_y = float(right_mean_y * globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_Y] +
                            globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_Y])

        return left_eye_x, left_eye_y, right_eye_x, right_eye_y




