'''
Stair case (SC) procedure
'''

import random
import itertools
import sys
import json
import numpy as np
from ui_constants import MatlabCommandsControl
from ui_configuration import matlab_config


class DifficultyLevel:
    NONE = 0
    LOW = 1
    HIGH = 2

class StimuliParam:
    SLANT = 0
    BI = 1
    MONO = 2
    START_POS = 3

class SCConstants:
    NUMBER_OF_REVERSAL = 4
    MAX_TRIALS = 30
    HIST_MAX_NUMBER_OF_REVERSE = 10
    STEPUP = 2
    STEPDOWN = 1

class ResponseDataType:
    MATLAB_STRING = 0
    RAW_STRING = 1
    IN_LIST = 2

class StairCase:
    def __init__(self):
        self.variance_lst = {} # Need variance for 0, 20, 40 seprately

        self.get_variances_for_reference_slant()

        # generate all posible combination of stimulus condition
        self.stim_conditions = list(itertools.product(matlab_config['reference_slant'],
                                                    matlab_config['binocular_cue'],
                                                    matlab_config['monocular_cue'],
                                                    matlab_config['start_position']))

        # Generate the list of indexes for the stimus
        self.stim_condition_indices = random.sample(xrange(len(self.stim_conditions)),
                                                           len(self.stim_conditions))

        # Stimulation exe history - index: {'correct':<count>, 'incorrect':<count>,
        #                                   "variance_hist":[], 'reversal_hist':[]},
        #        'cur_stimuli': {index:<>, expected_result :<>}, 'completed_stim':[] }
        self.stim_exe_history = {}
        for stim_idx in self.stim_condition_indices:
            variance_value = self.get_variance(stim_idx)
            self.stim_exe_history[stim_idx] = {
                'correct': 0, 'incorrect': 0,
                'variance_hist':[variance_value],
                'reversal_hist': [0]*SCConstants.HIST_MAX_NUMBER_OF_REVERSE
            } #  'completed': False,

        # Set to the first stimuli from the index list
        first_stim_idx = self.stim_condition_indices[0]
        first_stim_variance = self.stim_exe_history[first_stim_idx]['variance_hist'][0]
        self.stim_exe_history['cur_stimuli'] = {
            'index': first_stim_idx,
            'expected_result': self.get_expected_result(first_stim_variance,
                                                        self.stim_conditions[first_stim_idx][StimuliParam.SLANT])
        }
        self.stim_exe_history['completed_stim'] = []

    # Get the list of variance from reference slant
    def get_variances_for_reference_slant(self):
        reference_slant = matlab_config['reference_slant']
        max_slant_diff = matlab_config['max_slant'] - np.array(reference_slant)
        steps = matlab_config['stimulas_variarion']['steps']
        exponent = matlab_config['stimulas_variarion']['exponent']
        delta_slant = (max_slant_diff / float(pow(len(range(steps)), exponent))).tolist()

        for ref_diff_slant in reference_slant:
            index = np.array(reference_slant).tolist().index(ref_diff_slant)
            self.variance_lst[ref_diff_slant] = [(delta_slant[index] * pow(i, exponent)) for i in range(1, steps + 1)]

    # Clear the correct and incorrect data on moving up/down the step
    def clear_result_stats(self, cur_index):
        self.stim_exe_history[cur_index]['incorrect'] = 0
        self.stim_exe_history[cur_index]['correct'] = 0

    # Get the current stimulus
    def get_stimulus(self):
        # First select the stimuli
        stimuli_to_exe = self.stim_exe_history['cur_stimuli']['index']

        # Get the last variance in the list
        var_idx = len(self.stim_exe_history[stimuli_to_exe]['variance_hist']) - 1
        # Select the variance value if not already got
        return self.get_formated_stimulas(stimuli_to_exe,
                                          self.stim_exe_history[stimuli_to_exe]['variance_hist'][var_idx])

    # Update the variance for current stimulas  based on the user response to be used when executed next time
    def update_difficulty_level_for_next_iteration(self):
        reversed_val = None
        cur_stim_id = self.stim_exe_history['cur_stimuli']['index']

        # get variance based on difficulty level
        if (self.stim_exe_history.get(cur_stim_id) and
            self.stim_exe_history[cur_stim_id].get('correct', 0) >= SCConstants.STEPUP):
            variance = self.get_variance(cur_stim_id, DifficultyLevel.HIGH)
            self.clear_result_stats(cur_stim_id)
            reversed_val = 1  # Correct

        elif (self.stim_exe_history.get(cur_stim_id) and
              self.stim_exe_history[cur_stim_id].get('incorrect', 0) >= SCConstants.STEPDOWN):
            variance = self.get_variance(cur_stim_id, DifficultyLevel.LOW)
            self.clear_result_stats(cur_stim_id)
            reversed_val = -1  # Incorrect

        else:
            variance = self.get_variance(cur_stim_id, DifficultyLevel.NONE)

        status = self.update_reversal_params(cur_stim_id, reversed_val)

        # update the next difficulty level
        self.stim_exe_history[cur_stim_id]['variance_hist'].append(variance)
        return status

    # GEt the next stimuli
    def prepare_next_stimuli(self):
        # Prepare next stimuli using current stimuli index
        stim_to_exe = self.get_next_stimuli_index(self.stim_exe_history['cur_stimuli']['index'])
        var_idx = len(self.stim_exe_history[stim_to_exe]['variance_hist']) - 1
        variance = self.stim_exe_history[stim_to_exe]['variance_hist'][var_idx]

        # Update cur index and expected response
        self.stim_exe_history['cur_stimuli']['index'] = stim_to_exe
        self.stim_exe_history['cur_stimuli']['expected_result'] = \
            self.get_expected_result(variance, self.stim_conditions[stim_to_exe][StimuliParam.SLANT])

    # Get the next stimuli for execution
    def get_next_stimuli_index(self, cur_stimuli_id):
        # get the index of last stimuli index value
        stim_indices_idx = self.stim_condition_indices.index(cur_stimuli_id)

        while True:
            stim_indices_idx += 1  # get next stimuli

            # See if the end of the list is reached if yes rolover
            if stim_indices_idx > (len(self.stim_condition_indices) -1):
                stim_indices_idx = 0
                # Shuffle the list
                random.shuffle(self.stim_condition_indices)

            # If the task is completed ignore the completed task and fetch next one
            if self.stim_condition_indices[stim_indices_idx] not in self.stim_exe_history['completed_stim']:
                break

        return self.stim_condition_indices[stim_indices_idx]

    # For the given variance get the expected result
    def get_expected_result(self, variance, ref_slant):

        if ref_slant > (ref_slant + variance):
            return int(MatlabCommandsControl.COMMAND_WORD_BUTTON2_CLICKED)
        elif ref_slant < (ref_slant + variance) > 0:
            return int(MatlabCommandsControl.COMMAND_WORD_BUTTON4_CLICKED)

    # Update the reversal params - how many times it changed, is the task complete
    def update_reversal_params(self, cur_index, reversed_val=None):
        no_of_reversed_count = 0
        if reversed_val is not None:
            last_idx_val = self.stim_exe_history[cur_index]['reversal_hist'][SCConstants.HIST_MAX_NUMBER_OF_REVERSE-1]
            if last_idx_val == 0 and reversed_val == -1:
                pass
            else:

                self.stim_exe_history[cur_index]['reversal_hist'].append(reversed_val)
                del self.stim_exe_history[cur_index]['reversal_hist'][0]

                # Monitor the last 10 trials reversal parameter
                prev_rev_val = self.stim_exe_history[cur_index]['reversal_hist'][0]
                for i in self.stim_exe_history[cur_index]['reversal_hist']:
                    if i == 0: continue

                    if prev_rev_val !=0 and i != prev_rev_val:
                        no_of_reversed_count += 1
                    prev_rev_val = i

        # Add the stimuls which has completed its task into this list and see if it needs to be removed from the current population
        if no_of_reversed_count >= SCConstants.NUMBER_OF_REVERSAL:
            self.stim_exe_history['completed_stim'].append(cur_index)
        elif len(self.stim_exe_history[cur_index]['variance_hist']) >= SCConstants.MAX_TRIALS:
            self.stim_exe_history['completed_stim'].append(cur_index)

        # Check if all the task has been completed
        if len(self.stim_exe_history['completed_stim']) == len(self.stim_condition_indices):
            # Stop the experiment here
            return False

        return True

    # Update the results based on reponse
    def compare_update_result(self, result_value):
        cur_index = self.stim_exe_history['cur_stimuli']['index']

        # Repeat the experiment if no button was clicked
        if self.stim_exe_history['cur_stimuli']['expected_result'] \
                == MatlabCommandsControl.COMMAND_WORD_NO_BUTTON_CLICKED:
            return

        if self.stim_exe_history['cur_stimuli']['expected_result'] == result_value:
            self.stim_exe_history[cur_index]['correct'] += 1
            self.stim_exe_history[cur_index]['incorrect'] = 0

        else:
            self.stim_exe_history[cur_index]['incorrect'] += 1
            self.stim_exe_history[cur_index]['correct'] = 0

        status = self.update_difficulty_level_for_next_iteration()

        # If all task are executed then the status returned is False
        if not status:
            print("All simuli executed")

            # *** Change this accordingly after talking to Hoon ***
            return False

        self.prepare_next_stimuli()
        return True

    # get the variance for a given stimuli
    def get_variance(self, stimuli_index, difficulty_level=0):
        ref_slant = self.stim_conditions[stimuli_index][0]

        max_len = len(self.variance_lst[ref_slant]) - 1
        variance_index = max_len
        variance_value = self.variance_lst[ref_slant][max_len]

        # get existing variance value
        if self.stim_exe_history.get(stimuli_index):
            cur_var_idx = len(self.stim_exe_history[stimuli_index]['variance_hist']) - 1
            if self.stim_exe_history.get(stimuli_index).get('variance_hist')[cur_var_idx]:
                variance_value  = self.stim_exe_history[stimuli_index].get('variance_hist')[cur_var_idx]

                if variance_value < 0:
                    variance_value *= -1

        variance_index = self.variance_lst[ref_slant].index(variance_value)

        # Select variance based on difficulty level
        if difficulty_level == DifficultyLevel.HIGH: # 1 Increase difficulty level
            if variance_index != 0:  #  If @ 0th index remain there
                variance_index = variance_index -1

        elif difficulty_level == DifficultyLevel.LOW:  # 2 Means decrease difficulty level
            if variance_index != (max_len):  # If @ N-1th index remain there
                variance_index = variance_index + 1

        # Return the variance
        return (self.variance_lst[ref_slant][variance_index] * self.stim_conditions[stimuli_index][StimuliParam.START_POS])

    # This is formating routine
    def get_formated_stimulas(self, stimuli_index, variance,
                                 response_data_type=ResponseDataType.MATLAB_STRING):

        stim_string_raw = ''
        stim1_string = '%s %s/' % (MatlabCommandsControl.COMMAND_STATE_STIMULI_1_SLANT,
                                   self.stim_conditions[stimuli_index][StimuliParam.SLANT]
                                   )
        stim_string_raw += '%s ' % self.stim_conditions[stimuli_index][StimuliParam.SLANT]

        stim1_string += '%s %s/' % (MatlabCommandsControl.COMMAND_STATE_STIMULI_1_BI,
                                    self.stim_conditions[stimuli_index][StimuliParam.BI]
                                    )
        stim_string_raw += '%s ' % self.stim_conditions[stimuli_index][StimuliParam.BI]

        stim1_string += '%s %s/' % (MatlabCommandsControl.COMMAND_STATE_STIMULI_1_MONO,
                                    int("".join(str(i) for i in self.stim_conditions[stimuli_index][StimuliParam.MONO]),
                                        2)
                                    )
        stim_string_raw += '%s ' % self.stim_conditions[stimuli_index][StimuliParam.MONO]

        stim2_variance = float(self.stim_conditions[stimuli_index][StimuliParam.SLANT] + variance)
        stim2_string = '%s %s/' % (MatlabCommandsControl.COMMAND_STATE_STIMULI_2_SLANT,
                                   (stim2_variance)
                                   )

        stim_string_raw += '%s ' % (stim2_variance)

        stim2_string += '%s %s/' % (MatlabCommandsControl.COMMAND_STATE_STIMULI_2_BI,
                                    self.stim_conditions[stimuli_index][StimuliParam.BI]
                                    )
        stim_string_raw += '%s ' % self.stim_conditions[stimuli_index][StimuliParam.BI]

        stim2_string += '%s %s/' % (MatlabCommandsControl.COMMAND_STATE_STIMULI_2_MONO,
                                    int("".join(str(i) for i in self.stim_conditions[stimuli_index][StimuliParam.MONO]),
                                        2)
                                    )
        stim_string_raw += '%s' % str(self.stim_conditions[stimuli_index][StimuliParam.MONO])

        if response_data_type == ResponseDataType.MATLAB_STRING:
            return (stim1_string + stim2_string), stim_string_raw
        elif response_data_type == ResponseDataType.RAW_STRING:
            return stim_string_raw
        else:
            return stim_string_raw.split()


sc = StairCase()


def main():
    #start stair case0
    i = 0
    while True:


        cur_index = sc.stim_exe_history['cur_stimuli']['index']

        stim, stim_raw = sc.get_stimulus()
        stim_data = stim_raw.split()

        resp = raw_input('If "{}" is greater than "{}" for stim {}? Yes- 1 No- 0 '.format(stim_data[0],
                                                                                      stim_data[5],
                                                                                      cur_index))
        if len(resp) < 1:
            resp = raw_input('If {} is greater than {}? Yes- 1 No- 0 '.format(stim_data[0], stim_data[5]))
            if len(resp) < 1:
                break
        resp = 134 if int(resp) == 0 else 132
        res = sc.compare_update_result(int(resp))
        # i += 1

        # testing
        for k, v in sc.stim_exe_history.iteritems():
            if k != 'next_stimuli_exe' and k != 'cur_stimuli' and k != 'completed_stim':

                print(k, " : ", v['variance_hist'])
                print(' ', " : ", v['reversal_hist'])
        print("   completed Stim : ", sc.stim_exe_history['completed_stim'])

        if not res:
            sys.exit(1)


if __name__ == '__main__':
    main()

