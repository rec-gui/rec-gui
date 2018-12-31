'''
GUI
'''
import os
import time
import copy
import collections
import Tkinter as tk
import tkMessageBox
import numpy as np
import utility as util
from constants import (Constant as const, TrialsStats, ConfigLabels,
                       MessageType, Vergence, Task, Calibration, FieldMapping,
                       CalibrationListIndex, MouseClick, EyeRecordingMethods)
from data_collection import DataFileObj
from file import File
from global_parameters import Globals as globls
from logger import logging
from select_eye_recording import EyeRecord
from calibration import CalibrationObj as calib
from widget_api import WidgetApi
from button_funs import button_module
log = logging.getLogger(__name__)

class Gui:
    def __init__(self):
        """
            Initlization of GUI valriables to access widgets, frames
        """
        # Draw GUI window based on the screen width and height
        width = globls.gui_root.winfo_screenwidth()
        height = globls.gui_root.winfo_screenheight()

        #width = 1920
        #height = 1080
        globls.gui_root.geometry("%dx%d+0+0" % (width, height))
        globls.gui_root.title("Real-time experimental control GUI")
        globls.gui_root.configure(background="#d9d9d9")
        globls.gui_root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Initlization of objects for various classes which is going to be used by GUI
        self.file = File()
        self.t1 = None

        # Initlize the global parameters for GUI
        # eye, version window, vergence window parameters
        self.eye_pos_text = tk.StringVar()
        self.stim_pos_text = tk.StringVar()
        self.stim_pos_text.set("X (deg): 0\nY (deg): 0")
        self.zoom_by = 1
        # Last eye data is stored to move the eye widget based on current and previous values
        self.last_eye_data = [[0, 0], [0, 0]]
        # a + shape widgget
        self.eye_widget = [[None, None], [None, None]]     # Left (x, y), Right (x, y)
        self.draw_object = [[None, None], [None, None], [None, None], [None, None], [None, None]]

        # Last eye vergence data to move the vergence error widget between current and previous values
        self.last_eye_vergence_data = [0, 0, 0]    # (x, y)
        # a cross shaped widget
        self.vergence_eye_widget = [None, None]     # (x, y)
        self.vergence_window = None
        # self.vergence_window_size_changed = False
        # Window widgets have Left and right widget obj for point and window
        # [window left, window right, pt left, pt right]
        self.centre_pt_window_widget = []
        self.last_drawn_centre_point = []

        # # Trial frame parameters
        # self.trail_status = []
        # for i in range(TrialsStats.TRIAL_LABEL_10 + 1):
        #     self.trail_status.append(tk.IntVar())

        # offset, gain, parameters
        self.eye_check_button = [tk.IntVar(), tk.IntVar()]  # [left, Right]
        self.v_left_offset = tk.StringVar()
        self.v_left_gain = tk.StringVar()
        self.h_left_offset = tk.StringVar()
        self.h_left_gain = tk.StringVar()
        self.v_right_offset = tk.StringVar()
        self.v_right_gain = tk.StringVar()
        self.h_right_offset = tk.StringVar()
        self.h_right_gain = tk.StringVar()
        self.pupil_size = [tk.StringVar(), tk.StringVar()]  # [Left, Right]
        self.left_sb = []
        self.right_sb = []
        # self.version_entry = self.vergence_entry = None

        # Draw calibration controls parameters
        self.calibration_type = tk.IntVar()
        # In case of error want to revert back to previous state
        self.calibration_type_prev = 0
        self.clear_button = None
        self.accept_button = None
        self.calibrate_button = None
        self.cancel_lastdata_button = None
        self.auto_checkbutton = None
        self.manual_checkbutton = None
        # Manual calibration widgets
        self.manual_calib_cur_idx = tk.IntVar()
        self.manual_radiobutton = []
        self.manual_calibration_points = []
        self.accepted_eyepos_ploted_widget = []
        self.manual_points_color_marker = []

        # Auto calib widgets
        self.auto_calibration_points = np.array([])
        self.auto_calib_cur_index = 0
        self.auto_calib_entries = []

        # receptive field mapping variables
        self.receptive_field_map_checkbutton = tk.IntVar()
        self.receptive_field_map_type = tk.IntVar()
        self.dots = tk.IntVar()
        self.receptive_field_entries = []
        self.receptive_field_dots_checkbutton = None
        self.receptive_field_grating_checkbutton = None

        # Variable to hold task details like calibration, receptive field mapping
        self.last_selected_task = 0
        self.task_checkbutton = tk.IntVar()
        self.task_checkbutton.set(0)
        self.task_in_progress = False
        self.task_file_loaded = False
        self.subject_file_loaded = False

        '''  Draw the widgets '''
        # Scrolled text box
        # Textbox for logging
        self.text_data = 0
        self.text = self.draw_scrolled_text()
        # XXX: If using Anaconda or Python 3.0, calls to GUI from another thread ends up in a loop
        # to over come this use message queue or list to read and display the logs into UI
        # Or read the parameters in the periodic call
        globls.dump_log = self.log_to_textbox
        # Draw canvas
        self.last_mouse_target_point = [0, 0]
        self.mouse_click_target_points = None
        self.canvas_mouse_checkbutton = tk.IntVar()
        self.last_sel_canvas_mouse_checkbutton = 0
        '''
        self.depth_entry = None
        '''
        self.eye_canvas_obj = self.draw_canvas_for_eye_movements(width, height)
        self.eye_canvas_pix_w = self.eye_canvas_obj.winfo_width()
        self.eye_canvas_pix_h = self.eye_canvas_obj.winfo_height()
        #print(self.eye_canvas_pix_w,self.eye_canvas_pix_h)
	# prepare drawing objects
        # Draw line '-' Store this as X/Horizontal
        zeroX = 0
        zeroY = 0
        self.lineLength = 8
        self.draw_object[0][const.X] = self.eye_canvas_obj.create_line(zeroX - self.lineLength / 2, zeroY,
                                                                      zeroX + self.lineLength / 2, zeroY, fill='black')
        self.draw_object[0][const.Y] = self.eye_canvas_obj.create_line(zeroX, zeroY - self.lineLength / 2, zeroX,
                                                                      zeroY + self.lineLength / 2, fill='black')
        self.draw_object[1][const.X] = self.eye_canvas_obj.create_line(zeroX - self.lineLength / 2, zeroY,
                                                                      zeroX + self.lineLength / 2, zeroY, fill='black')
        self.draw_object[1][const.Y] = self.eye_canvas_obj.create_line(zeroX, zeroY - self.lineLength / 2, zeroX,
                                                                      zeroY + self.lineLength / 2, fill='black')
        self.draw_object[2][const.X] = self.eye_canvas_obj.create_line(zeroX - self.lineLength / 2, zeroY,
                                                                      zeroX + self.lineLength / 2, zeroY, fill='black')
        self.draw_object[2][const.Y] = self.eye_canvas_obj.create_line(zeroX, zeroY - self.lineLength / 2, zeroX,
                                                                      zeroY + self.lineLength / 2, fill='black')
        self.draw_object[3][const.X] = self.eye_canvas_obj.create_line(zeroX - self.lineLength / 2, zeroY,
                                                                      zeroX + self.lineLength / 2, zeroY, fill='black')
        self.draw_object[3][const.Y] = self.eye_canvas_obj.create_line(zeroX, zeroY - self.lineLength / 2, zeroX,
                                                                      zeroY + self.lineLength / 2, fill='black')
        self.draw_object[4][const.X] = self.eye_canvas_obj.create_line(zeroX - self.lineLength / 2, zeroY,
                                                                      zeroX + self.lineLength / 2, zeroY, fill='black')
        self.draw_object[4][const.Y] = self.eye_canvas_obj.create_line(zeroX, zeroY - self.lineLength / 2, zeroX,
                                                                      zeroY + self.lineLength / 2, fill='black')


        # Control buttons
        self.startbutton = None
        self.pausebutton = None
        self.stopbutton = None
        self.exitbutton = None
        self.draw_control_buttons()

        # raw subject configuration
        self.subject_config_entry = None
        self.draw_loadsave_subject()


        # Draw frame for configuration window and draw labels and entry for accepting configuration
        # Holds config that are to be drawn or read fron the GUI widget
        self.editable_configuration_entries = []
        self.draw_editable_configuration_window()

        # Draw frame for configuration window and draw labels and entry for displaying configuration
        # This is used to build the widget information and when data is entered
        # a dictionary having command word value and data is built and stored in self.displayable_configuration_dict
        # self.displayable_configuration_dict will be used to map the values coming in from 3rd party server
        self.displayable_widget_config = {}
        self.displayable_configuration_dict = {}
        self.draw_displayable_configuration_widgets()

        '''
            Eye recording method selection processing
        '''
        # Open new window and add the selection of eye link or eye tracker
        # And as well channel selector (radio button)
        # Once the radio button is selected show the option on Eye control Configuration options window
        # So that the user can see it.

        globls.eye_recording_method_obj = EyeRecord()
        globls.eye_recording_method_obj.dialog1.focus_force()
        globls.gui_root.wait_window(globls.eye_recording_method_obj.dialog1)
        # Wait here for user to make selection of which eye window to be selected
        globls.eye_recording_method_obj.eye_recording_win.attributes("-topmost",True)
        globls.gui_root.wait_window(globls.eye_recording_method_obj.eye_recording_win)

        if globls.eye_recording_method == EyeRecordingMethods.EYE_NONE:
            globls.custom_button = []
            globls.custom_button_callbacks = button_module()
            tracking_config_dict = GuiWidget['tracker_window_config']['tracker_window_label']
            self.draw_tracker_window_config()
            self.draw_callback_buttons()
        else:
            self.draw_subject_viewing_params()
            # Draw eye offset, gain, configuration
            self.draw_eye_and_window_config()
            # Draw eye calibration widgets
            self.draw_eye_calibration_task_button()
            # Do this in the end as it initilizes some of the widgets as well
            self.init_calibration_configuration_parameter(init=True)
            # receptve field mapping
            self.draw_receptive_field_mapping_window()
            tracking_config_dict = GuiWidget['eye_window_config']['eye_window_label']

        # Draw the label with the updated eye selection method value
        tracking_config_dict['text'] = tracking_config_dict['text']
        tracking_config_dict['relwidth'] = 0.09

        # Redraw the selected option on the eye configuration label header
        WidgetApi.draw_label(globls.gui_root, tracking_config_dict)

        # TO DO. if the eye recording needs to be edited or view the channel details.
        # if eye_mov_cap_method == EyeRecordingMethods.EYE_COIL:
        #     obj.bind("<Button-1>", self.eye_recording_method_obj.display_channel_for_eye_pos)

        # Periodic call to display window, vergence
        self.gui_periodic_call()
        self.display_warning_error_message("Warning, No Subject or Task File Loaded ",
                               "Please load subject and task file to proceed.")

        globls.gui_height = globls.gui_root.winfo_height()
        globls.gui_width = globls.gui_root.winfo_width()
        # print(globls.gui_width,globls.gui_height)
        globls.update_gui_display_param(globls.gui_width, globls.gui_height,
                                        GuiWidget['eye_display']['main_frame']['relwidth'], GuiWidget['eye_display']['main_frame']['relheight'],
                                        GuiWidget['eye_display']['canvas']['relwidth'], GuiWidget['eye_display']['canvas']['relheight'])
        globls.update_gui_scale_factor()

    ''' Task rediness is checked before executing the task '''
    def check_task_readiness(self, task=None, load_file=None):
        if (task and self.task_in_progress):
            self.display_warning_error_message("Error, Stop Current Experiment ",
                                   "Please stop the current experiment before proceeding.")
            return False

        if load_file and (not self.task_file_loaded or not self.subject_file_loaded):
            self.display_warning_error_message("Warning, Subject or Task File Not Loaded ",
                                   "Please load subject and task file to proceed.")
            return False
        return True

    ''' On 3rd party server connecting to the GUI it displays message '''
    def display_warning_error_message(self,window_title,window_text):

        # Generate an error window with an okay button
        self.dialog1 = tk.Toplevel(globls.gui_root)
        #self.dialog1.geometry("200x200")
        self.dialog1.geometry("{}x{}+750+450".format(
            400,
            100
        ))
        self.dialog1.wm_title(window_title)
        self.warning_title = tk.Label(self.dialog1,text=window_text,font="bold")
        self.warning_title.pack(pady=5)
        self.buttonOK = tk.Button(self.dialog1,text="OK",command=self.dialog1.destroy,padx = 30)
        self.buttonOK.pack(pady=10)
        self.dialog1.attributes("-topmost",True)
        self.buttonOK.focus_set()
        self.buttonOK.bind('<Return>', lambda event, key='<space>': self.buttonOK.event_generate(key))
        self.dialog1.protocol("WM_DELETE_WINDOW", self.dialog1.destroy)

        return


    ''' Update if the both subject and task file are read '''
    def update_task_subject_file_loaded(self, subject_file=None, task_file=None):
        if subject_file is not None:
            self.subject_file_loaded = subject_file

        if task_file is not None:
            self.task_file_loaded = task_file

        # If both files loaded then set the flag and enable control button
        if self.task_file_loaded and self.subject_file_loaded:
            globls.load_subject_task_config_flag = False
            if not self.task_in_progress:
                self.startbutton.configure(state=tk.NORMAL)
                self.pausebutton.configure(state=tk.NORMAL)
                self.stopbutton.configure(state=tk.NORMAL)

        if not self.task_file_loaded or not self.subject_file_loaded:
            self.startbutton.configure(state=tk.DISABLED)
            self.pausebutton.configure(state=tk.DISABLED)
            self.stopbutton.configure(state=tk.DISABLED)

    ''' Process the experiment based on selection '''
    def process_task(self):
        # based on Task enable or disable the entrire widget

        # Do not allow switchig task without Stopping the experiment if already started
        task = self.task_checkbutton.get()

        if not self.check_task_readiness(True, True):
            self.task_checkbutton.set(self.last_selected_task)
            return

        if task:
            if task == Task.CALIBRATION:
                self.update_calibration_widgets()
            elif task == Task.RECEPTIVE_FIELD_MAPPING:
                self.update_receptive_field_mapping_widget()
        else:
            self.update_calibration_widgets(tk.DISABLED, tk.DISABLED)
            self.update_receptive_field_mapping_widget(tk.DISABLED)
        self.last_selected_task = self.task_checkbutton.get()

    ''' Periodic call to draw eye, version, vergence, '''
    def gui_periodic_call(self):
        try:
            # Display any config from Arbitrator server
            self.update_displayable_configuration()

            # Read the latest configuation
            self.read_eye_window_configuration()

            if globls.eye_recording_method == EyeRecordingMethods.EYE_NONE:
                # Draw tracking objects
                self.display_drawing_object()
            else:
                # Draw eye Data
	            self.display_eye()
	

            # Draw window
            self.display_windows()

            # Draw vergence
            self.display_vergence()

            if globls.load_subject_task_config_flag:
                if not self.task_file_loaded or not self.subject_file_loaded:
                    self.display_warning_error_message("Third Party Server Connection Established",
                                                       "Load subject and task file to proceed.")
                elif self.task_in_progress:
                    self.display_warning_error_message("Error, Third Party Server Connection Already Established",
                                       "Please stop the current experiment to proceed.")
                else:
                    self.display_warning_error_message("Third Party Server Connection Established",
                                      "Click on start to proceed.")
                    # Send the configuration that is required by 3rd party server
                    self.submit_configuration_data()
                    util.send_screen_parameters()

                globls.update_load_subject_task_config_flag(False)
                self.update_task_subject_file_loaded()


        except Exception as e:
            log.exception(e)

        if not globls.is_program_running:
            return
        globls.gui_root.after(const.GUI_PERIODIC_CALL, self.gui_periodic_call)

    ''' Read the parameters from GUI like  offset gain '''
    def read_eye_window_configuration(self):
        try:
            # Depth
            ''' Removed option 4/5/18 -LT
            if len(self.depth_entry.get()) and float(self.depth_entry.get()) != globls.depth:
                globls.update_depth(float(self.depth_entry.get()))
                data = "{} {}/".format(const.TARGET_Z, globls.depth)
                util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data, "depth ")
            '''
            # Read offset gain
            if len(self.pupil_size[const.LEFT].get()):
                globls.pupil_size['left'] = int(self.pupil_size[const.LEFT].get())
            if len(self.pupil_size[const.RIGHT].get()):
                globls.pupil_size['right'] = int(self.pupil_size[const.RIGHT].get())
            if len(self.h_left_offset.get()):
                globls.offset_gain_config['left_offset_x'] = float(self.h_left_offset.get())
            if len(self.h_left_gain.get()):
                globls.offset_gain_config['left_gain_x'] = float(self.h_left_gain.get())
            if len(self.v_left_offset.get()):
                globls.offset_gain_config['left_offset_y'] = float(self.v_left_offset.get())
            if len(self.v_left_gain.get()):
                globls.offset_gain_config['left_gain_y'] = float(self.v_left_gain.get())
            if len(self.h_right_offset.get()):
                globls.offset_gain_config['right_offset_x'] = float(self.h_right_offset.get())
            if len(self.h_right_gain.get()):
                globls.offset_gain_config['right_gain_x'] = float(self.h_right_gain.get())
            if len(self.v_right_offset.get()):
                globls.offset_gain_config['right_offset_y'] = float(self.v_right_offset.get())
            if len(self.v_right_gain.get()):
                globls.offset_gain_config['right_gain_y'] = float(self.v_right_gain.get())

        except Exception as e:
            log.exception(e)

    ''' Draw and display eye information from eye link '''
    @staticmethod
    def get_line_pos(x, y, cross_line=False):
        # :param x: x position
        # :param y: y position
        # :param cross_line: if it is + or X
        # :return: the positionX for line | or /, positionY  for line | or /
        diff = 8
        # return X pos list and y pos list
        if cross_line:
            return [x - diff, x + diff, x + diff, x - diff], [y - diff, y + diff, y - diff, y + diff]
        else:
            return [x - diff, x + diff, x, x], [y, y, y - diff, y + diff]

    def display_drawing_object(self):
        for i in range(globls.drawing_object_number):
            tempx = globls.drawing_object_pos[i][0]
            tempy = globls.drawing_object_pos[i][1]

            # tempR = str(hex(globls.drawing_obejct_color[i][0]))
            # tempG = str(hex(globls.drawing_obejct_color[i][1]))
            # tempB = str(hex(globls.drawing_obejct_color[i][2]))
            # tempColor = '#' + tempR.replace('0x','') + tempG.replace('0x','') + tempB.replace('0x','')

            # self.eye_canvas_object.itemconfig(self.draw_obejct[i][const.X], fill = tempColor)
            self.eye_canvas_obj.coords(self.draw_object[i][const.X], tempx - self.lineLength / 2, tempy, tempx + self.lineLength / 2, tempy)
            # self.eye_canvas_object.itemconfig(self.draw_obejct[i][const.Y], fill = tempColor)
            self.eye_canvas_obj.coords(self.draw_object[i][const.Y], tempx, tempy - self.lineLength / 2, tempx, tempy + self.lineLength / 2)	

    def display_eye(self):
        '''
            Display eye marker on GUI
        '''
        try:
            if len(globls.eye_data[0]):
                eye_pos_non_scaled = copy.copy(globls.eye_data)

                # Convert the eye data to pixel and co-ordinate system where (0, 0)
                # starts at top left
                left_x, left_y = util.convert_mm_to_pix(eye_pos_non_scaled[const.LEFT][0],
                                                        eye_pos_non_scaled[const.LEFT][1])
                left_x, left_y = util.shift_to_top_left(left_x, left_y)

                right_x, right_y = util.convert_mm_to_pix(eye_pos_non_scaled[const.RIGHT][0],
                                                          eye_pos_non_scaled[const.RIGHT][1])
                right_x, right_y = util.shift_to_top_left(right_x, right_y)

                deg_l_x, deg_l_y = util.convert_mm_to_deg(eye_pos_non_scaled[const.LEFT][0], eye_pos_non_scaled[const.LEFT][1],)
                deg_r_x, deg_r_y = util.convert_mm_to_deg(eye_pos_non_scaled[const.RIGHT][0], eye_pos_non_scaled[const.RIGHT][1],)

                #self.eye_pos_text.set('L: ({}, {}) R: ({}, {})'.format(
                #    int(left_x), int(left_y), int(right_x), int(right_y)))

                self.eye_pos_text.set('L: ({}, {}) R: ({}, {})'.format(
                    float(round(deg_l_x,3)), float(round(deg_l_y,3)), float(round(deg_r_x,3)), float(round(deg_r_y,3))))

                if left_x < 0: left_x = 0
                elif left_x > globls.arbitrator_window_width:
                    left_x = globls.arbitrator_window_width

                if left_y < 0: left_y = 0
                elif left_y > globls.arbitrator_window_height:
                    left_y = globls.arbitrator_window_height

                if right_x < 0: right_x = 0
                elif right_x > globls.arbitrator_window_width:
                    right_x = globls.arbitrator_window_width

                if right_y < 0: right_y = 0
                elif right_y > globls.arbitrator_window_height:
                    right_y = globls.arbitrator_window_height

                # resize it fit into GUI canvas
                left_x_resized = left_x / globls.arbitrator_display['x_scale_factor']
                left_y_resized = left_y / globls.arbitrator_display['y_scale_factor']
                right_x_resized = right_x / globls.arbitrator_display['x_scale_factor']
                right_y_resized = right_y / globls.arbitrator_display['y_scale_factor']

                diff_xy_pos_left = np.subtract([left_x_resized, left_y_resized],
                                               self.last_eye_data[const.LEFT]).tolist()
                diff_xy_pos_right = np.subtract([right_x_resized, right_y_resized],
                                                self.last_eye_data[const.RIGHT]).tolist()

                if globls.eye_selected['left']:
                    if self.zoom_by:
                        self.eye_canvas_obj.delete(self.eye_widget[const.LEFT][const.X])
                        self.eye_canvas_obj.delete(self.eye_widget[const.LEFT][const.Y])
                        self.eye_widget[const.LEFT][const.X] = None
                        self.eye_widget[const.LEFT][const.Y] = None

                    if (self.eye_widget[const.LEFT][const.X] is None or
                        self.eye_widget[const.LEFT][const.Y] is None):
                        # get line co-ordinates which would look like '+'
                        posx, posy = self.get_line_pos(left_x_resized * self.zoom_by - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                       left_y_resized * self.zoom_by - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1))
                        #posx, posy = self.get_line_pos(left_x_resized * self.zoom_by + (globls.eye_canvas_width - globls.eye_canvas_width*self.zoom_by)/2,
                        #                               left_y_resized * self.zoom_by + (globls.eye_canvas_height - globls.eye_canvas_height*self.zoom_by)/2)

                        # Draw line '-' Store this as X/Horizontal
                        self.eye_widget[const.LEFT][const.X] = self.eye_canvas_obj.create_line(
                            posx[0], posy[0], posx[1], posy[1], fill='green')
                        # draw line '|'. Store this as Y/Vertical
                        self.eye_widget[const.LEFT][const.Y] = self.eye_canvas_obj.create_line(
                            posx[2], posy[2], posx[3], posy[3], fill='green')
                    else:

                        self.eye_canvas_obj.move(self.eye_widget[const.LEFT][const.X],
                                                diff_xy_pos_left[0]* self.zoom_by - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                diff_xy_pos_left[1]* self.zoom_by - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1))
                        self.eye_canvas_obj.move(self.eye_widget[const.LEFT][const.Y],
                                                diff_xy_pos_left[0]* self.zoom_by - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                diff_xy_pos_left[1]* self.zoom_by - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1))
                else:
                    self.eye_canvas_obj.delete(self.eye_widget[const.LEFT][const.X])
                    self.eye_canvas_obj.delete(self.eye_widget[const.LEFT][const.Y])
                    self.eye_widget[const.LEFT][const.X] = None
                    self.eye_widget[const.LEFT][const.Y] = None

                if globls.eye_selected['right']:
                    # this is required to be done as move will move the eye window out of
                    # the canvas
                    if self.zoom_by:
                        self.eye_canvas_obj.delete(self.eye_widget[const.RIGHT][const.X])
                        self.eye_canvas_obj.delete(self.eye_widget[const.RIGHT][const.Y])
                        self.eye_widget[const.RIGHT][const.X] = None
                        self.eye_widget[const.RIGHT][const.Y] = None

                    if (self.eye_widget[const.RIGHT][const.X] is None or
                        self.eye_widget[const.RIGHT][const.Y] is None):
                        posx, posy = self.get_line_pos(right_x_resized * self.zoom_by - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                       right_y_resized * self.zoom_by - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1))

                        # Draw line '-' Store this as X/Horizontal
                        self.eye_widget[const.RIGHT][const.X] = self.eye_canvas_obj.create_line(
                            posx[0], posy[0], posx[1], posy[1], fill='blue')
                        # draw line '|'. Store this as Y/Vertical
                        self.eye_widget[const.RIGHT][const.Y] = self.eye_canvas_obj.create_line(
                            posx[2], posy[2], posx[3], posy[3], fill='blue')
                    else:
                        self.eye_canvas_obj.move(self.eye_widget[const.RIGHT][const.X],
                                                diff_xy_pos_right[0]* self.zoom_by - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                diff_xy_pos_right[1]* self.zoom_by - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1))
                        self.eye_canvas_obj.move(self.eye_widget[const.RIGHT][const.Y],
                                                diff_xy_pos_right[0]* self.zoom_by - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                diff_xy_pos_right[1]* self.zoom_by - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1))
                else:
                    self.eye_canvas_obj.delete(self.eye_widget[const.RIGHT][const.X])
                    self.eye_canvas_obj.delete(self.eye_widget[const.RIGHT][const.Y])
                    self.eye_widget[const.RIGHT][const.X] = None
                    self.eye_widget[const.RIGHT][const.Y] = None

                self.last_eye_data = [[left_x_resized, left_y_resized],
                                      [right_x_resized, right_y_resized]]
        except Exception as e:
            log.exception(e)

    ''' Display windows like version, target '''
    def display_windows(self):
        '''
            updated: This flag will be set to True if on demand window is required to be draw
        '''
        try:

            centre_pt = copy.copy(globls.centre_of_windows)
            # Draw this only if window is asked to be displayed
            if globls.centre_window_on:

                diff = {tuple(i) for i in self.last_drawn_centre_point} ^ {tuple(i) for i in centre_pt}
                # if there is change in window from previos one then draw the window else do not
                if len(diff):
                    # Delete it
                    for pt_win in self.centre_pt_window_widget:
                        # Left point window widget
                        if pt_win[0]: self.eye_canvas_obj.delete(pt_win[0])
                        if pt_win[1]: self.eye_canvas_obj.delete(pt_win[1])

                        # Right point widget
                        if pt_win[2]: self.eye_canvas_obj.delete(pt_win[2])
                        if pt_win[3]: self.eye_canvas_obj.delete(pt_win[3])
                    self.centre_pt_window_widget = []

                    # based on the target points available
                    for tp in centre_pt:
                        left_pt = left_win = right_pt = right_win = None
                        # Get offset and disparity applied points

                        lx, ly, rx, ry = util.get_disparity_offset_applied_points(tp[0], tp[1], tp[2])
                        # print "lx, ly, rx, ry ", lx, ly, rx, ry
                        # print "iod, sd", globls.arbitrator_display['iod_mm'], globls.arbitrator_display['screen_distance_mm']

                        x, y = util.convert_mm_to_pix(lx, ly)
                        left_x, left_y = util.shift_to_top_left(x, y)

                        rx, ry = util.convert_mm_to_pix(rx, ry)
                        right_x, right_y = util.shift_to_top_left(rx, ry)

                        # convert the 3rd parameter diameter from degreee to pix
                        diameter, tmp = util.convert_deg_to_pix(tp[3])
                        lcolor = 'green'
                        if len(tp) > 4:
                            lcolor = tp[4]
                        rcolor = 'blue'
                        if len(tp) > 5:
                            rcolor = tp[5]

                        if globls.eye_selected['left']:
                            left_pt = self.draw_point(left_x, left_y, color=lcolor)
                            left_win = self.draw_window(left_x, left_y, color=lcolor, win_size=diameter/2)

                        if globls.eye_selected['right']:
                            right_pt = self.draw_point(right_x, right_y, color=rcolor)
                            right_win = self.draw_window(right_x, right_y, color=rcolor, win_size=diameter/2)

                        self.centre_pt_window_widget.append([left_win, right_win, left_pt, right_pt])
            else:
                # Delete it
                for pt_win in self.centre_pt_window_widget:
                    # Left window widget

                    # Right left window widget
                    if pt_win[0]: self.eye_canvas_obj.delete(pt_win[0])
                    if pt_win[1]: self.eye_canvas_obj.delete(pt_win[1])

                    # Right left point widget
                    if pt_win[2]: self.eye_canvas_obj.delete(pt_win[2])
                    if pt_win[3]: self.eye_canvas_obj.delete(pt_win[3])
                centre_pt = []
                self.centre_pt_window_widget = []
            self.last_drawn_centre_point = centre_pt
        except Exception as e:
            log.exception(e)

    def display_vergence(self):
        '''
        Display the vergence on the GUI
        '''
        try:
            vergence_error = copy.copy(globls.vergence_error_to_plot)
            if globls.display_vergence:     # and self.vergence_selected.get():
                verg_pos_x, verg_pos_y = util.convert_deg_to_mm(vergence_error[0],
                                                                 vergence_error[1])
                verg_pos_x, verg_pos_y = util.convert_mm_to_pix(verg_pos_x, verg_pos_y)
                verg_pos_x, verg_pos_y = util.shift_to_top_left(verg_pos_x, verg_pos_y)

                # Resize to fit to UI co-ordinates
                verg_pos_x_resized = verg_pos_x / globls.arbitrator_display['x_scale_factor']
                verg_pos_y_resized = verg_pos_y / globls.arbitrator_display['y_scale_factor']

                diff_verg_pos_x = verg_pos_x_resized - self.last_eye_vergence_data[0]
                diff_verg_pos_y = verg_pos_y_resized - self.last_eye_vergence_data[1]


                # Draw vergence error with a cross mark
                if (self.vergence_eye_widget[const.X] and
                        self.vergence_eye_widget[const.Y]):
                    self.eye_canvas_obj.move(self.vergence_eye_widget[0],
                                            diff_verg_pos_x,
                                            diff_verg_pos_y)
                    self.eye_canvas_obj.move(self.vergence_eye_widget[1],
                                            diff_verg_pos_x,
                                            diff_verg_pos_y)
                else:

                    posx, posy = self.get_line_pos(verg_pos_x_resized, verg_pos_y_resized, True)
                    # Draw the line with '\'
                    self.vergence_eye_widget[const.X] = self.eye_canvas_obj.create_line(
                        posx[0], posy[0], posx[1], posy[1], fill='black')
                    # Draw the line with '/'
                    self.vergence_eye_widget[const.Y] = self.eye_canvas_obj.create_line(
                        posx[2], posy[2], posx[3], posy[3], fill='black')

                # Draw window
                #if self.vergence_window_size_changed:
                if not self.vergence_window or vergence_error[2] != self.last_eye_vergence_data[2]:
                    if self.vergence_window:
                        self.eye_canvas_obj.delete(self.vergence_window)
                        self.vergence_window = None

                    verg_diameter, tmp = util.convert_deg_to_pix(vergence_error[2])
                    verg_pos_x, verg_pos_y = util.convert_deg_to_mm(0, 0)
                    verg_pos_x, verg_pos_y = util.convert_mm_to_pix(verg_pos_x, verg_pos_y)
                    verg_pos_x, verg_pos_y = util.shift_to_top_left(verg_pos_x, verg_pos_y)

                    self.vergence_window = self.draw_window(verg_pos_x, verg_pos_y,
                                                            color='black', win_size=verg_diameter/2)

                    self.vergence_window_size_changed = False
                self.last_eye_vergence_data = [verg_pos_x_resized, verg_pos_y_resized, vergence_error[2]]
            else:
                self.eye_canvas_obj.delete(self.vergence_eye_widget[0])
                self.eye_canvas_obj.delete(self.vergence_eye_widget[1])
                self.vergence_eye_widget[0] = None
                self.vergence_eye_widget[1] = None

                if self.vergence_window:
                    self.eye_canvas_obj.delete(self.vergence_window)
                    self.vergence_window = None

        except Exception as e:
            log.exception(e)


    ''' Eye and Window configuration '''
    def draw_eye_and_window_config(self):
        # Draw the frame and widgets for offset, gain

        eye_win_widget = GuiWidget['eye_window_config']
        eye_win_config = WidgetApi.draw_frame(globls.gui_root, eye_win_widget['main_frame'])
        WidgetApi.draw_label(globls.gui_root, eye_win_widget['eye_window_label'])
        # Draw the labels in eye window configuration
        for l in eye_win_widget['config_labels']:
            WidgetApi.draw_label(eye_win_config, l)

        eye_win_widget['left_checkbutton']['variable'] = self.eye_check_button[const.LEFT]
        eye_win_widget['left_checkbutton']['command'] = self.process_left_right_checkbutton
        WidgetApi.draw_check_button(eye_win_config, eye_win_widget['left_checkbutton'])

        eye_win_widget['right_checkbutton']['variable'] = self.eye_check_button[const.RIGHT]
        eye_win_widget['right_checkbutton']['command'] = self.process_left_right_checkbutton
        WidgetApi.draw_check_button(eye_win_config, eye_win_widget['right_checkbutton'])

        # Spinboxes
        eye_win_widget['h_left_offset']['textvariable'] = self.h_left_offset
        self.left_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['h_left_offset']))
        # Horizontal Left gain spinbox
        eye_win_widget['h_left_gain']['textvariable'] = self.h_left_gain
        self.left_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['h_left_gain']))
        # Horizontal Right Offset spinbox
        eye_win_widget['h_right_offset']['textvariable'] = self.h_right_offset
        self.right_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['h_right_offset']))
        # Horizontal Right Gain spinbox
        eye_win_widget['h_right_gain']['textvariable'] = self.h_right_gain
        self.right_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['h_right_gain']))
        # vertical Left offset spinbox
        eye_win_widget['v_left_offset']['textvariable'] = self.v_left_offset
        self.left_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['v_left_offset']))
        # vertical Left gain spinbox
        eye_win_widget['v_left_gain']['textvariable'] = self.v_left_gain
        self.left_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['v_left_gain']))
        # vertical Right offset spinbox
        eye_win_widget['v_right_offset']['textvariable'] = self.v_right_offset
        self.right_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['v_right_offset']))
        # vertical Right gain spinbox
        eye_win_widget['v_right_gain']['textvariable'] = self.v_right_gain
        self.right_sb.append(WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['v_right_gain']))

        # Left pupil size spinbox
        eye_win_widget['left_pupil_size']['textvariable'] = self.pupil_size[const.LEFT]
        WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['left_pupil_size'])
        # Right pupil size spinbox
        eye_win_widget['right_pupil_size']['textvariable'] = self.pupil_size[const.RIGHT]
        WidgetApi.draw_spin_box(eye_win_config, eye_win_widget['right_pupil_size'])

        self.update_default_eye_configuration(True)
        self.update_eye_spinbox_and_window()

    def draw_tracker_window_config(self):
        # Draw the frame and widgets for offset, gain

        tracker_win_widget = GuiWidget['tracker_window_config']
        tracker_win_config = WidgetApi.draw_frame(globls.gui_root, tracker_win_widget['main_frame'])
        WidgetApi.draw_label(globls.gui_root, tracker_win_widget['tracker_window_label'])
        # Draw the labels in eye window configuration
        for l in tracker_win_widget['config_labels']:
            WidgetApi.draw_label(tracker_win_config, l)

        # Spinboxes
        tracker_win_widget['h_offset']['textvariable'] = self.h_left_offset
        self.left_sb.append(WidgetApi.draw_spin_box(tracker_win_config, tracker_win_widget['h_offset']))
        # Horizontal Left gain spinbox
        tracker_win_widget['h_gain']['textvariable'] = self.h_left_gain
        self.left_sb.append(WidgetApi.draw_spin_box(tracker_win_config, tracker_win_widget['h_gain']))
        # vertical Left offset spinbox
        tracker_win_widget['v_offset']['textvariable'] = self.v_left_offset
        self.left_sb.append(WidgetApi.draw_spin_box(tracker_win_config, tracker_win_widget['v_offset']))
        # vertical Left gain spinbox
        tracker_win_widget['v_gain']['textvariable'] = self.v_left_gain
        self.left_sb.append(WidgetApi.draw_spin_box(tracker_win_config, tracker_win_widget['v_gain']))

        #self.update_default_eye_configuration(True)
        #self.update_eye_spinbox_and_window()

    def update_default_eye_configuration(self, init=False):
        '''
        Update the eye configuration during initilization and when a subject specific configuration is loaded
        :param init:
        :return:
        '''
        status = globls.eye_selected['left']
        self.eye_check_button[const.LEFT].set(status)

        status = globls.eye_selected['right']
        self.eye_check_button[const.RIGHT].set(status)

        if init:
            self.h_left_gain.set(1)
            self.h_left_offset.set(0)
            self.h_right_gain.set(1)
            self.h_right_offset.set(0)
            self.v_left_gain.set(1)
            self.v_left_offset.set(0)
            self.v_right_gain.set(1)
            self.v_right_offset.set(0)
        else:
            self.h_left_gain.set(globls.offset_gain_config['left_gain_x'])
            self.h_left_offset.set(globls.offset_gain_config['left_offset_x'])
            self.v_left_gain.set(globls.offset_gain_config['left_gain_y'])
            self.v_left_offset.set(globls.offset_gain_config['left_offset_y'])

            self.h_right_gain.set(globls.offset_gain_config['right_gain_x'])
            self.h_right_offset.set(globls.offset_gain_config['right_offset_x'])
            self.v_right_gain.set(globls.offset_gain_config['right_gain_y'])
            self.v_right_offset.set(globls.offset_gain_config['right_offset_y'])

        self.pupil_size[const.LEFT].set(globls.pupil_size['left'])
        self.pupil_size[const.RIGHT].set(globls.pupil_size['right'])

    def update_eye_spinbox_and_window(self):
        '''
             Enable the spinbox based on the Right or Left check box is enabled
        '''
        # Left
        status = tk.DISABLED
        if globls.eye_selected['left']:
            status = tk.NORMAL

        # Update this flag to ensure the window gets updated
        globls.update_centre_window_on_off(True)

        # Set the status accordingly
        for sb in self.left_sb:
            sb.configure(state=status)

        # Right
        status = tk.DISABLED
        if globls.eye_selected['right']:
            status = tk.NORMAL
        # Set the status accordingly
        for sb in self.right_sb:
            sb.configure(state=status)

    def process_left_right_checkbutton(self):

        globls.eye_selected['left'] = self.eye_check_button[const.LEFT].get()
        globls.eye_selected['right'] = self.eye_check_button[const.RIGHT].get()

        self.update_eye_spinbox_and_window()

    ''' Calibration configuration processing '''
    def draw_eye_calibration_task_button(self):
        '''
        Draw frames and widgets for parameters related to eye calibration
        :return:
        '''
        eye_calib_widgets = GuiWidget['eye_calibration']
        calib_frame = WidgetApi.draw_frame(globls.gui_root, eye_calib_widgets['main_frame'])

        eye_calib_widgets['calibration_checkbutton']['variable'] = self.task_checkbutton
        eye_calib_widgets['calibration_checkbutton']['command'] = self.process_task
        WidgetApi.draw_check_button(calib_frame, eye_calib_widgets['calibration_checkbutton'])

        self.calibration_type.set(0)
        eye_calib_widgets['manual_calibration_checkbutton']['variable'] = self.calibration_type
        eye_calib_widgets['manual_calibration_checkbutton']['command'] = self.process_calibration_flag
        self.manual_checkbutton = WidgetApi.draw_check_button(
            calib_frame,
            eye_calib_widgets['manual_calibration_checkbutton'])

        self.manual_calib_cur_idx.set(CalibrationListIndex.CENTER)

        for rb in eye_calib_widgets['manual_radiobutton']:
            rb['variable'] = self.manual_calib_cur_idx
            rb['command'] = self.process_manual_calibration_radiobutton
            rb_obj = WidgetApi.draw_radio_button(calib_frame, rb)
            self.manual_radiobutton.append(rb_obj)
        self.manual_radiobutton[CalibrationListIndex.CENTER].select()

        #eye_calib_widgets['auto_calibration_checkbutton']['variable'] = self.calibration_type
        #eye_calib_widgets['auto_calibration_checkbutton']['command'] = self.process_calibration_flag
        #self.auto_checkbutton = WidgetApi.draw_check_button(
         #   calib_frame,
         #   eye_calib_widgets['auto_calibration_checkbutton'])

        # Draw all the labels
        #for label in eye_calib_widgets['labels']:
         #   WidgetApi.draw_label(calib_frame, label)

        # Draw all the entries and collect the entries in a list for reading and processing
        '''
        self.auto_calib_entries = []
        for entry_dict in eye_calib_widgets['entries']:
            # Read from configuration
            value = globls.calibration_config['auto'][entry_dict['field']]
            entry_dict['value'] = value
            ent = WidgetApi.draw_entry(calib_frame, entry_dict)

            self.auto_calib_entries.append((entry_dict['field'], ent, entry_dict))
        '''

        self.initilize_auto_calibration_points()

        # On, Off, clear, cancel

        #eye_calib_widgets['submit_button']['command'] = lambda e=self.auto_calib_entries: self.calib_config_submit_data(e)
        # self.calib_config_submit = WidgetApi.draw_button(calib_frame,
        #                                                  eye_calib_widgets['submit_button'])


        eye_calib_widgets['accept_button']['command'] = self.accept_measured_eyepos
        self.accept_button = WidgetApi.draw_button(calib_frame, eye_calib_widgets['accept_button'])

        eye_calib_widgets['cancel_button']['command'] = self.process_cancel_last_accepted_data
        self.cancel_lastdata_button = WidgetApi.draw_button(calib_frame,
                                                             eye_calib_widgets['cancel_button'])

        eye_calib_widgets['calibrate_button']['command'] = self.procces_calibrate
        self.calibrate_button = WidgetApi.draw_button(calib_frame, eye_calib_widgets['calibrate_button'])

        eye_calib_widgets['clear_button']['command'] = self.init_calibration_configuration_parameter
        self.clear_button = WidgetApi.draw_button(calib_frame, eye_calib_widgets['clear_button'])

    def set_calibration_config(self, config):
        globls.update_calibration_config(config)

        for entries in self.auto_calib_entries:
            value = globls.calibration_config['auto'][entries[0]]
            entries[1].delete(0, 'end')
            entries[1].insert(0, value)
        self.initilize_auto_calibration_points()
        self.init_calibration_configuration_parameter()

    def init_calibration_configuration_parameter(self, init=False):
        '''
        Clear the calibrated parameters on click of clear button on GUI
        :param init:
        :return:
        '''
        # Get X and Y deg for the manual calibration
        self.manual_calibration_points = [[-1, 1], [0, 1], [1, 1],
                                            [-1, 0], [0, 0], [1, 0],
                                            [-1, -1], [0, -1], [1, -1]]
        x_deg = globls.calibration_config['manual']['x'] * globls.calibration_config['manual']['percent_area'] / 100
        y_deg = globls.calibration_config['manual']['y'] * globls.calibration_config['manual']['percent_area'] / 100
        for calib_pt in self.manual_calibration_points:
            calib_pt[0] = calib_pt[0] * x_deg
            calib_pt[1] = calib_pt[1] * y_deg

        if not init:
            data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.CLEAR)
            util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                           'Clear calibrated values ')

            self.h_left_gain.set(str(1))
            self.h_left_offset.set(str(0))
            self.h_right_gain.set(str(1))
            self.h_right_offset.set(str(0))
            self.v_left_gain.set(str(1))
            self.v_left_offset.set(str(0))
            self.v_right_gain.set(str(1))
            self.v_right_offset.set(str(0))

        for i in range(len(self.accepted_eyepos_ploted_widget)):
            self.eye_canvas_obj.delete(self.accepted_eyepos_ploted_widget[i][const.LEFT])
            self.eye_canvas_obj.delete(self.accepted_eyepos_ploted_widget[i][const.RIGHT])

        for rb in self.manual_radiobutton:
            rb.configure(selectcolor='white')

        self.accepted_eyepos_ploted_widget = []
        self.manual_points_color_marker = []

        calib.init_calibration_parameter()


    def process_calibration_flag(self):
        '''
            Process Manual and Auto calibration
        '''
        if not self.task_checkbutton.get() == Task.CALIBRATION:
            self.display_warning_error_message("Error, Incorrect Option Selection ",
                                   "Please check the calibration before proceeding")
            self.calibration_type.set(self.calibration_type_prev)
            return

        #if self.calibration_type.get() == Calibration.MANUAL:
         #   self.auto_checkbutton.configure(state=tk.DISABLED)
        if self.calibration_type.get() == Calibration.AUTO:
            self.manual_checkbutton.configure(state=tk.DISABLED)
        else:
            if self.task_in_progress:
                self.display_warning_error_message("Error Selection",
                                       "Please click on 'Stop' to proceed\nwith this action")
                self.calibration_type.set(self.calibration_type_prev)
            else:
                '''Dont currently allow auto calibration'''
                #self.auto_checkbutton.configure(state=tk.DISABLED)
                self.manual_checkbutton.configure(state=tk.NORMAL)
        self.calibration_type_prev = self.calibration_type.get()

    def process_manual_calibration_radiobutton(self):
        # If auto calibration enabled and start is executed only then allow
        # this operation
        if (self.calibration_type.get() != Calibration.MANUAL or
            self.startbutton['state'] == tk.NORMAL):
            self.display_warning_error_message("Error Selection",
                                    "Please check if Manual check button is enabled\nor Start button is pressed")
            self.manual_calib_cur_idx.set(CalibrationListIndex.CENTER)
            return

        # Select x, y position to display
        self.select_center_xy_position()

    def update_calibration_widgets(self, button_state=tk.NORMAL, checkbutton_state=tk.NORMAL):
        #self.calib_config_submit.configure(state=button_state)
        self.calibrate_button.configure(state=button_state)
        self.accept_button.configure(state=button_state)
        self.cancel_lastdata_button.configure(state=button_state)
        self.clear_button.configure(state=button_state)

        self.manual_checkbutton.configure(state=checkbutton_state)
        '''Dont currently allow auto calibration'''
        #self.auto_checkbutton.configure(state=tk.DISABLED)
        #self.calibration_type.set(0)

    def calib_config_submit_data(self, entries):
        '''
        Submit the calibration read data
        :param entries:
        :return:
        '''
        try:
            for e in entries:
                field = e[0]
                value = e[1].get()
                field_dict = e[2]

                status, msg, val = self.__validate_field(field, value, field_dict)
                if not status:
                    self.display_warning_error_message("Invalid Input",msg)
                    e[1].delete(0, 'end')
                    return

                if val is None:
                    self.log_to_textbox('Unknown {}'.format(field), MessageType.ERROR)
                    continue
                globls.calibration_config['auto'][field] = val

            # Get the Target points
            if self.auto_calibration_points.shape[0] > 0:
                # clear all the points
                for pt_win in self.centre_pt_window_widget:
                    # Left window widget
                    if pt_win[0]: self.eye_canvas_obj.delete(pt_win[0])
                    # Right window widget
                    if pt_win[1]: self.eye_canvas_obj.delete(pt_win[0])

                    # Left pt widget
                    if pt_win[2]: self.eye_canvas_obj.delete(pt_win[2])
                    # Right pt widget
                    if pt_win[3]: self.eye_canvas_obj.delete(pt_win[3])

                self.centre_pt_window_widget = []
            self.initilize_auto_calibration_points()
        except Exception as e:
            log.exception(e)

        self.log_to_textbox("Total number of Target points to calibrate {}".format(self.auto_calibration_points.shape[0]))

    def initilize_auto_calibration_points(self):
        '''
        centre Points to be displayed for calibriation
        :return:
        '''
        try:
            # Add 1 to the max to make the stop inclusive
            x_pts = np.arange(globls.calibration_config['auto']['target_pos_horizantal_min'],
                              globls.calibration_config['auto']['target_pos_horizantal_max'] + .01,
                              globls.calibration_config['auto']['target_pos_horizantal_step'])
            y_pts = np.arange(globls.calibration_config['auto']['target_pos_vertical_min'],
                              globls.calibration_config['auto']['target_pos_vertical_max'] + .01,
                              globls.calibration_config['auto']['target_pos_vertical_step'])
            if (not globls.calibration_config['auto']['target_pos_depth_min'] and
                    not globls.calibration_config['auto']['target_pos_depth_max']):
                z_pts = np.array([0])
            else:
                z_pts = np.arange(globls.calibration_config['auto']['target_pos_depth_min'],
                                  globls.calibration_config['auto']['target_pos_depth_max'] + .01,
                                  globls.calibration_config['auto']['target_pos_depth_step'])

            self.auto_calibration_points = np.array(np.meshgrid(x_pts, y_pts, z_pts)).T.reshape(-1, 3)
            np.random.shuffle(self.auto_calibration_points)
            self.auto_calib_cur_index = 0

        except ValueError as e:
            log.exception(e)

    def select_center_xy_position(self):
        '''
        Get the next centre point to be dispayed for calibration
        :param accepted:
        :return:
        '''
        x = 0
        y = 0
        z = 0
        if self.calibration_type.get() == Calibration.AUTO:
            # If value is accepted increment the index here
            self.auto_calib_cur_index += 1

            # see if all points are calibrated
            if self.auto_calib_cur_index >= self.auto_calibration_points.shape[0]:
                self.auto_calib_cur_index = 0
                self.procces_calibrate()
                self.display_warning_error_message("Auto Calibration Completed",
                                      "Auto calibration has been completed.")
                return False
            else:

                # Get the data and draw
                x = self.auto_calibration_points[self.auto_calib_cur_index][const.X]
                y = self.auto_calibration_points[self.auto_calib_cur_index][const.Y]
                z = self.auto_calibration_points[self.auto_calib_cur_index][const.Z]

        elif self.calibration_type.get() == Calibration.MANUAL:
            calib_task_pos = int(self.manual_calib_cur_idx.get())
            x = self.manual_calibration_points[calib_task_pos][0]
            y = self.manual_calibration_points[calib_task_pos][1]
            z = globls.depth
        else:
            self.display_warning_error_message("Error, Calibration Method Not Selected",
                                   "Please select either Manual or Auto calibration")
            self.stop(True)
            return

        x, y = util.convert_deg_to_mm(x, y)

        data = "{} {}/{} {}/{} {}/".format(const.TARGET_X, x, const.TARGET_Y, y, const.TARGET_Z, z)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data)

        return True

    def accept_measured_eyepos(self):
        '''
            process accept calibration button
        '''
        # Accept the measured eye position
        left_mean, right_mean = calib.process_accept_measured_eye_pos()
        # Draw the accepted mean eye position. This has to be done from the UI thread
        self.draw_accepted_measured_eye_pos_data(left_mean, right_mean)

        data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.ACCEPT)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                       'Accept ')

        # Get the next (X, Y) centre points if all the ppoints are exhausted then stop the experiment
        if self.calibration_type.get() == Calibration.AUTO:
            resp = self.select_center_xy_position()
            # In auto calibration if all the points are displayed then stop
            if not resp:
                self.stop()
                return
        elif self.calibration_type.get() == Calibration.MANUAL:
            calib_task_eye_pos = int(self.manual_calib_cur_idx.get())
            self.manual_points_color_marker.append(calib_task_eye_pos)
            # Set this to red to indicate calibration is accepted for the radio button position
            self.manual_radiobutton[calib_task_eye_pos].configure(selectcolor='red')

    def procces_calibrate(self):
        '''
        process calibrate button
        :return:
        '''
        if calib.get_length_of_accepted_moving_eye_position() < 5:
            self.display_warning_error_message("Warning, Incomplete Calibration",
                "A minimum of 5 accepted values is needed to calibrate.")
            return

        data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.CALIBRATE)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                       'Calibrate ')

        calib.calculate_offset_gain()

        # Set the new offset and gain on GUI widget
        self.h_left_gain.set(globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_X])
        self.h_left_offset.set(globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_X])
        self.v_left_gain.set(globls.offset_gain_config[ConfigLabels.LEFT_EYE_GAIN_Y])
        self.v_left_offset.set(globls.offset_gain_config[ConfigLabels.LEFT_EYE_OFFSET_Y])
        self.h_right_gain.set(globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_X])
        self.h_right_offset.set(globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_X])
        self.v_right_gain.set(globls.offset_gain_config[ConfigLabels.RIGHT_EYE_GAIN_Y])
        self.v_right_offset.set(globls.offset_gain_config[ConfigLabels.RIGHT_EYE_OFFSET_Y])

        self.init_calibration_configuration_parameter(init=True)

        # update to centre point and wait for the periodic call to draw
        globls.update_centre_point(0, [])

    def process_cancel_last_accepted_data(self):
        '''
        process cancal last acceptd calbration point button
        :return:
        '''
        if calib.get_length_of_accepted_moving_eye_position() == 0:
            self.display_warning_error_message("Unable to Cancel Accepted Values",
                "No values have been accepted yet.")
            return

        data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.CANCEL)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                       'Cancel last accepted data point ')

        # Reset the calibration parameters
        calib.cancel_last_accepted_data()

        # delete the widget and redraw
        if self.calibration_type == Calibration.AUTO:
            if self.auto_calib_cur_index > 0:
                self.auto_calib_cur_index -= 1
        else:
            duplicates = [k for k,v in collections.Counter(self.manual_points_color_marker).items() if v>1]
            if self.manual_points_color_marker[-1] not in duplicates:
                self.manual_radiobutton[self.manual_points_color_marker[-1]].configure(selectcolor='white')
            self.manual_points_color_marker.pop(-1)

        self.eye_canvas_obj.delete(self.accepted_eyepos_ploted_widget[-1][const.LEFT])
        self.eye_canvas_obj.delete(self.accepted_eyepos_ploted_widget[-1][const.RIGHT])
        self.accepted_eyepos_ploted_widget.pop(-1)

    def draw_accepted_measured_eye_pos_data(self, left_mean, right_mean):
        '''
        Draw the accepted measred eye postion on the GUI
        :param left_mean:
        :param right_mean:
        :return:
        '''
        # Convert it to pix and co-ordinate 0,0 starting on top left
        lx, ly = util.convert_mm_to_pix(left_mean[const.X],
                                                left_mean[const.Y])
        left_x, left_y = util.shift_to_top_left(lx, ly)


        # Convert it to pix and co-ordinate 0,0 starting on top left
        rx, ry = util.convert_mm_to_pix(right_mean[const.X],
                                                right_mean[const.Y])
        right_x, right_y = util.shift_to_top_left(rx, ry)

        left_pt_widget = self.draw_point(left_x, left_y, color='green')
        right_pt_widget = self.draw_point(right_x, right_y, color='blue')

        # update the widget value
        self.accepted_eyepos_ploted_widget.append([left_pt_widget, right_pt_widget])

    @staticmethod
    def __validate_field(field, val, entry_dict):
        '''
        Common function to validate the fields
        :param field:
        :param val:
        :param entry_dict:
        :return:
        '''
        msg = "No input provided"
        if not val or entry_dict.get('field') != field:
            return False, msg, None

        try:
            data_validation = entry_dict
            if data_validation.get('type') == 'int':
                msg = "Please correct {}.\nField should be an Integer".format(field)
                v = int(val)
                if v < data_validation.get('min', 0) or v > data_validation.get('max', 0):
                    msg = "Please correct {}.\nInput not in allowed range".format(field)
                    return False, msg, int(val)
                return True, 'success', int(val)
            elif data_validation.get('type') == 'float':
                msg = "Please correct {}.\nField should be a float".format(field)
                v = float(val)
                if v < data_validation.get('min', 0) or v > data_validation.get('max', 0):
                    msg = "Please correct {}.\nInput not in allowed range".format(field)
                    return False, msg, float(val)
                return True, 'success', float(val)
            elif data_validation.get('type') == 'string':
                if len(val) > data_validation.get('length'):
                    msg = "Please correct {}.\nInput not in allowed range".format(field)
                    return False, msg, str(val)
                return True, 'sucess', str(val)
            return False, msg, None
        except ValueError:
            return False, msg, val
        except Exception as e:
            log.exception(e)
            return

    def draw_callback_buttons(self):
        '''
        Draw frame and widget for custom button functions
        :return:
        '''
        custom_buttons_widget = GuiWidget['custom_buttons']
        custom_buttons_frame = WidgetApi.draw_frame(globls.gui_root, custom_buttons_widget['main_frame'])


        for b in range(len(custom_buttons_widget['buttons'])):
            custom_buttons_widget['buttons'][b]['command'] = globls.custom_button_callbacks.linker_list[b]
            globls.custom_button.append(WidgetApi.draw_button(custom_buttons_frame,
                                                            custom_buttons_widget['buttons'][b]))


    ''' Receptive field mapping '''
    def draw_receptive_field_mapping_window(self):
        '''
        Draw frame and widget for receptive field mapping
        :return:
        '''
        receptive_field_widgets = GuiWidget['receptive_field_mapping']
        receptive_field_map_frame = WidgetApi.draw_frame(globls.gui_root, receptive_field_widgets['main_frame'])
    
        receptive_field_widgets['receptive_field_checkbutton']['variable'] = self.task_checkbutton
        receptive_field_widgets['receptive_field_checkbutton']['command'] = self.process_task
        WidgetApi.draw_check_button(globls.gui_root,receptive_field_widgets['receptive_field_checkbutton'])
    
        receptive_field_widgets['grating_checkbutton']['variable'] = self.receptive_field_map_type
        receptive_field_widgets['grating_checkbutton']['command'] = self.process_receptive_field_mapping_flag
        self.receptive_field_grating_checkbutton = WidgetApi.draw_check_button(receptive_field_map_frame,receptive_field_widgets['grating_checkbutton'])
    
        receptive_field_widgets['dots_checkbutton']['variable'] = self.receptive_field_map_type
        receptive_field_widgets['dots_checkbutton']['command'] = self.process_receptive_field_mapping_flag
        self.receptive_field_dots_checkbutton = WidgetApi.draw_check_button(receptive_field_map_frame,receptive_field_widgets['dots_checkbutton'])

        receptive_field_widgets['bar_checkbutton']['variable'] = self.receptive_field_map_type
        receptive_field_widgets['bar_checkbutton']['command'] = self.process_receptive_field_mapping_flag
        self.receptive_field_bar_checkbutton = WidgetApi.draw_check_button(receptive_field_map_frame,receptive_field_widgets['bar_checkbutton'])

        # Assume initial stim start is 0,0 - update using dragging/mouse clicks in canvas
        receptive_field_widgets['stimpos_text_label']['textvariable'] = self.stim_pos_text
        WidgetApi.draw_label(receptive_field_map_frame, receptive_field_widgets['stimpos_text_label'])

        # Draw labels
        for label in receptive_field_widgets['labels']:
            WidgetApi.draw_label(receptive_field_map_frame, label)
    
        # Draw all the entries and collect the entries in a list for reading and processing
        self.receptive_field_entries = []
        for entry_dict in receptive_field_widgets['entries']:
            # Read from configuration
            value = globls.receptive_field_map[entry_dict['field']]
            entry_dict['value'] = value
            ent = WidgetApi.draw_entry(receptive_field_map_frame, entry_dict)
    
            self.receptive_field_entries.append((entry_dict['field'], ent, entry_dict))
    
        receptive_field_widgets['submit_button']['command'] = self.process_receptive_field_mapping
        self.receptive_field_button = WidgetApi.draw_button(receptive_field_map_frame, receptive_field_widgets['submit_button'])
    
    def update_receptive_field_mapping_widget(self, state=tk.NORMAL):
        self.receptive_field_button.configure(state=state)
        self.receptive_field_grating_checkbutton.configure(state=state)
        self.receptive_field_dots_checkbutton.configure(state=state)
        self.receptive_field_bar_checkbutton.configure(state=state)
        self.receptive_field_map_type.set(0)

    def process_receptive_field_mapping_flag(self, entries=None):
        # process the receptive field mapping check boxes
        if self.receptive_field_map_type.get() == FieldMapping.DOTS:
            self.receptive_field_grating_checkbutton.configure(state=tk.DISABLED)
            self.receptive_field_bar_checkbutton.configure(state=tk.DISABLED)
        elif self.receptive_field_map_type.get() == FieldMapping.GRATING:
            self.receptive_field_dots_checkbutton.configure(state=tk.DISABLED)
            self.receptive_field_bar_checkbutton.configure(state=tk.DISABLED)
        elif self.receptive_field_map_type.get() == FieldMapping.BAR:
            self.receptive_field_dots_checkbutton.configure(state=tk.DISABLED)
            self.receptive_field_grating_checkbutton.configure(state=tk.DISABLED)
        elif self.receptive_field_map_type.get() == 0:
            self.receptive_field_dots_checkbutton.configure(state=tk.NORMAL)
            self.receptive_field_grating_checkbutton.configure(state=tk.NORMAL)
            self.receptive_field_bar_checkbutton.configure(state=tk.NORMAL)

    def process_receptive_field_mapping(self):
        #Submit and  read data
        #param entries:
        #return:

        try:
            data_to_send = ''
            for e in self.receptive_field_entries:
                field = e[0]
                value = e[1].get()
                field_dict = e[2]
                # Validate the field entries
                status, msg, val = self.__validate_field(field, value, field_dict)
                if not status:
                    self.display_warning_error_message("Invalid Input",msg)
                    e[1].delete(0, 'end')
                    return

                if val is None:
                    self.log_to_textbox('Unknown {}'.format(field), MessageType.ERROR)
                    continue
                # Send MATLAB the correct information
                globls.receptive_field_map[field] = val
                command_word = field_dict.get('command')  #int(entries[1].get())
                data_word = globls.receptive_field_map[field]
                data_to_send += '{} {}/'.format(command_word, data_word)

            # Indicate whether grating, bar, or dots
            command_word = GuiWidget['receptive_field_mapping']['grating_checkbutton']['cmd']
            if self.receptive_field_map_type.get() == FieldMapping.GRATING:
                data_word = FieldMapping.GRATING
            elif self.receptive_field_map_type.get() == FieldMapping.DOTS:
                data_word = FieldMapping.DOTS
            elif self.receptive_field_map_type.get() == FieldMapping.BAR:
                data_word = FieldMapping.BAR
            data_to_send += '{} {}/'.format(command_word, data_word)
             # If the total length exceeds specified limit just send the partial set
            util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr,
                        data_to_send, 'ReceptiveFieldUpdate')
            #data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.ACCEPT)
            #util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr,
             #           data, 'ReceptiveFieldUpdate')
            data_to_send = ''
            #self.pause()
            #self.start()

        except ValueError:
            return False, msg, val

    ''' control button processing '''
    def draw_control_buttons(self):
        '''
        Draw frame and widgets for start, stop, pause and exit
        :return:
        '''
        task_control_widget = GuiWidget['task_controls']
        button_frame = WidgetApi.draw_frame(globls.gui_root, task_control_widget['main_frame'])

        WidgetApi.draw_label(globls.gui_root, task_control_widget['task_control_label'])

        self.task_file_entry = WidgetApi.draw_entry(button_frame, task_control_widget['task_file_entry'])
        WidgetApi.draw_label(button_frame, task_control_widget['task_file_label'])

        task_control_widget['task_file_load']['command'] = lambda e='Load': self.process_load_save_task_file(e)
        loadbutton = WidgetApi.draw_button(button_frame, task_control_widget['task_file_load'])
        loadbutton.bind('<Return>', lambda event, key='<space>': loadbutton.event_generate(key))

        task_control_widget['task_file_save']['command'] = lambda e='Save': self.process_load_save_task_file(e)
        savebutton = WidgetApi.draw_button(button_frame, task_control_widget['task_file_save'])
        savebutton.bind('<Return>', lambda event, key='<space>': savebutton.event_generate(key))

        task_control_widget['start_button']['command'] = self.start
        self.startbutton = WidgetApi.draw_button(button_frame, task_control_widget['start_button'])
        task_control_widget['pause_button']['command'] = self.pause
        self.pausebutton = WidgetApi.draw_button(button_frame, task_control_widget['pause_button'])
        task_control_widget['stop_button']['command'] = self.stop
        self.stopbutton = WidgetApi.draw_button(button_frame, task_control_widget['stop_button'])
        task_control_widget['exit_button']['command'] = self.on_exit
        self.exitbutton = WidgetApi.draw_button(button_frame, task_control_widget['exit_button'])

    def process_load_save_task_file(self, operation):
        try:
            filename = self.task_file_entry.get()
            if not len(filename):
                self.display_warning_error_message("Error, Incorrect Entry Specified",
                                       "Please enter the file to {}".format(operation))
                return

            CURDIR = const.CUR_DIR_NAME
            file = os.path.join(CURDIR, filename)
            if operation == 'Load':
                data = self.file.read(file)
                if not data:
                    self.display_warning_error_message("Error, Could Not Find File",
                                           "Please check if the file exists")
                    return None

                if data.get('config_to_edit'):
                    self.set_editable_configuration(data['config_to_edit'])
                if data.get('config_to_display'):
                    self.set_displayable_config(data['config_to_display'])
                if data.get('calibration'):
                    self.set_calibration_config(data['calibration'])
                self.update_task_subject_file_loaded(task_file=True)
                command_value = const.LOAD_TASK
            else:
                config = {}
                config['config_to_edit'] = []
                for entry in self.editable_configuration_entries:
                    name = entry[0].get()
                    command_word = entry[1].get()
                    if len(name) and len(command_word):
                        config['config_to_edit'].append([name, command_word, entry[2].get()])

                config['config_to_display'] = []
                od = collections.OrderedDict(sorted(self.displayable_widget_config.items()))
                for k, v in od.iteritems():
                    name = v['command_label'].get()
                    command = v['command_word'].get()
                    if len(name) and len(command):
                        config['config_to_display'].append([name, command, 0])


                if self.task_checkbutton.get() == Task.CALIBRATION:
                    config['calibration'] = globls.calibration_config

                self.file.write(config, file)
                command_value = const.SAVE_TASK

            data = "{} {}/".format(const.COMMAND_WORD_CONTROL, command_value)
            util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                           'Task {} '.format(operation))

        except Exception as e:
            log.exception(e)
            self.display_warning_error_message("Error, Incorrect Entry Specified",
                                   "Please do not use special characters")

    def start(self):
        # Start the task

        try:
            self.startbutton['state'] = tk.DISABLED
	    self.pausebutton['state'] = tk.NORMAL
            self.submit_configuration_data()
            self.process_receptive_field_mapping()

            data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.CONTROL_START)
            util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                           'Send Start Command')

            #  After un pausing collect data from here. hence enable flag
            if self.task_in_progress:
                DataFileObj.update_data_collect_flag(True)

            # Create the data file to write the data.
            # On stop write the entire data to file and reset the file for next
            # start
            # between pause and start this file would not be overwritten but
            # data would be written as the experiments are unpaused
            if not DataFileObj.is_data_file_created():
                # Create the file
                DataFileObj.update_file_name(globls.subject_name)
                DataFileObj.update_header_into_data_file()

            # Based on task start the task
            self.task_in_progress = True
            if self.task_checkbutton.get() == Task.CALIBRATION:
                self.select_center_xy_position()

            if self.task_checkbutton.get() == Task.RECEPTIVE_FIELD_MAPPING:
                #self.receptive_field_button.invoke
                #self.process_receptive_field_mapping_flag()
                e=self.receptive_field_entries
                self.process_receptive_field_mapping(e)
                #receptive_field_widgets['submit_button']['command']


        except Exception as e:
            log.exception(e)
            self.log_to_textbox('Exception sending Start data to matlab', MessageType.ERROR)
            return

        

    def pause(self):
        '''
        Pause the task
        :return:
        '''
        # do not collect data when it is paused
        DataFileObj.update_data_collect_flag(False)
        self.pausebutton['state'] = tk.DISABLED

        data = "{} {}/".format(const.COMMAND_WORD_CONTROL,
                               const.CONTROL_PAUSE
                               )
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                       'Send Pause command')

        self.startbutton['state'] = tk.NORMAL

    def stop(self, task_just_started=False):
        # Stop the task

        """ When you click to Stop, this Ensure to ask if task and subject config should be saved """
        if not task_just_started:
            if tkMessageBox.askyesno("End Session?",
                                     "Do you want to save the Task or Subject configuration files? Click 'Yes' to return to the GUI to save them, or 'No' to end the session"):
                return

        # Do not collect data on stop
        # Write data to the file and reset the data filename for next experiment
        DataFileObj.dump_data_to_file()
        DataFileObj.total_data_dumped_to_file()
        DataFileObj.reset_file_name()
        self.task_in_progress = False
        data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.CONTROL_STOP)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                       'Send Stop command')

        # Disable the buttons but keep the checkbuttons normal in case some one wants to run it again
        self.update_calibration_widgets(checkbutton_state=tk.DISABLED)
        self.update_receptive_field_mapping_widget(state=tk.DISABLED)
        self.init_calibration_configuration_parameter()
        self.task_checkbutton.set(0)
        self.canvas_mouse_checkbutton.set(0)
        self.last_sel_canvas_mouse_checkbutton = 0
        self.last_selected_task = 0
        globls.update_centre_point(0, [])
        globls.update_centre_window_on_off(False)
        globls.udpdate_vergence_display(False)
        globls.update_last_sent_eye_in_out([-1, -1])
        globls.update_last_sent_vergence_error(-1)
        globls.update_depth(0)
        globls.update_displayable_config()

        if not task_just_started:
            # Clean up few global parameters which are required for the experiment
            self.update_task_subject_file_loaded(subject_file=False, task_file=False)
            self.task_file_entry.delete(0, 'end')
            self.subject_config_entry.delete(0, 'end')
            self.set_displayable_config([])
            self.set_editable_configuration([])
        else:
            self.startbutton['state'] = tk.NORMAL
            self.pausebutton['state'] = tk.NORMAL

        # Clean up the required parameters here

    def on_exit(self):
        """ When you click to exit, this function is called """
        if tkMessageBox.askyesno("Close GUI?",
                                 "Do you want to save the Task or Subject configuration files? Click 'Yes' to return to the GUI to save them, or 'No' to close the GUI"):
            return

        # send stop signal to collect data
        DataFileObj.dump_data_to_file()
        DataFileObj.total_data_dumped_to_file()
        DataFileObj.reset_file_name()

        data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.CONTROL_EXIT)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr,
                       data, 'Exit command')
        globls.dump_log('Closing all socket and threads')
        # Send this message to self socket to wakeup the socket which is waiting on the
        # arbitrator server and close. Making exit a smooth
        util.send_data(globls.arbitrator_sock,
                       ('127.0.0.1', globls.config_param['arbitrator_service']['local_port']),
                       data, 'Exit command to self')

        # Update this flag to stop all processing
        globls.is_program_running = False

    ''' Scrolled text '''
    def draw_scrolled_text(self):
        '''
        Draw frames and wigets for scrolled text
        :return:
        '''
        scrolled_widgets = GuiWidget['scrolled_text']
        scrolled_text_frame = WidgetApi.draw_frame(globls.gui_root, scrolled_widgets['main_frame'])
        WidgetApi.draw_label(globls.gui_root, scrolled_widgets['scrolled_text_label'])

        scrolledtext = WidgetApi.draw_scrolledtext(scrolled_text_frame, scrolled_widgets['text_frame'])
        return scrolledtext

    def log_to_textbox(self, msg, msg_type=MessageType.DEBUG, log_to_ui=True):
        try:
            '''
            Log or dump the logs to GUI
            :param msg:
            :param msg_type:
            :param log_to_ui:
            :return:
            '''
            if log_to_ui:
                # self.text.configure(state='normal')
                if self.text_data >= const.MAX_NO_OF_LINES_TO_DISPLAY:
                    self.text.delete('1.0', tk.END)
                    self.text.mark_set("sentinel", tk.INSERT)
                    self.text.mark_gravity("sentinel", tk.LEFT)
                    self.text.see("end")
                    self.text_data = 0

                time.ctime()
                self.text_data += 1
                self.text.insert(tk.END, "{}:{}: {} \n"
                                 .format(msg_type, time.strftime('%m-%d-%y:%H.%M.%S'), msg)
                                 )
                self.text.see("end")
                # self.text.configure(state='disabled')
        except Exception as e:
            log.exception(e)

        log.debug(msg)

    ''' Draw the canvas frames and widgets '''
    def draw_canvas_for_eye_movements(self, width, height):
        '''
        Draw frames and widgets for capturing eye movement
        :return:
        '''
        display_widget = GuiWidget['eye_display']
        canvas_frame = WidgetApi.draw_frame(globls.gui_root, display_widget['main_frame'])

        # Draw canvas
        canvas = WidgetApi.draw_canvas(canvas_frame, display_widget['canvas'])

        # Left Button pressed down
        canvas.bind("<Button-1>", self.mouse_button_pressed)
        # Left button moved while pressed down
        canvas.bind("<B1-Motion>", self.canvas_mouse_position)
        # Left button released
        canvas.bind("<ButtonRelease-1>", self.mouse_button_released)

        display_widget['eyepos_text_label']['textvariable'] = self.eye_pos_text
        WidgetApi.draw_label(canvas_frame, display_widget['eyepos_text_label'])

        #display_widget['zoomout_button']['command'] = lambda zoomout=1: self.display_zoom(zoomout)
        #WidgetApi.draw_button(canvas, display_widget['zoomout_button'])
        #display_widget['zoomin_button']['command'] = lambda zoomin=0: self.display_zoom(zoomin)
        #WidgetApi.draw_button(canvas, display_widget['zoomin_button'])
        '''
        WidgetApi.draw_label(canvas_frame, display_widget['depth_label'])
        self.depth_entry = WidgetApi.draw_entry(canvas_frame, display_widget['depth_entry'])
        '''
        self.canvas_mouse_checkbutton.set(0)
        for check_button in display_widget['mouse_checkbutton']:
            check_button['variable'] = self.canvas_mouse_checkbutton
            check_button['command'] = self.process_canvas_mouse_checkbutton
            WidgetApi.draw_check_button(canvas_frame, check_button)

        # Update GUI screen parameter to calulcate the scale factor
        globls.update_gui_display_param(width, height,
                                        display_widget['main_frame']['relwidth'], display_widget['main_frame']['relheight'],
                                        display_widget['canvas']['relwidth'], display_widget['canvas']['relheight'])
        globls.update_gui_scale_factor()
        return canvas

    # Process the checkbutton on canvas
    def process_canvas_mouse_checkbutton(self):
        if not self.check_task_readiness(load_file=True):
            self.display_warning_error_message("Warning. Subject or Task File Not Loaded",
                                   "Please load Subject and Task file to proceed.")
            self.canvas_mouse_checkbutton.set(0)
            return

        mouse_checkbutton = self.canvas_mouse_checkbutton.get()
        self.last_sel_canvas_mouse_checkbutton = mouse_checkbutton

    # Process mouse pressed button on canvas
    def mouse_button_pressed(self, mouse_click_event):
        if self.canvas_mouse_checkbutton.get() == MouseClick.DRAGGING:
            # Send target on
            data = '{} 1/'.format(const.TARGET_ON)
            util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data, 'Sent Target On')

            # Send the Mouse co-ordinate
            self.canvas_mouse_position(mouse_click_event)
        elif self.canvas_mouse_checkbutton.get() == MouseClick.FEEDBACK:
            # Send the Mouse co-ordinate
            self.canvas_mouse_position(mouse_click_event)
        else:
            self.display_warning_error_message("Warning, Feedback or Dragging Not Selected",
                                     "Please select Feedback or Dragging.")
            return

    # Process mouse released button on canvas
    def mouse_button_released(self, mouse_click_event):
        if self.canvas_mouse_checkbutton.get() == 0:
            return

        # send target off
        data = '{} 1/'.format(const.TARGET_OFF)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data, 'Sent Target Off')

        # Clear the previous target if any on canvas
        if self.mouse_click_target_points:
            self.clear_window_on_canvas(self.mouse_click_target_points)
            self.mouse_click_target_points = None

    # Get canvas co-ordinates for both dragging and feedback checkbox
    def canvas_mouse_position(self, mouse_click_event):
        if self.canvas_mouse_checkbutton.get() == 0:
            return

        # if self.t1 is None:
        #     self.t1 = time.time()
        # t2 = time.time()
        # #print t2 - self.t1
        # self.t1 = t2

        # send mouse co-ordinates
        x_scaled = mouse_click_event.x * globls.arbitrator_display['x_scale_factor']
        y_scaled = mouse_click_event.y * globls.arbitrator_display['y_scale_factor']

        if x_scaled < 0:
            x_scaled = 0
        if x_scaled > globls.arbitrator_window_width:
            x_scaled = globls.arbitrator_window_width

        if y_scaled < 0:
            y_scaled = 0
        if y_scaled > globls.arbitrator_window_height:
            y_scaled = globls.arbitrator_window_height



        # Send the new target position to Arbitrator server
        x, y = util.shift_to_centre(x_scaled, y_scaled)
        x_mm, y_mm = util.convert_pix_to_mm(x, y)

         # Convert to deg if receptive field mapping to display stim pos in RF window
        if self.task_checkbutton.get()== Task.RECEPTIVE_FIELD_MAPPING:
            #ind = GuiWidget['editable_configuration']['entries']['label'].index('ScreenDistanceMm')
            #print(GuiWidget['editable_configuration']['entries']['label'])
            '''
            for entries in self.editable_configuration_entries:

                # If any of the entries are empty skip processing
                if not len(entries[0].get()) or not len(entries[1].get()) or not len(entries[2].get()):
                    continue

                command_word = int(entries[1].get())
                if command_word==const.SCREEN_DISTANCE:
                    data_word = entries[2].get()
                    continue
            '''
            try:
                deg_x, deg_y = util.convert_pix_to_deg(x,y, int(globls.arbitrator_display['screen_distance_mm']))
                self.stim_pos_text.set('X (deg): {}\nY (deg): {}'.format(
                    float(round(deg_x,3)), float(round(deg_y,3))))
            except TypeError:
                self.display_warning_error_message("Error, Incorrect Value",
                                           "You need an input for ScreenDistanceMm (Identifier = -4)")
                return


        data = '{} {}/{} {}/{} {}'.format(const.TARGET_X, x_mm, const.TARGET_Y, y_mm,
                                          const.TARGET_Z, globls.depth)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data)

        # TO DO: What needs to be done for dragging case, should it be drawn immideately or
        # when matlab responds back
        if self.canvas_mouse_checkbutton.get() == MouseClick.DRAGGING:
            diff_xy_pos = np.subtract([x_scaled, y_scaled], self.last_mouse_target_point).tolist()
            if not self.mouse_click_target_points:
                # Draw the target current target on canvas
                self.mouse_click_target_points = self.draw_point(x_scaled, y_scaled, win_size=8)
            else:
                self.move_point(self.mouse_click_target_points,
                                diff_xy_pos[0], diff_xy_pos[1])
            self.last_mouse_target_point = [x_scaled, y_scaled]

    # On zoom enlarge the size
    def display_zoom(self, zoom_out):
        # :param increase: should it be increased or decreased
        increase_factor = 0.1
        if zoom_out:
            self.zoom_by += increase_factor
        else:
            if self.zoom_by <= 0.1:
                self.zoom_by = 0.1
                return
            self.zoom_by -= increase_factor

    # Draw a point
    def draw_point(self, x, y, color='black', win_size=3):
        '''
        :param x: X position
        :param y: y position
        :param color: color
        :param win_size: size
        :return:
        '''
        scaled_win_size = int(win_size / globls.arbitrator_display['x_scale_factor'] * self.zoom_by)
        x_scaled = x / globls.arbitrator_display['x_scale_factor'] * self.zoom_by
        y_scaled = y / globls.arbitrator_display['y_scale_factor'] * self.zoom_by
        target = self.eye_canvas_obj.create_oval(x_scaled - scaled_win_size- globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                y_scaled - scaled_win_size- globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1),
                                                x_scaled + scaled_win_size- globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                y_scaled + scaled_win_size- globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1),
                                                outline=color, fill=color
                                                )
        return target

    def move_point(self, widget, x, y):
        '''
        Function to move a  point on screen
        :param x:
        :param y:
        '''
        x_scaled = x / globls.arbitrator_display['x_scale_factor']
        y_scaled = y / globls.arbitrator_display['y_scale_factor']
        self.eye_canvas_obj.move(widget, x_scaled, y_scaled)

    def clear_window_on_canvas(self, widget):
        # Common function to clear the widgets on canvas
        self.eye_canvas_obj.delete(widget)
        widget = None

    # Draw a window around a point
    def draw_window(self, x, y, color='black', win_size=2):
        '''
        :param x: position x
        :param y: position y
        :param color: color
        :param win_size: window size
        :return: the widget id
        '''
        scaled_win_size = int(win_size / globls.arbitrator_display['x_scale_factor']) * self.zoom_by
        x_scaled = x / globls.arbitrator_display['x_scale_factor'] * self.zoom_by
        y_scaled = y / globls.arbitrator_display['y_scale_factor'] * self.zoom_by
        circle = self.eye_canvas_obj.create_oval(x_scaled - scaled_win_size - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                y_scaled - scaled_win_size - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by -1),
                                                x_scaled + scaled_win_size - globls.arbitrator_window_width/globls.arbitrator_display['x_scale_factor']/2 * (self.zoom_by - 1),
                                                y_scaled + scaled_win_size - globls.arbitrator_window_height/globls.arbitrator_display['y_scale_factor']/2 * (self.zoom_by - 1),
                                                outline=color, dash=(3, 5)
                                                )
        return circle

    ''' Draw editable configuration widgets '''
    def draw_editable_configuration_window(self):
        '''
        Draw the widgets for accepting configuration in runtime
        '''
        configuration_widget = GuiWidget['editable_configuration']
        configure_frame = WidgetApi.draw_frame(globls.gui_root, configuration_widget['main_frame'])
        WidgetApi.draw_label(globls.gui_root, configuration_widget['configuration_label'])

        # Draw lables
        for label in configuration_widget['labels']:
            resp = WidgetApi.draw_label(configure_frame, label)
            resp.grid(row=label['row'], column=label['column'], padx=label['padx'], pady=label['pady'])

        # Draw inner frame to place entry boxes and scrollbar
        interior = WidgetApi.draw_scrollable_frame(configure_frame, configuration_widget['scrollable_frame'])

        for i in range(globls.constant['number_of_task_config_entries']):
            entry_dict = configuration_widget['entries']

            label_dict = entry_dict['label']
            ent1 = WidgetApi.draw_entry(interior, label_dict)
            ent1.grid(row =i, column=label_dict['column'],
                      padx=label_dict['padx'], pady=label_dict['pady'])

            command_word_dict = entry_dict['command_word']
            ent2 = WidgetApi.draw_entry(interior, command_word_dict)
            ent2.grid(row=i, column=command_word_dict['column'],
                      padx=command_word_dict['padx'], pady=command_word_dict['pady'])

            data_word_dict = entry_dict['data_word']
            ent3 = WidgetApi.draw_entry(interior, data_word_dict)
            ent3.grid(row=i, column=data_word_dict['column'],  pady=data_word_dict['pady'])

            self.editable_configuration_entries.append([ent1, ent2, ent3])

        configuration_widget['submit_button']['command'] = self.submit_configuration_data
        WidgetApi.draw_button(configure_frame, configuration_widget['submit_button'])

    def submit_configuration_data(self):
        '''
        Send the condiguration from GUI to 3rd party server
        '''
        try:
            data_to_send = ''
            data_to_send_flag = False
            for entries in self.editable_configuration_entries:

                # If any of the entries are empty skip processing
                if not len(entries[0].get()) or not len(entries[1].get()) or not len(entries[2].get()):
                    continue
                data_to_send_flag = True
                try:
                    command_word = int(entries[1].get())
                    data_word = entries[2].get()

                except ValueError:
                    self.display_warning_error_message("Error, Incorrect Value",
                                           "Entry for {} is incorrect".format(entries[0].get()))
                    return

                data_to_send += '{} {}/'.format(command_word, data_word)

                # If the total length exceeds specified limit just send the partial set
                if len(data_to_send) > (globls.constant['data_size_length'] - 24):
                    util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr,
                                   data_to_send, "Configuration")
                    data_to_send_flag = False
                    data_to_send = ''

            # Any unsent data will be sent here
            if data_to_send_flag:
                util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr,
                               data_to_send, "Configuration")
        except Exception as e:
            log.exception(e)

    def set_editable_configuration(self, configuration):
        '''
        :param configuration: List of configuration like
          [[Label 1, command_word 1, command_type 1],
          [Label 2, command_word 2, command_type 2],
          ....
          ]
          if length of configuration is 0 then it means we are just resetting the entry box
        '''
        try:
            i = 0
            for lst in self.editable_configuration_entries:
                lst[0].delete(0, 'end')
                lst[1].delete(0, 'end')
                lst[2].delete(0, 'end')

                if i < len(configuration):
                    lst[0].insert(0, configuration[i][0])
                    lst[1].insert(0, configuration[i][1])
                    lst[2].insert(0, configuration[i][2])
                i += 1

            # send the data only if the configuration is present else do nothing
            if len(configuration):
                self.submit_configuration_data()

        except Exception as e:
            log.exception(e)

    @staticmethod
    def clear_data(entries):
        for e in entries:
            e[0].delete(0, 'end')
            e[1].delete(0, 'end')
            e[2].delete(0, 'end')

    ''' Config for displaying the configuration '''
    def draw_displayable_configuration_widgets(self):
        '''
        Draw the widets like entry boxes for display and edit the configuration
        :return:
        '''
        configuration_widget = GuiWidget['displayable_configuration']
        configure_frame = WidgetApi.draw_frame(globls.gui_root, configuration_widget['main_frame'])
        WidgetApi.draw_label(globls.gui_root, configuration_widget['displayable_configuration_label'])

        # Draw lables
        for label in configuration_widget['labels']:
            resp = WidgetApi.draw_label(configure_frame, label)
            resp.grid(row=label['row'], column=label['column'], padx=label['padx'], pady=label['pady'])

        interior = WidgetApi.draw_scrollable_frame(configure_frame, configuration_widget['scrollable_frame'])

        for i in range(globls.constant['number_of_task_config_entries']):
            scrollable_widgets = configuration_widget['scrollable_widgets']
            label_entry_dict = scrollable_widgets['label']
            ent1 = WidgetApi.draw_entry(interior, label_entry_dict)
            ent1.grid(row=i, column=label_entry_dict['column'],
                      padx=label_entry_dict['padx'], pady=label_entry_dict['pady'])

            command_word_dict = scrollable_widgets['command_word']
            ent2 = WidgetApi.draw_entry(interior, command_word_dict)
            ent2.grid(row=i, column=command_word_dict['column'],
                      padx=command_word_dict['padx'], pady=command_word_dict['pady'])

            label_dict = scrollable_widgets['data_word']
            label_string = tk.StringVar()
            label_dict['textvariable'] = label_string
            label = WidgetApi.draw_label(interior, label_dict)
            label.grid(row=i, column=label_dict['column'],
                      pady=label_dict['pady'])

            self.displayable_widget_config[ent2] = {'command_label': ent1,
                                                    'command_word': ent2,
                                                   'data_word': label_string}

            ent2.bind('<Return>', self.update_displayable_configuration_dict)
            ent2.bind('<Tab>', self.update_displayable_configuration_dict)
            self.displayable_widget_config[ent2]['data_word'].set(0)

    # On entering the command word on displayable window and pressing enter or tab this function would be
    # called to update the internal data structure to read the configuration from the 3rd party server
    # and update on the UI
    def update_displayable_configuration_dict(self, event=None):

        if self.displayable_widget_config.get(event.widget, None):
            widget_row = self.displayable_widget_config.get(event.widget)
            command_word = event.widget.get()
            if len(command_word):

                if (self.displayable_configuration_dict.get(command_word, None) is not None and
                            self.displayable_configuration_dict[command_word]['command_word'] != event.widget):
                    self.display_warning_error_message("Error, Incorrect Identifier",
                                           "Two variables cannot have same identifier")
                    widget_row['command_label'].delete(0, 'end')
                    widget_row['command_word'].delete(0, 'end')
                    widget_row['data_word'].set(0)
                    return

                self.displayable_configuration_dict[command_word] = {'command_word': event.widget,
                                                                     'data_word_label': widget_row['data_word']}
                widget_row['data_word'].set(0)
            else:
                key = None
                for k, v in self.displayable_configuration_dict.iteritems():
                    if v['command_word'] == event.widget:
                        key = k
                        break
                if key is not None:
                    del self.displayable_configuration_dict[key]

    def update_displayable_configuration(self):
        '''
        This function updates the configuration from the 3rd partyserver
        [
        [command_type 1, command_word 1],
        [command_type 2, command_word 2],
        ....
        ]
        '''
        configuration = copy.copy(globls.displayable_config)
        try:
            for k, v in configuration.iteritems():
                display_config = self.displayable_configuration_dict.get(int(k), None)
                # if the configuratio is defined
                # TO DO check why you need the second check
                if display_config is not None and len(display_config['command_word'].get()):
                    display_config['data_word_label'].set(v)
        except Exception as e:
            log.exception(e)

    def set_displayable_config(self, configuration):
        '''
            This function updates the configuration from the 3rd partyserver
            [
            [label, command_type 1, command_word 1],
            [label, command_type 2, command_word 2],
            ....
            ]
            if length of configuration is 0 then it means we are just resetting the entry box
        '''
        try:
            i = 0
            self.displayable_configuration_dict = {}
            od = collections.OrderedDict(sorted(self.displayable_widget_config.items()))

            for k, v in od.iteritems():
                v['command_label'].delete(0, 'end')
                v['command_word'].delete(0, 'end')
                v['data_word'].set(0)

                # Update only the configuration that is present in the file
                if i < len(configuration):
                    v['command_label'].insert(0, configuration[i][0])
                    v['command_word'].insert(0, configuration[i][1])
                    v['data_word'].set(configuration[i][2])

                    command_word = int(configuration[i][1])

                    # Form the new configuration
                    self.displayable_configuration_dict[command_word] = {'command_word': v['command_word'],
                                                                     'data_word_label': v['data_word']}

                i += 1
        except Exception as e:
            log.exception(e)

    ''' Configuration for loading the subject file '''
    def draw_loadsave_subject(self):
        '''
        draw frame to load and save subject specific configuraiton file
        :return:
        '''
        load_config_widget = GuiWidget['load_subject_config']
        # Frame for loading the configuration file
        file_config_frame = WidgetApi.draw_frame(globls.gui_root, load_config_widget['main_frame'])
        WidgetApi.draw_label(globls.gui_root,
                             load_config_widget['load_subject_config_label'])

        WidgetApi.draw_label(file_config_frame, load_config_widget['load_file_label'])

        self.subject_config_entry = WidgetApi.draw_entry(file_config_frame,
                                                     load_config_widget['load_file_entry'])
        load_config_widget['load_button']['command'] = self.load_from_subject_file
        loadbutton = WidgetApi.draw_button(file_config_frame,
                              load_config_widget['load_button'])
        loadbutton.bind('<Return>', lambda event, key='<space>': loadbutton.event_generate(key))

        load_config_widget['save_button']['command'] = self.save_subject_configuration
        savebutton = WidgetApi.draw_button(file_config_frame, load_config_widget['save_button'])
        savebutton.bind('<Return>', lambda event, key='<space>': savebutton.event_generate(key))



        ''' Configuration for loading subject viewing parameters '''
    def draw_subject_viewing_params(self):
        '''
        draw frame to load and save subject specific configuraiton file
        :return:
        '''
        subj_viewing_widget = GuiWidget['subject_viewing_widget']
        # Frame for loading the configuration file
        subj_viewing_frame = WidgetApi.draw_frame(globls.gui_root, subj_viewing_widget['main_frame'])
        WidgetApi.draw_label(globls.gui_root,
                             subj_viewing_widget['subject_viewing_label'])
        WidgetApi.draw_label(subj_viewing_frame,
                             subj_viewing_widget['screen_parameters_label'])

        # Draw labels
        for label in subj_viewing_widget['subject_viewing_params']['labels']:
            WidgetApi.draw_label(subj_viewing_frame, label)

        # Draw all the entries and collect the entries in a list for reading and processing
        self.subject_viewing_entries = []
        for entry_dict in subj_viewing_widget['subject_viewing_params']['entries']:
            # Read from configuration
            value = globls.arbitrator_display[entry_dict['field']]
            entry_dict['value'] = value
            ent = WidgetApi.draw_entry(subj_viewing_frame, entry_dict)

            self.subject_viewing_entries.append((entry_dict['field'], ent, entry_dict))

    # Write to file. Writing to file depends on what is selected on UI
    # if no file is selected in "Load config from subject" then the values are written to default
    # file else it is written into the subject specific file
    def save_subject_configuration(self):
        '''
        save configuration from subject file
        :return:
        '''
        # globls.update_screen_config(self.subject_viewing_entries)
        subject_name = self.subject_config_entry.get()
        if not len(subject_name):
            self.display_warning_error_message("Error, Invalid Subject Name",
                                   "Please sepecify the subject name")
            return

        # data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.SAVE_SUBJECT)
        # util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
        #                'Save subject')

        globls.save_subject_specifc_config(subject_name, globls.directories['configuration'])

    # Load the data from the subject file
    def load_from_subject_file(self):
        '''
            Load configuration from subject file
        '''
        subject_name = self.subject_config_entry.get()
        subject_file_name = subject_name + '.conf'
        resp, msg = globls.read_config(subject_file_name, globls.directories['configuration'])
        if not resp:
            self.display_warning_error_message("Error Reading File",
                "Please check if the subject file exists")
            return

        data = "{} {}/".format(const.COMMAND_WORD_CONTROL, const.LOAD_SUBJECT)
        util.send_data(globls.arbitrator_sock, globls.arbitrator_sock_addr, data,
                       'Load Subject')

        globls.update_subject_name(subject_name)
        globls.update_subject_spcific_configuration(resp, subject_file_name)
        self.draw_subject_viewing_params()
        globls.update_screen_config(self.subject_viewing_entries)
        self.update_default_eye_configuration()
        self.update_eye_spinbox_and_window()
        globls.update_gui_scale_factor()
        self.update_task_subject_file_loaded(subject_file=True)
        util.send_screen_parameters()

'''
    Information about the GUI main screen widget like location, width and height
'''
GuiWidget = {
    'eye_display': {
        'main_frame': {
            'relx': 0.01, 'rely': 0.01,
            'relheight': .39, 'relwidth': .37},
        'canvas': {
            'relx': 0.0, 'rely': 0.00,
            'relheight': 0.95, 'relwidth': 1},
        'eyepos_text_label': {
            'relx': 0.01, 'rely': .95,
            'relheight': 0.04, 'relwidth': 0.40},
        'mouse_checkbutton': [
            {'text': ' Feedback', 'offvalue': 0, 'onvalue': MouseClick.FEEDBACK,
            'relx': 0.35, 'rely': .95,
            'relheight':  0.045, 'relwidth': 0.17},
            {'text': ' Dragging', 'offvalue': 0, 'onvalue': MouseClick.DRAGGING,
            'relx': 0.55, 'rely': .95,
            'relheight':  0.045, 'relwidth': 0.17},
        ],
        'zoomout_button': {
            'text': '+',
            'relx': 0.97, 'rely': 0.90,
            'relheight': 0.04, 'relwidth': 0.03},
        'zoomin_button': {
            'text': '-',
            'relx': 0.97, 'rely': 0.945,
            'relheight': 0.04, 'relwidth': 0.03},
    },
    'scrolled_text': {
        'main_frame': {
            'relx': 0.50, 'rely': 0.78,
            'relheight': 0.21, 'relwidth': 0.46},
        'scrolled_text_label': {
            'text': 'Data Log',
            'relx': 0.50, 'rely': 0.77,
            'relheight': 0.02, 'relwidth': 0.04},
        'text_frame': {
            'relx': 0.0, 'rely': 0.05,
            'relheight': 1.0, 'relwidth': 1.0, 'width': 102}
    },

    'eye_window_config': {
        'main_frame': {
            'relx': 0.01, 'rely': 0.41,
            'relheight': 0.23, 'relwidth': 0.37, 'width': 595},
        'eye_window_label': {
            'text': 'Eye Control Configuration',
            'relx': 0.01, 'rely': 0.40,
            'relheight': 0.02, 'relwidth': 0.09},
        'config_labels': [
            # {'text': 'Window Size',
            #  'relx': 0.75, 'rely': 0.10,
            #  'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Eye',
             'relx': 0.01, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Horizontal',
             'relx': 0.18, 'rely': 0.10,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Vertical',
             'relx': 0.42, 'rely': 0.10,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Offset',
             'relx': 0.13, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Gain',
             'relx': 0.26, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Offset',
             'relx': 0.37, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Gain',
             'relx': 0.49, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Pupil Size',
             'relx': 0.60, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            # {'text': 'Version(deg)',
            #  'relx': 0.72, 'rely': 0.38,
            #  'relheight': 0.10, 'relwidth': 0.18},
            # {'text': 'Vergence(deg)',
            #  'relx': 0.72, 'rely': 0.55,
            #  'relheight': 0.10, 'relwidth': 0.18},
        ],
        'left_checkbutton': {
            'text': ' Left',
            'relx': 0.0, 'rely': 0.36,
            'relheight': 0.1, 'relwidth': 0.12},
        'right_checkbutton': {
            'text': ' Right',
            'relx': 0.0, 'rely': 0.56,
            'relheight': 0.1, 'relwidth': 0.12},
        # 'vergence_checkbutton': [
        #     {'text': ' Vergence HV', 'offvalue': 0, 'onvalue': Vergence.HORTIZONTAL_VERTICAL,
        #      'relx': 0.0, 'rely': 0.76,
        #      'relheight': 0.1, 'relwidth': 0.20},
        #     {'text': ' Vergence H', 'onvalue': Vergence.HORTIZONTAL, 'offvalue': 0,
        #      'relx': 0.25, 'rely': 0.76,
        #      'relheight': 0.1, 'relwidth': 0.20}
        # ],
        'h_left_offset': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.13, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'h_left_gain': {
            'from_val': -15000, 'to_val': 15000, 'increment': 0.1, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.25, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'h_right_offset': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.RIGHT_EYE_COLOR,
            'relx': 0.13, 'rely': 0.54,
            'relheight': 0.14, 'relwidth': 0.09},
        'h_right_gain': {
            'from_val': -15000, 'to_val': 15000, 'increment': 0.1, 'color': const.RIGHT_EYE_COLOR,
            'relx': 0.25, 'rely': 0.54,
            'relheight': 0.14, 'relwidth': 0.09},
        'v_left_offset': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.37, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'v_left_gain': {
            'from_val': -15000, 'to_val': 15000, 'increment': 0.1, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.49, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'v_right_offset': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.RIGHT_EYE_COLOR,
            'relx': 0.37, 'rely': 0.54,
            'relheight': 0.14, 'relwidth': 0.09},
        'v_right_gain': {
            'from_val': -15000, 'to_val': 15000, 'increment': 0.1, 'color': const.RIGHT_EYE_COLOR,
            'relx': 0.49, 'rely': 0.54,
            'relheight': 0.14, 'relwidth': 0.09},
        'left_pupil_size': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.61, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'right_pupil_size': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.RIGHT_EYE_COLOR,
            'relx': 0.61, 'rely': 0.54,
            'relheight': 0.14, 'relwidth': 0.09},
        # 'version_entry': {
        #     'relx': 0.90, 'rely': 0.37,
        #     'relheight': 0.1, 'relwidth': 0.08,
        #     'value': globls.configuration['version_window_size']},
        # 'vergence_entry': {
        #     'relx': 0.90, 'rely': 0.54,
        #     'relheight': 0.1, 'relwidth': 0.08,
        #     'value': globls.configuration['vergence_size']},
    },
    'tracker_window_config': {
        'main_frame': {
            'relx': 0.01, 'rely': 0.41,
            'relheight': 0.23, 'relwidth': 0.37, 'width': 595},
        'tracker_window_label': {
            'text': 'Control Configuration',
            'relx': 0.01, 'rely': 0.40,
            'relheight': 0.02, 'relwidth': 0.09},
        'config_labels': [
            {'text': 'Horizontal',
             'relx': 0.18, 'rely': 0.10,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Vertical',
             'relx': 0.42, 'rely': 0.10,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Offset',
             'relx': 0.13, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Gain',
             'relx': 0.26, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Offset',
             'relx': 0.37, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
            {'text': 'Gain',
             'relx': 0.49, 'rely': 0.21,
             'relheight': 0.10, 'relwidth': 0.13},
        ],
        'h_offset': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.13, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'h_gain': {
            'from_val': -15000, 'to_val': 15000, 'increment': 0.1, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.25, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'v_offset': {
            'from_val': -15000, 'to_val': 15000, 'increment': 5, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.37, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09},
        'v_gain': {
            'from_val': -15000, 'to_val': 15000, 'increment': 0.1, 'color': const.LEFT_EYE_COLOR,
            'relx': 0.49, 'rely': 0.34,
            'relheight': 0.14, 'relwidth': 0.09}
    },
    'task_controls': {
        'main_frame': {
            'relx': 0.39, 'rely': 0.01,
            'relheight': 0.23, 'relwidth': 0.10},
        'task_control_label': {
            'text': 'Task Control',
            'relx': 0.39, 'rely': 0.01,
            'relheight': 0.02, 'relwidth': 0.06},
        'task_file_label': {
            'text': 'File',
            'relx': 0.02, 'rely': 0.05,
            'relheight': 0.22, 'relwidth': 0.20},
        'task_file_entry': {
            'relx': 0.27, 'rely': 0.10,
            'relheight': 0.1, 'relwidth': 0.64},
        'task_file_load': {
            'text': 'Load', 'anchor': tk.N,
            'relx': 0.08, 'rely': 0.29,
            'relheight': 0.115, 'relwidth': 0.35},
        'task_file_save': {
            'text': 'Save', 'anchor': tk.N,
            'relx': 0.47, 'rely': 0.29,
            'relheight': 0.115, 'relwidth': 0.35},
        'start_button': {
            'text': 'Start', 'state': tk.DISABLED,
            'relx': 0.08, 'rely': 0.55,
            'relheight': 0.115, 'relwidth': 0.35},
        'pause_button': {
            'text': 'Pause', 'state': tk.DISABLED,
            'relx': 0.47, 'rely': 0.55,
            'relheight': 0.115, 'relwidth': 0.35},
        'stop_button': {
            'text': 'Stop', 'state': tk.DISABLED,
            'relx': 0.08, 'rely': 0.75,
            'relheight': 0.115, 'relwidth': 0.35},
        'exit_button': {
            'text': 'Exit',
            'relx': 0.47, 'rely': 0.75,
            'relheight': 0.115, 'relwidth': 0.35},
    },
    'eye_calibration': {
        'main_frame': {
            'relx': 0.33, 'rely': 0.41,
            'relheight': 0.23, 'relwidth': 0.16, 'width': 225},
        'calibration_checkbutton': {
            'text': ' Eye Calibration', 'onvalue': Task.CALIBRATION, 'offvalue': 0,
            'relx': 0.009, 'rely': 0.02,
            'relheight': 0.1, 'relwidth': 0.50},
        'manual_calibration_checkbutton': {
            'text': ' Manual', 'onvalue': Calibration.MANUAL, 'offvalue': 0, 'state': tk.DISABLED,
            'relx': 0.08, 'rely': 0.12,
            'relheight': 0.1, 'relwidth': 0.50},
        'manual_radiobutton': [
            {'text': ' NW', 'value': CalibrationListIndex.NORTH_WEST,
                'relx': 0.14, 'rely': 0.25,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' N', 'value': CalibrationListIndex.NORTH,
                'relx': 0.34, 'rely': 0.25,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' NE', 'value': CalibrationListIndex.NORTH_EAST,
                'relx': 0.54, 'rely': 0.25,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' W', 'value': CalibrationListIndex.WEST,
                'relx': 0.14, 'rely': 0.32,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' C', 'value': CalibrationListIndex.CENTER,
                'relx': 0.34, 'rely': 0.32,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' E', 'value': CalibrationListIndex.EAST,
                'relx': 0.54, 'rely': 0.32,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' SW', 'value': CalibrationListIndex.SOUTH_WEST,
                'relx': 0.14, 'rely': 0.39,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' S', 'value': CalibrationListIndex.SOUTH,
                'relx': 0.34, 'rely': 0.39,
                'relheight': 0.08, 'relwidth': 0.24},
            {'text': ' SE', 'value': CalibrationListIndex.SOUTH_EAST,
                'relx': 0.54, 'rely': 0.39,
                'relheight': 0.08, 'relwidth': 0.24},
        ],
        #
        # 'auto_calibration_checkbutton': {
        #     'text': ' Automatic', 'onvalue': Calibration.AUTO, 'offvalue': 0, 'state': tk.DISABLED,
        #     'relx': 0.02, 'rely': 0.34,
        #     'relheight': 0.04, 'relwidth': 0.30},
        # 'labels': [
        #     {'text': 'Min',
        #      'relx': 0.33, 'rely': 0.385,
        #      'relheight': 0.05, 'relwidth': 0.30,
        #      'justify': tk.LEFT},
        #     {'text': 'Max',
        #      'relx': 0.53, 'rely': 0.385,
        #      'relheight': 0.05, 'relwidth': 0.30,
        #      'justify': tk.LEFT},
        #     {'text': 'Step Size',
        #      'relx': 0.73, 'rely': 0.385,
        #      'relheight': 0.05, 'relwidth': 0.30,
        #      'justify': tk.LEFT},
        #     {'text': 'Horizontal (deg)',
        #      'relx': 0.02, 'rely': 0.475,
        #      'relheight': 0.05, 'relwidth': 0.30,
        #      'justify': tk.LEFT},
        #     {'text': 'Vertical (deg)',
        #      'relx': 0.02, 'rely': 0.575,
        #      'relheight': 0.05, 'relwidth': 0.30,
        #      'justify': tk.LEFT},
        #     {'text': 'Depth (mm)',
        #      'relx': 0.02, 'rely': 0.675,
        #      'relheight': 0.05, 'relwidth': 0.30,
        #      'justify': tk.LEFT},
        # ],
        #
        'entries': [
            {'field': 'target_pos_horizantal_min',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.31, 'rely': 0.475,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_horizantal_max',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.51, 'rely': 0.475,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_horizantal_step',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.72, 'rely': 0.475,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_vertical_min',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.31, 'rely': 0.575,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_vertical_max',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.51, 'rely': 0.575,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_vertical_step',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.72, 'rely': 0.575,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_depth_min',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.31, 'rely': 0.675,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_depth_max',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.51, 'rely': 0.675,
             'relwidth': 0.13, 'relheight': 0.05},
            {'field': 'target_pos_depth_step',
             'type': 'float', 'min': -2000, 'max': 2000,
             'relx': 0.72, 'rely': 0.675,
             'relwidth': 0.13, 'relheight': 0.05},
        ],
        'submit_button': {
            'text': 'Submit', 'state': tk.DISABLED,
            'relx': 0.61, 'rely': 0.41,
            'relheight': 0.07, 'relwidth': 0.20},
        'accept_button': {
            'text': 'Accept', 'state': tk.DISABLED,
            'relx': 0.14, 'rely': 0.58,
            'relheight': 0.12, 'relwidth': 0.30},
        'cancel_button': {
            'text': 'Cancel', 'state': tk.DISABLED,
            'relx': 0.45, 'rely': 0.58,
            'relheight': 0.12, 'relwidth': 0.30},
        'calibrate_button': {
            'text': 'Calibrate', 'state': tk.DISABLED,
            'relx': 0.14, 'rely': 0.70,
            'relheight': 0.12, 'relwidth': 0.30},
        'clear_button': {
            'text': 'Clear', 'state': tk.DISABLED,
            'relx': 0.45, 'rely': 0.70,
            'relheight': 0.12, 'relwidth': 0.30},
    },
    'custom_buttons': {
        'main_frame': {
            'relx': 0.01, 'rely': 0.65,
            'relheight': 0.34, 'relwidth': 0.48, 'width': 225},
        'buttons': [
            {'text': 'Start Save', 'state': tk.NORMAL,
                'relx': 0.1, 'rely': 0.2,
                'relheight': 0.07, 'relwidth': 0.20},
            {'text': 'Open Gate', 'state': tk.NORMAL,
                'relx': 0.4, 'rely': 0.2,
                'relheight': 0.07, 'relwidth': 0.20},
            {'text': 'E-Shock', 'state': tk.NORMAL,
                'relx': 0.7, 'rely': 0.2,
                'relheight': 0.07, 'relwidth': 0.20},
            {'text': 'Button 4', 'state': tk.NORMAL,
                'relx': 0.1, 'rely': 0.6,
                'relheight': 0.07, 'relwidth': 0.20},
            {'text': 'Button 5', 'state': tk.NORMAL,
                'relx': 0.4, 'rely': 0.6,
                'relheight': 0.07, 'relwidth': 0.20},
            {'text': 'Button 6', 'state': tk.NORMAL,
                'relx': 0.7, 'rely': 0.6,
                'relheight': 0.07, 'relwidth': 0.20},
            ]
    },
    'receptive_field_mapping': {
        'main_frame': {
            'relx': 0.01, 'rely': 0.65,
            'relheight': 0.34, 'relwidth': 0.48, 'width': 225},
        'receptive_field_checkbutton': {
            'text': ' Receptive Field Mapping', 'onvalue': Task.RECEPTIVE_FIELD_MAPPING, 'offvalue': 0,
            'relx': 0.01, 'rely': 0.64,
            'relheight': 0.03, 'relwidth': 0.10},
        'grating_checkbutton': {
            'text': ' Grating', 'onvalue': FieldMapping.GRATING, 'offvalue': 0, 'state': tk.DISABLED, 'cmd': const.RECEPTIVE_STIM,
            'relx': 0.02, 'rely': 0.05,
            'relheight': 0.06, 'relwidth': 0.20},
        'dots_checkbutton': {
            'text': ' Dots', 'onvalue': FieldMapping.DOTS, 'offvalue': 0, 'state': tk.DISABLED, 'cmd': const.RECEPTIVE_STIM,
            'relx': 0.5, 'rely': 0.05,
            'relheight': 0.06, 'relwidth': 0.35},
        'bar_checkbutton': {
            'text': ' Bar', 'onvalue': FieldMapping.BAR, 'offvalue': 0, 'state': tk.DISABLED, 'cmd': const.RECEPTIVE_STIM,
            'relx': 0.26, 'rely': 0.05,
            'relheight': 0.06, 'relwidth': 0.15},
        'labels': [
            # {'text': 'Direction (deg)',
            #  'relx': 0.5, 'rely': 0.15,
            #  'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Speed (deg/sec)',
             'relx': 0.5, 'rely': 0.15,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Density (dots/deg' u'\u00B2'')',
             'relx': 0.5, 'rely': 0.21,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Dot Size (deg)',
             'relx': 0.5, 'rely': 0.27,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Orientation (deg)',
             'relx': 0.02, 'rely': 0.52,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Spatial Freq.',
             'relx': 0.02, 'rely': 0.15,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Temporal Freq.',
             'relx': 0.02, 'rely': 0.21,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Contrast',
             'relx': 0.02, 'rely': 0.64,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Bar Height (deg)',
             'relx': 0.26, 'rely': 0.15,
             'relheight': 0.06, 'relwidth': 0.15},
            {'text': 'Bar Width (deg)',
             'relx': 0.26, 'rely': 0.21,
             'relheight': 0.06, 'relwidth': 0.15},
            {'text': 'Bar Color (RGB)',
             'relx': 0.26, 'rely': 0.27,
             'relheight': 0.06, 'relwidth': 0.15},
            {'text': 'Diameter (deg)',
             'relx': 0.02, 'rely': 0.58,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Depth (mm)',
             'relx': 0.02, 'rely': 0.7,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Pulse Duration (sec)',
             'relx': 0.02, 'rely': 0.76,
             'relheight': 0.06, 'relwidth': 0.30},
            {'text': 'Inter-Pulse Interval (sec)',
             'relx': 0.02, 'rely': 0.82,
             'relheight': 0.06, 'relwidth': 0.35},
            {'text': 'Fixation Point',
             'relx': 0.54, 'rely': 0.46,
             'relheight': 0.06, 'relwidth': 0.35},
            {'text': 'X (deg)',
             'relx': 0.54, 'rely': 0.51,
             'relheight': 0.06, 'relwidth': 0.25},
            {'text': 'Y (deg)',
             'relx': 0.54, 'rely': 0.57,
             'relheight': 0.06, 'relwidth': 0.25},
            {'text': 'Z (mm)',
             'relx': 0.54, 'rely': 0.63,
             'relheight': 0.06, 'relwidth': 0.25},
            {'text': 'General Stimulus Properties',
             'relx': 0.05, 'rely': 0.46,
             'relheight': 0.06, 'relwidth': 0.25},
            {'text': 'Stimulus Position',
             'relx': 0.33, 'rely': 0.46,
             'relheight': 0.06, 'relwidth': 0.15}
            ],
        'stimpos_text_label': {
            'relx': 0.35, 'rely': 0.52,
            'relheight': 0.1, 'relwidth': 0.25},
        'entries': [
             {'field': 'receptive_field_map_size',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.2, 'rely': 0.58,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.FIELD_SIZE},
            {'field': 'dot_density',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.65, 'rely': 0.21,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.DOT_DENISTY},
            {'field': 'dot_size',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.65, 'rely': 0.27,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.DOT_SIZE},
            # {'field': 'dot_direction',
            #  'type': 'float', 'min': 0, 'max': 360,
            #  'relx': 0.65, 'rely': 0.15,
            #  'relwidth': 0.07, 'relheight': 0.05,
            #  'command': const.DOT_DIRECTION},
            {'field': 'dot_speed',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.65, 'rely': 0.15,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.DOT_SPEED},
            {'field': 'grating_spatial_freq',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.14, 'rely': 0.15,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.SPAT_FREQ},
            {'field': 'grating_temporal_freq',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.14, 'rely': 0.21,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.TEMP_FREQ},
            {'field': 'orientation',
             'type': 'float', 'min': 0, 'max': 360,
             'relx': 0.2, 'rely': 0.52,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.ORIENTATION},
            {'field': 'grating_contrast',
             'type': 'float', 'min': 0, 'max': 100,
             'relx': 0.2, 'rely': 0.64,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.GRATING_CONTRAST},
            {'field': 'bar_height',
             'type': 'float', 'min': 0, 'max': 100,
             'relx': 0.39, 'rely': 0.15,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.BAR_HEIGHT},
            {'field': 'bar_width',
             'type': 'float', 'min': 0, 'max': 100,
             'relx': 0.39, 'rely': 0.21,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.BAR_WIDTH},
            {'field': 'bar_color_r',
             'type': 'float', 'min': 0, 'max': 1,
             'relx': 0.39, 'rely': 0.27,
             'relwidth': 0.03, 'relheight': 0.05,
             'command': const.BAR_COLOR_R},
            {'field': 'bar_color_g',
             'type': 'float', 'min': 0, 'max': 1,
             'relx': 0.42, 'rely': 0.27,
             'relwidth': 0.03, 'relheight': 0.05,
             'command': const.BAR_COLOR_G},
            {'field': 'bar_color_b',
             'type': 'float', 'min': 0, 'max': 1,
             'relx': 0.45, 'rely': 0.27,
             'relwidth': 0.03, 'relheight': 0.05,
             'command': const.BAR_COLOR_B},
            {'field': 'receptive_field_map_depth',
             'type': 'int', 'min': -1000, 'max': 1000,
             'relx': 0.2, 'rely': 0.70,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.FIELD_DEPTH},
            {'field': 'pulse_dura',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.2, 'rely': 0.76,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.PULSE_DURA},
            {'field': 'pulse_iti',
             'type': 'float', 'min': 0, 'max': 1000,
             'relx': 0.2, 'rely': 0.82,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.PULSE_ITI},
            {'field': 'xFix',
             'type': 'float', 'min': -1000, 'max': 1000,
             'relx': 0.60, 'rely': 0.51,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.XFIX},
            {'field': 'yFix',
             'type': 'float', 'min': -1000, 'max': 1000,
             'relx': 0.60, 'rely': 0.57,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.YFIX},
            {'field': 'zFix',
             'type': 'float', 'min': -1000, 'max': 1000,
             'relx': 0.60, 'rely': 0.63,
             'relwidth': 0.07, 'relheight': 0.05,
             'command': const.ZFIX}
        ],
        "submit_button": {
            'text': 'Submit', 'state': tk.DISABLED,
            'relx': 0.45, 'rely': 0.79,
            'relheight': 0.07, 'relwidth': 0.20},
     },
    'load_subject_config': {
        'main_frame': {
            'relx': 0.50, 'rely': 0.01,
            'relheight': 0.05, 'relwidth': 0.46, 'width': 835},
        'load_subject_config_label': {
            'text': 'Load From Subject File',
            'relx': 0.50, 'rely': 0.00,
            'relheight': 0.02, 'relwidth': 0.14},
        'load_file_label': {
            'text': 'Subject Name',
            'relx': 0.03, 'rely': 0.28,
            'relheight': 0.24, 'relwidth': 0.20},
        'load_file_entry': {
            'text': 'Load',
            'relx': 0.18, 'rely': 0.2,
            'relheight': 0.40, 'relwidth': 0.18},
        'load_button': {
            'text': 'Load',
            'relx': 0.38, 'rely': 0.24,
            'relheight': 0.46, 'relwidth': 0.10},
        'save_button': {
            'text': 'Save',
            'relx': 0.50, 'rely': 0.24,
            'relheight': 0.46, 'relwidth': 0.10},
    },
    'subject_viewing_widget': {
        'main_frame': {
            'relx': 0.39, 'rely': 0.23,
            'relheight': 0.17, 'relwidth': 0.10, 'width': 835},
        'subject_viewing_label': {
            'text': 'Configuration',
            'relx': 0.39, 'rely': 0.23,
            'relheight': 0.014, 'relwidth': 0.07},
        'screen_parameters_label': {
            'text': 'Screen Parameters',
            'relx': 0.01, 'rely': 0.38,
            'relheight': 0.25, 'relwidth': 0.9},
        'subject_viewing_params': {
            'labels': [
                {'text': 'Subject Parameters',
                'relx': 0.01, 'rely': 0.095,
                'relheight': 0.15, 'relwidth': 0.9},
                {'text': 'IOD (mm)',
                'relx': 0.01, 'rely': 0.21,
                'relheight': 0.13, 'relwidth': 0.7},
                {'text': 'Distance (mm)',
                 'relx': 0.01, 'rely': 0.55,
                'relheight': 0.15, 'relwidth': 0.7},
                {'text': 'Height (mm)',
                 'relx': 0.01, 'rely': 0.7,
                'relheight': 0.15, 'relwidth': 0.7},
                {'text': 'Width (mm)',
                 'relx': 0.01, 'rely': 0.85,
                'relheight': 0.15, 'relwidth': 0.7},
                ],
            'entries': [
                {'field': 'iod_mm',
                'relx': 0.6, 'rely': 0.21,
                'relheight': 0.12, 'relwidth': 0.3,
                'command': const.SCREEN_IOD},
                {'field': 'screen_distance_mm',
                'relx': 0.6, 'rely': 0.55,
                'relheight': 0.12, 'relwidth': 0.3,
                'command': const.SCREEN_DISTANCE},
                {'field': 'screen_height_mm',
                'relx': 0.6, 'rely': 0.7,
                'relheight': 0.12, 'relwidth': 0.3,
                'command': const.SCREEN_HEIGHT},
                {'field': 'screen_width_mm',
                'relx': 0.6, 'rely': 0.85,
                'relheight': 0.12, 'relwidth': 0.3,
                'command': const.SCREEN_WIDTH}
            ]
        },
    },
    'editable_configuration': {
        'main_frame': {
            'relx': 0.50, 'rely': 0.07,
            'relheight': 0.38, 'relwidth': 0.46, 'width': 835},
        'configuration_label': {
            'text': 'Sending Panel',
            'relx': 0.50, 'rely': 0.06,
            'relheight': 0.02, 'relwidth': 0.07},
        'scrollable_frame': {
            'relx': 0.01, 'rely': 0.07, 'relheight': .844, 'relwidth': 0.90},
        'labels': [
            {'text': 'Variable Name', 'row': 1, 'column': 1, 'padx': 40, 'pady': 7},
            {'text': 'Identifier', 'row': 1, 'column': 2, 'padx': 105, 'pady': 7},
            {'text': 'Value', 'row': 1, 'column': 3, 'padx': 70, 'pady': 7},
        ],
        "entries": {
            'label': {
                'column': 1, 'padx': 3, 'pady': 5},
            'command_word': {
                'column': 2, 'padx': 80, 'pady': 5},
            'data_word': {
                'column': 3, 'pady': 5},
        },
        'submit_button': {
            'text': 'Submit',
            'relx': 0.80, 'rely': 0.92,
            'relheight': 0.07, 'relwidth': 0.15},
        'clear_button': {
            'text': 'Clear',
            'relx': 0.12, 'rely': 0.92,
            'relheight': 0.07, 'relwidth': 0.15},
    },
    'displayable_configuration': {
        'main_frame': {
            'relx': 0.50, 'rely': 0.46,
            'relheight': 0.31, 'relwidth': 0.46, 'width': 835},
        'displayable_configuration_label': {
            'text': 'Receiving Panel',
            'relx': 0.50, 'rely': 0.45,
            'relheight': 0.02, 'relwidth': 0.07},
        'scrollable_frame': {
            'relx': 0.01, 'rely': 0.11, 'relheight': .86, 'relwidth': 0.90},
        'labels': [
            {'text': 'Variable Name', 'row': 1, 'column': 1, 'padx': 40, 'pady': 15},
            {'text': 'Identifier', 'row': 1, 'column': 2, 'padx': 105, 'pady': 15},
            {'text': 'Value', 'row': 1, 'column': 3, 'padx': 35, 'pady': 15},
        ],
        "scrollable_widgets": {
            'label': {
                'column': 1, 'padx': 3, 'pady': 5,
                'relx': 0.48, 'rely': 0.03,
                'relwidth': 0.13, 'relheight': 0.04},
            'command_word': {
                'column': 2, 'padx': 80, 'pady': 5,
                'relx': 0.48, 'rely': 0.03,
                'relwidth': 0.13, 'relheight': 0.04},
            'data_word': {
                'column': 3, 'pady': 5, 'width': 4},
        },
    },
}
#
