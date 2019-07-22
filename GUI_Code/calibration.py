'''
   Calibrating the eye movements
'''
import time
import os
import numpy as np
from numpy.linalg import inv
import utility as util
from file import File
from data_collection import DataFileObj
from constants import Constant as const, ConfigLabels
from global_parameters import Globals as globls
from logger import logging
log = logging.getLogger(__name__)


class Calibration():
    def __init__(self):
        self.file_obj = File()
        self.eye_pos_samples = [
            [[0] * 2] * globls.constant['moving_eye_position_mean'],
            [[0] * 2] * globls.constant['moving_eye_position_mean']]

    def init_calibration_parameter(self):
        '''
        Initialize the calibration parameters. This would be called during init and when a clear
        calibration is initiated.
        '''
        # Maintains list of positions used for calibration in the format [R[(x,y),..], L[(x,y)...]]
        self.true_eyepos = [[], []]

        # Measured eye position has the mean of the 100 samples for any given position
        self.measured_eyepos = [[], []]

        self.accepted_eyepos_ploted_widget = []

    def process_accept_measured_eye_pos(self):
        '''
        Accept the measured eye position to calculate the offset and gain
        :return:
        '''
        # Send Reward to Arbitrator server. Comment this if not required
        data = "{} {}/".format(const.REWARD, 1)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data, msg="Reward signal")
        ts = time.time()

        # Retrieve the accepted mean eye value from global parameter and
        # store those values for further calculation
        left_mean = globls.eye_data[const.LEFT]
        right_mean = globls.eye_data[const.RIGHT]

        self.measured_eyepos[const.LEFT].append(left_mean)
        self.measured_eyepos[const.RIGHT].append(right_mean)

        # get and save the true position of the center point
        true_pos_leftx, true_pos_lefty, true_pos_rightx, true_pos_righty = \
            util.get_disparity_offset_applied_points(globls.centre_of_windows[0][0],
                                                       globls.centre_of_windows[0][1],
                                                       globls.centre_of_windows[0][2])

        self.true_eyepos[const.LEFT].append([true_pos_leftx, true_pos_lefty])
        self.true_eyepos[const.RIGHT].append([true_pos_rightx, true_pos_righty])

        # save data in the data file 6, 151, Ltruepox, Ltrueposy, Rtrueposx, Rtrueposy,
        # LXmean, LYmean, RXmean, RYmean
        data_to_save = "{} {} {} {} {} {} {} {} {} {}".format(const.CLIENT_CALIBRATION_COMMAND,
                                                              const.CALIBRATION_ACCEPTED_VALUES,
                                                              true_pos_leftx, true_pos_lefty, true_pos_rightx,
                                                              true_pos_righty, left_mean[const.X],
                                                              left_mean[const.Y], right_mean[const.X],
                                                              right_mean[const.Y])
        DataFileObj.save_raw_eye_taskdata(
            ts,
            globls.last_raw_eye_data[0], globls.last_raw_eye_data[1],
            globls.last_raw_eye_data[2], globls.last_raw_eye_data[3],
            task_data=data_to_save)
        return left_mean, right_mean

    def get_length_of_accepted_moving_eye_position(self):
        '''
        length of accepted measured eye position
        :return:
        '''
        return len(self.true_eyepos[const.LEFT])

    def calculate_offset_gain(self):
        '''
        calculate offset and gain
        :return:
        '''
        # Flag for enabling Auto calibration
        self.enable_auto_calibration_data_collect = False

        # Need to transpose as the values are appended as rows into a list
        measured_eyepos_transpose = np.transpose(self.measured_eyepos, (0, 2, 1))
        true_eye_pos_transpose = np.transpose(self.true_eyepos, (0, 2, 1))

        # Form a matrix by adding ones to each measured eye position list of R and L (x, y) position
        measured_eyepos_matrix_lx = np.matrix(np.vstack(
            (measured_eyepos_transpose[const.LEFT][const.X],
             np.ones(len(measured_eyepos_transpose[const.LEFT][const.X])))))
        measured_eyepos_matrix_ly = np.matrix(np.vstack(
            (measured_eyepos_transpose[const.LEFT][const.Y],
             np.ones(len(measured_eyepos_transpose[const.LEFT][const.Y])))))
        measured_eyepos_matrix_rx = np.matrix(np.vstack(
            (measured_eyepos_transpose[const.RIGHT][const.X],
             np.ones(len(measured_eyepos_transpose[const.RIGHT][const.X])))))
        measured_eyepos_matrix_ry = np.matrix(np.vstack(
            (measured_eyepos_transpose[const.RIGHT][const.Y],
             np.ones(len(measured_eyepos_transpose[const.RIGHT][const.Y])))))

        # Convert it to matrix for performing matrix multiplication as a list multiplication and
        # array multiplication of different dimensions are not allowed
        true_eye_pos_lx = np.matrix(true_eye_pos_transpose[const.LEFT][const.X])
        true_eye_pos_ly = np.matrix(true_eye_pos_transpose[const.LEFT][const.Y])
        true_eye_pos_rx = np.matrix(true_eye_pos_transpose[const.RIGHT][const.X])
        true_eye_pos_ry = np.matrix(true_eye_pos_transpose[const.RIGHT][const.Y])

        try:
            # offsetgain = TEP * (MEP' * (inv(MEP * MEP'))) 'TEP->True eye pos' 'MEP -> Measure eye pos'
            reconstructed_offsetgain_lx = np.array(
                true_eye_pos_lx * (measured_eyepos_matrix_lx.transpose() *
                                    inv(measured_eyepos_matrix_lx * measured_eyepos_matrix_lx.transpose())))

            reconstructed_offsetgain_ly = np.array(
                true_eye_pos_ly * (measured_eyepos_matrix_ly.transpose() *
                                    inv(measured_eyepos_matrix_ly * measured_eyepos_matrix_ly.transpose())))

            reconstructed_offsetgain_rx = np.array(
                true_eye_pos_rx * (measured_eyepos_matrix_rx.transpose() *
                                   inv(measured_eyepos_matrix_rx * measured_eyepos_matrix_rx.transpose())))
            reconstructed_offsetgain_ry = np.array(
                true_eye_pos_ry * (measured_eyepos_matrix_ry.transpose() *
                                   inv(measured_eyepos_matrix_ry * measured_eyepos_matrix_ry.transpose())))

        except Exception as e:
            log.exception(e)
            print "measured_eyepos_matrix_ly", measured_eyepos_matrix_ly
            print "measured_eyepos_matrix_lx", measured_eyepos_matrix_lx
            return

        # new gain is calculated as
        # Gain =  New_gain * Old_gain
        # offset = new_offset + ( new gain * old_offset )
        updated_gain_lx = reconstructed_offsetgain_lx[0][0] * globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_X]
        updated_off_lx = reconstructed_offsetgain_lx[0][1] + \
                         (reconstructed_offsetgain_lx[0][0] * globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_X])

        updated_gain_ly = reconstructed_offsetgain_ly[0][0] * globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_Y]
        updated_off_ly = reconstructed_offsetgain_ly[0][1] + \
                         (reconstructed_offsetgain_ly[0][0] * globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_Y])

        updated_gain_rx = reconstructed_offsetgain_rx[0][0] * globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_X]
        updated_off_rx = reconstructed_offsetgain_rx[0][1] + \
                         (reconstructed_offsetgain_rx[0][0] * globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_X])

        updated_gain_ry = reconstructed_offsetgain_ry[0][0] * globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_Y]
        updated_off_ry = reconstructed_offsetgain_ry[0][1] + \
                         (reconstructed_offsetgain_ry[0][0] * globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_Y])

        # Update the config
        globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_X] = updated_gain_lx
        globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_X] = updated_off_lx
        globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_Y] = updated_gain_ly
        globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_Y] = updated_off_ly
        globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_X] = updated_gain_rx
        globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_X] = updated_off_rx
        globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_Y] = updated_gain_ry
        globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_Y] = updated_off_ry

        # Save the True eye position and Measured value to a file
        data_dict = {}
        data_dict['true_eye_pos'] = {'left': self.true_eyepos[const.LEFT],
                                     'right': self.true_eyepos[const.RIGHT]}
        data_dict['measured_eye_pos'] = {'left': self.measured_eyepos[const.LEFT],
                                         'right': self.measured_eyepos[const.RIGHT]}
        data_dict['gain_offset'] = {'Gain Left(x, y)': [updated_gain_lx, updated_gain_ly],
                                    'Offset Left(x, y)': [updated_off_lx, updated_off_ly],
                                    'Gain Right(x, y)': [updated_gain_rx, updated_gain_ry],
                                    'Offset Right(x, y)': [updated_off_rx, updated_off_ry],}

        filename_with_path = os.path.join(globls.directories['configuration'], (globls.subject_name + '.calibration'))
        self.file_obj.write(data_dict, filename_with_path)

    def cancel_last_accepted_data(self):
        '''
            Remove the last index
        '''
        self.measured_eyepos[const.LEFT].pop(-1)
        self.measured_eyepos[const.RIGHT].pop(-1)
        self.true_eyepos[const.LEFT].pop(-1)
        self.true_eyepos[const.RIGHT].pop(-1)

CalibrationObj = Calibration()






