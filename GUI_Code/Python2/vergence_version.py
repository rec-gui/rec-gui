'''
Eye in or out of window
vergence error calculation
'''
import math
import utility as util
from constants import Constant as const, Vergence
from global_parameters import Globals as globls


class ValidateVergenceVersion():
    def __init__(self):
        pass

    @staticmethod
    def _is_eye_in(eye_pos_x, eye_pos_y, win_x1, win_y1, fix_win_size):
        dist = math.sqrt(pow((win_x1 - eye_pos_x), 2) + pow((win_y1 - eye_pos_y), 2))
        result = dist <= fix_win_size
        return result

    def eye_in_out(self):
        '''
            Validate the version data
            Eye in or out of the specific window
        '''
        left_eye_x = globls.eye_data[const.LEFT][const.X]
        left_eye_y = globls.eye_data[const.LEFT][const.Y]
        right_eye_x = globls.eye_data[const.RIGHT][const.X]
        right_eye_y = globls.eye_data[const.RIGHT][const.Y]
        left_eye_in_out = 0
        right_eye_in_out = 0

        # Different set of points
        points_list = globls.centre_of_windows

        # Loop through all the target points specified to see where the eye is
        for i in range(len(points_list)):
            left_eye_in_out = 0
            right_eye_in_out = 0

            left_tp_x, left_tp_y, right_tp_x, right_tp_y = \
                util.get_disparity_offset_applied_points(points_list[i][0],
                                                                points_list[i][1],
                                                                points_list[i][2])
            diameter_in_mm, tmp = util.convert_deg_to_mm(points_list[i][3])

            # TP: x, y, Diameter
            left_eye_in = self._is_eye_in(
                left_eye_x, left_eye_y, left_tp_x, left_tp_y, diameter_in_mm/2)

            right_eye_in = self._is_eye_in(
                right_eye_x, right_eye_y, right_tp_x, right_tp_y, diameter_in_mm/2)

            if left_eye_in: left_eye_in_out =  i + 1
            if right_eye_in: right_eye_in_out = i + 1

            if left_eye_in_out and right_eye_in_out:
                break

        # If UI has any specific eye selected
        left, right = globls.eye_selected['left'], globls.eye_selected['right']

        # If only left or only right eye is selected on UI, then
        # set the other eye to be in
        if left and not right:
            right_eye_in_out = left_eye_in_out
        elif right and not left:
            left_eye_in_out = right_eye_in_out
        elif not right and not left:
            left_eye_in_out = right_eye_in_out = 0

        globls.update_eye_in_out(left_eye_in_out, right_eye_in_out)

    def vergence_error(self, target_pt_data):
        ''''
            Validate the vergence
        '''
        left_eye_x = globls.eye_data[const.LEFT][0]
        left_eye_y = globls.eye_data[const.LEFT][1]
        right_eye_x = globls.eye_data[const.RIGHT][0]
        right_eye_y = globls.eye_data[const.RIGHT][1]

        x = target_pt_data[0]
        y = target_pt_data[1]
        z = target_pt_data[2]
        vergence = target_pt_data[3]
        vergence_option = int(target_pt_data[4])

        vergence_error_in_limit = 1
        iod = globls.arbitrator_display['iod_mm']
        screendist = globls.arbitrator_display['screen_distance_mm']

        # Get the target point information for which the vergence needs to be verified
        left_tp_x, left_tp_y, right_tp_x, right_tp_y = \
            util.get_disparity_offset_applied_points(x, y, z)

        # print left_tp_x, left_tp_y, right_tp_x, right_tp_y

        # CALCULATE IDEAL GAZE ANGLES
        # By this convention, looking straight ahead is 0 degrees, looking towards
        # your nose is negative, looking away from your nose is positive. Fixation
        # on a point along the gaze direction of the cyclopean eye looking straight
        # ahead will give you the same coordinate for left & right eyes.
        # Calculate in degrees
        #
        perfect_theta_lx = math.degrees(math.atan2(-(left_tp_x + (iod / 2)), screendist))
        perfect_theta_rx = math.degrees(math.atan2((right_tp_x - (iod / 2)), screendist))
        perfect_delta_x = perfect_theta_lx + perfect_theta_rx

        # Calculate the actual values of x using eye data in degrees
        actual_theta_lx = math.degrees(math.atan2(-(left_eye_x + (iod / 2)), screendist))
        actual_theta_rx = math.degrees(math.atan2((right_eye_x - (iod / 2)), screendist))

        # Calculate the actual values of y using eye data in degrees
        actual_theta_ly = 90 - math.degrees(math.atan2(screendist, left_eye_y))
        actual_theta_ry = 90 - math.degrees(math.atan2(screendist, right_eye_y))

        # CALCULATE ERRORS
        actual_delta_x = actual_theta_lx + actual_theta_rx
        vergence_error_x = actual_delta_x - perfect_delta_x
        # print actual_delta_x, perfect_delta_x

        vergence_error_y = 0
        if vergence_option == Vergence.HORTIZONTAL_VERTICAL:
            vergence_error_y = actual_theta_ly - actual_theta_ry
            vergence_magnitude_error = math.sqrt(
                ((vergence_error_x) ** 2) + (vergence_error_y ** 2))
        else:
            vergence_magnitude_error = math.sqrt(((vergence_error_x) ** 2))

        # Method 2
        # vergence_magnitude_error = math.sqrt((left_eye[const.X]-left_tp_eye[0]) ** 2 +
        # (right_eye[const.X]-right_tp_eye[0]) ** 2)
        # vergence_error_x = vergence_magnitude_error
        # vergence_error_y = 0
        if (vergence_magnitude_error > vergence/2):
            # Send vergence not in specified limit
            vergence_error_in_limit = 0

        # Update x, y value to plot
        globls.update_vergence_error_to_plot(vergence_error_x, vergence_error_y, vergence)

        return vergence_error_in_limit

