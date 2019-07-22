'''
Eye recording method
Choose what eye recording method to use.
If eye coil: choose channels and the associated eye to channel data
'''
import Tkinter as tk
import utility as util
from widget_api import WidgetApi
from constants import ConfigLabels, EyeCoilChannelId
from global_parameters import Globals as globls


class EyeRecordFrame:
    # Eye movement method. Select the method, eye coil, and eye position
    # frame position information
    SELCTION_RELX = 0.01
    SELCTION_RELY = 0.02
    SELCTION_HEIGHT = 65

    COIL_CHANNEL_RELX = 0.01
    COIL_CHANNEL_RELY = 0.170
    COIL_CHANNEL_HEIGHT = 200

    EYECOIL_EYEPOS_RELX = 0.01
    EYECOIL_EYEPOS_RELY = 0.558
    EYECOIL_EYEPOS_HEIGHT = 200

    WIDTH = 600
    WINDOW_WIDTH = WIDTH + 10
    WINDOW_HEIGHT = (SELCTION_HEIGHT + COIL_CHANNEL_HEIGHT +
                     EYECOIL_EYEPOS_HEIGHT + 90)

class EyeRecordingMethods:
    EYE_LINK = 0
    EYE_COIL = 1
    NONE = 2


class EyeXYZIndex:
    LEFT_X = 0
    LEFT_Y = 1
    LEFT_Z = 2
    RIGHT_X = 3
    RIGHT_Y = 4
    RIGHT_Z = 5
    TWAIN_XYZ_INDEX = 6


class EyeRecord:

    def __init__(self):
        # Generate an error window with an okay button
        self.dialog1 = tk.Toplevel(globls.gui_root)
        #self.dialog1.geometry("200x200")
        self.dialog1.geometry("{}x{}+750+450".format(
            400,
            100
        ))
        self.dialog1.wm_title("Warning, Eye Recording Method Selection")
        self.recording_warning = tk.Label(self.dialog1,text="Please select eye recording method to be used.",font="bold")
        self.recording_warning.pack(pady=5)
        self.buttonOK = tk.Button(self.dialog1,text="OK",command=self.dialog1.destroy,padx = 30)
        self.buttonOK.pack(pady=10)
        self.dialog1.attributes("-topmost",True)
        self.buttonOK.focus_set()
        self.buttonOK.bind('<Return>', lambda event, key='<space>': widget.event_generate(key))
        self.dialog1.protocol("WM_DELETE_WINDOW", self.dialog1.destroy)

        # New window for capturing the eye window (parent window for new window)
        self.eye_recording_win = tk.Toplevel(globls.gui_root)


        # self.eye_recording_win.geometry("{}*{}+650+189".format(
        #     EyeRecordFrame.WINDOW_WIDTH,
        #     EyeRecordFrame.WINDOW_HEIGHT
        # ))
        self.eye_recording_win.geometry("{}x{}+650+189".format(
            EyeRecordFrame.WINDOW_WIDTH,
            EyeRecordFrame.WINDOW_HEIGHT
        ))

        self.eye_recording_win.wm_title("Eye Method Selection")

        # Recording method (eye coil or eyelink)
        self.eye_recording_method = tk.IntVar()
        # Draw dropdown box or option menu
        self.eye_pos_option_menu_object = []
        self.eye_pos_option_menu_list = []
        for i in range(EyeXYZIndex.TWAIN_XYZ_INDEX):
            self.eye_pos_option_menu_list.append(tk.StringVar())

        # Channel list and object
        self.eye_coil_channel = []  # To get the eye channel value 0 or 1
        self.eye_coil_channel_obj = []  # To get the eye coil check button object
        for i in range(EyeCoilChannelId.C16 + 1):
            self.eye_coil_channel.append(tk.IntVar())

        self.eye_recording_win.protocol("WM_DELETE_WINDOW", self.save_eye_reording_information)

        # eye movement capture method selection
        self.draw_eye_recording_method_selection()

        # Frame for displaying eye coil channel
        self.draw_eye_coil_channel(True)

        # Draw dropdown box
        self.draw_eye_pos_selection(True)
        EyeRecordWidget['ok_button']['command'] = self.save_eye_reording_information
        widget = WidgetApi.draw_button(self.eye_recording_win, EyeRecordWidget['ok_button'])
        widget.focus_set()
        widget.bind('<Return>', lambda event, key='<space>': widget.event_generate(key))


    def save_eye_reording_information(self):
        '''
        Save the selected information
        :return:
        '''
        # Store the channels used for x, y, and z
        if int(self.eye_recording_method.get()) == 1:
            eye_pos = self.get_eye_positions_channel()

            # Store the channels list
            channel_list_selected = []
            for i in range(EyeCoilChannelId.C16 + 1):
                if self.eye_coil_channel[i].get():
                    channel_list_selected.append(i)
            eye_coil_channels = util.convert_bit_to_int(channel_list_selected)
            globls.update_eye_recording_method_parameters(eye_coil_channels=eye_coil_channels, eye_pos=eye_pos)
        self.eye_recording_win.destroy()

    def draw_eye_recording_method_selection(self):
        '''
        Draw frame and widgets for selecting the method for eye recording
        :return:
        '''
        recording_method_select_widget = EyeRecordWidget['recording_method_selection']
        eye_capture_method_frame = WidgetApi.draw_frame(self.eye_recording_win,
                                                        recording_method_select_widget['main_frame'])
        WidgetApi.draw_label(self.eye_recording_win, recording_method_select_widget['method_selection_label'])

        for rb_wiget in recording_method_select_widget['radiobuttons']:
            rb_wiget['variable'] = self.eye_recording_method
            rb_wiget['command'] = self.process_eye_capture_method_selection_callback
            WidgetApi.draw_radio_button(eye_capture_method_frame, rb_wiget)

        # Get the default or config stored in file
        status = globls.eye_recording_method
        self.eye_recording_method.set(status)

    def process_eye_capture_method_selection_callback(self):
        '''
        Process the options for recording
        :return:
        '''
        if int(self.eye_recording_method.get()) == 1:

            # Keep the child window selected
            # self.eye_recording_win.lift(aboveThis=self.parent)
            for i in range(EyeCoilChannelId.C16 + 1):
                self.eye_coil_channel_obj[i].configure(state=tk.NORMAL)

            if len(self.get_channel_selected_list()) >= 6:
                for i in range(EyeXYZIndex.TWAIN_XYZ_INDEX):
                    self.eye_pos_option_menu_object[i].configure(state=tk.NORMAL)

            recording_method_name = 'Eye Coil'
        elif int(self.eye_recording_method.get()) == 0:
            for i in range(EyeCoilChannelId.C16 + 1):
                self.eye_coil_channel_obj[i].configure(state=tk.DISABLED)

            for i in range(EyeXYZIndex.TWAIN_XYZ_INDEX):
                self.eye_pos_option_menu_object[i].configure(state=tk.DISABLED)

            recording_method_name = 'Eyelink'
        else:
            # No eye tracking
            recording_method_name = 'No Eyes'

        globls.update_eye_recording_method_parameters(int(self.eye_recording_method.get()),
                                                      recording_method_name)

    def draw_eye_coil_channel(self, edit=False):
        '''
        Draw frame and widgets for channel selection
        :param edit:
        :return:
        '''
        eye_coil_channel_widget = EyeRecordWidget['eye_coil_channel']
        eye_coil_channel_frame = WidgetApi.draw_frame(self.eye_recording_win,
                                                      eye_coil_channel_widget['main_frame'])
        WidgetApi.draw_label(self.eye_recording_win, eye_coil_channel_widget['eye_coil_label'])

        if edit:
            WidgetApi.draw_label(eye_coil_channel_frame, eye_coil_channel_widget['min_channel_selection_label'])
            # Get the default or config stored in file
            status = globls.analaog_input_output['eye_coil_channels']
            channel_lst = util.convert_int_to_bitlist(status)

            # Initialize eye coil channel
            for i in range(EyeCoilChannelId.C16 + 1):
                if i in channel_lst:
                    self.eye_coil_channel[i].set(1)

            i = 0
            for channel_dict in eye_coil_channel_widget['channels_checkbutton']:
                if not edit or self.eye_recording_method.get() == EyeRecordingMethods.EYE_LINK:
                    channel_dict['state'] = tk.DISABLED
                channel_dict['variable'] = self.eye_coil_channel[i]
                channel_dict['command'] = self.process_eye_coil_channel_selection_callback
                cb_resp = WidgetApi.draw_check_button(eye_coil_channel_frame, channel_dict)
                self.eye_coil_channel_obj.append(cb_resp)
                i += 1

    def process_eye_coil_channel_selection_callback(self):
        '''
        Process the channel selection to form a list
        :return:
        '''
        channel_selected_list = self.get_channel_selected_list()

        if len(channel_selected_list) >= 6:
            for i in range(EyeXYZIndex.TWAIN_XYZ_INDEX):
                value = self.eye_pos_option_menu_list[i].get()

                # Get the previous value and if not in the new list then reset the
                # corresponding eye's value to 1st on the list and user would have
                # to choose the appropriate values for recording
                if value not in channel_selected_list:
                    index = 0
                else:
                    index = channel_selected_list.index(value)

                self.eye_pos_option_menu_object[i].configure(state=tk.NORMAL)
                self._reset_option_menu(self.eye_pos_option_menu_object[i],
                                        self.eye_pos_option_menu_list[i],
                                        channel_selected_list,
                                        index=index)
        else:
            for i in range(EyeXYZIndex.TWAIN_XYZ_INDEX):
                self.eye_pos_option_menu_object[i].configure(state=tk.DISABLED)

    def _reset_option_menu(self, om_obj, om_variable, options, index=None):
        '''Reset the values in the option menu

        If index is given, set the value of the menu to
        the option at the given index
        '''
        menu = om_obj["menu"]
        menu.delete(0, "end")

        for string in options:
            menu.add_command(label=string,
                             command=lambda value=string:
                             om_variable.set(value))
        try:
            if index is not None:
                om_variable.set(options[index])
        except IndexError:
            om_variable.set(options[0])

    def draw_eye_pos_selection(self, edit=False):
        ''''
        Draw frames and widgets to select the channel for a specific eye
        '''
        eye_pos_selection_widget = EyeRecordWidget['eye_pos_selection']
        eye_pos_selection_frame = WidgetApi.draw_frame(self.eye_recording_win,
                                                       eye_pos_selection_widget['main_frame'])
        WidgetApi.draw_label(self.eye_recording_win, eye_pos_selection_widget['eye_pos_selection_label'])

        # Labels for eye selction for x, y, z
        for label in eye_pos_selection_widget['channel_config_labels']:
            WidgetApi.draw_label(eye_pos_selection_frame, label)

        # Channel selection
        channel_list = self.get_channel_selected_list()

        for option_dict in eye_pos_selection_widget['eyepos_option_menu']:
            status = globls.analaog_input_output['analog_channel'][option_dict['name']]
            self.eye_pos_option_menu_list[option_dict['value']].set(status)
            option_dict['variable'] = self.eye_pos_option_menu_list[option_dict['value']]
            if (not edit or len(channel_list) < 6 or
                        int(self.eye_recording_method.get()) == EyeRecordingMethods.EYE_LINK):
                option_dict['state'] = tk.DISABLED
            om_obj = WidgetApi.drawa_option_menu(eye_pos_selection_frame, option_dict, *channel_list if len(channel_list) else (1))
            self.eye_pos_option_menu_object.append(om_obj)

    def get_channel_selected_list(self):
        '''
        Get the selected channel list
        :return:
        '''
        channel_selected_list = []
        for i in range(EyeCoilChannelId.C16 + 1):
            if self.eye_coil_channel[i].get():
                channel_selected_list.append(str(i + 1))
        return channel_selected_list

    def get_eye_positions_channel(self):
        '''
        Get the associated channels for eye
        :return:
        '''
        return (self.eye_pos_option_menu_list[EyeXYZIndex.LEFT_X].get(),
                self.eye_pos_option_menu_list[EyeXYZIndex.LEFT_Y].get(),
                self.eye_pos_option_menu_list[EyeXYZIndex.LEFT_Z].get(),
                self.eye_pos_option_menu_list[EyeXYZIndex.RIGHT_X].get(),
                self.eye_pos_option_menu_list[EyeXYZIndex.RIGHT_Y].get(),
                self.eye_pos_option_menu_list[EyeXYZIndex.RIGHT_Z].get()
                )


EyeRecordWidget = {
    'recording_method_selection': {
        'main_frame': {
            'relx': EyeRecordFrame.SELCTION_RELX, 'rely': EyeRecordFrame.SELCTION_RELY,
            'width': EyeRecordFrame.WIDTH, 'height': EyeRecordFrame.SELCTION_HEIGHT},
        'method_selection_label': {
            'text': 'Eye Movement Selection',
            'relx': (EyeRecordFrame.SELCTION_RELX), 'rely': (EyeRecordFrame.SELCTION_RELY - 0.01),
            'relheight': 0.05, 'relwidth': 0.27},
        'radiobuttons': [
            {'text': ' Eyelink', 'value': EyeRecordingMethods.EYE_LINK,
            'relheight': 0.30, 'relwidth': 0.30,
             'relx': 0.20, 'rely': 0.35},
            {'text': ' Eye Coil', 'value': EyeRecordingMethods.EYE_COIL,
             'relheight': 0.30, 'relwidth': 0.30,
             'relx': 0.50,  'rely': 0.35},
            {'text': ' None', 'value': EyeRecordingMethods.NONE,
             'relheight': 0.30, 'relwidth': 0.30,
             'relx': 0.80,  'rely': 0.35}
        ],
    },
    'eye_coil_channel': {
        'main_frame': {
            'relx': EyeRecordFrame.COIL_CHANNEL_RELX, 'rely': EyeRecordFrame.COIL_CHANNEL_RELY,
            'width': EyeRecordFrame.WIDTH, 'height': EyeRecordFrame.COIL_CHANNEL_HEIGHT},
        'eye_coil_label': {
            'text': 'Eye Coil Channel Selection',
            'relx': EyeRecordFrame.COIL_CHANNEL_RELX, 'rely': (EyeRecordFrame.COIL_CHANNEL_RELY - 0.01),
            'relheight': 0.05, 'relwidth': 0.28},
        'min_channel_selection_label': {
            'text': '',
            'relx': 0.02, 'rely': 0.04,
            'relheight': 0.05, 'relwidth': 0.30},
        'channels_checkbutton': [
            {'text': ' 1', 'value': EyeCoilChannelId.C1, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.10, 'rely': 0.20,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 2', 'value': EyeCoilChannelId.C2, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.30, 'rely': 0.20,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 3', 'value': EyeCoilChannelId.C3, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.50, 'rely': 0.20,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 4', 'value': EyeCoilChannelId.C4, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.70, 'rely': 0.20,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 5', 'value': EyeCoilChannelId.C5, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.10, 'rely': 0.40,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 6', 'value': EyeCoilChannelId.C6, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.30, 'rely': 0.40,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 7', 'value': EyeCoilChannelId.C7, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.50, 'rely': 0.40,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 8', 'value': EyeCoilChannelId.C8, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.70, 'rely': 0.40,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 9', 'value': EyeCoilChannelId.C9, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.10, 'rely': 0.60,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 10', 'value': EyeCoilChannelId.C10, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.30, 'rely': 0.60,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 11', 'value': EyeCoilChannelId.C11, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.50, 'rely': 0.60,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 12', 'value': EyeCoilChannelId.C12, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.70, 'rely': 0.60,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 13', 'value': EyeCoilChannelId.C13, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.10, 'rely': 0.80,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 14', 'value': EyeCoilChannelId.C14, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.30, 'rely': 0.80,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 15', 'value': EyeCoilChannelId.C15, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.50, 'rely': 0.80,
             'relheight': 0.13, 'relwidth': 0.17},
            {'text': ' 16', 'value': EyeCoilChannelId.C16, 'onvalue': 1, 'offvalue': 0,
             'relx': 0.70, 'rely': 0.80,
             'relheight': 0.13, 'relwidth': 0.17},
        ],
    },
    'eye_pos_selection': {
        'main_frame': {
            'relx': EyeRecordFrame.EYECOIL_EYEPOS_RELX, 'rely': EyeRecordFrame.EYECOIL_EYEPOS_RELY,
            'width': EyeRecordFrame.WIDTH, 'height': EyeRecordFrame.EYECOIL_EYEPOS_HEIGHT},
        'eye_pos_selection_label': {
            'text': 'Eye Position Channels',
            'relx': EyeRecordFrame.EYECOIL_EYEPOS_RELX, 'rely': (EyeRecordFrame.EYECOIL_EYEPOS_RELY - 0.01),
            'relheight': 0.04, 'relwidth': 0.25},
        'channel_config_labels': [
            {'text': 'Channels',
             'relx': 0.42, 'rely': 0.07,
             'relheight': 0.13, 'relwidth': 0.15},
            {'text': 'Eye',
             'relx': 0.04, 'rely': 0.07,
             'relheight': 0.13, 'relwidth': 0.15},
            {'text': 'X',
             'relx': 0.26, 'rely': 0.16,
             'relheight': 0.13, 'relwidth': 0.15},
            {'text': 'Y',
             'relx': 0.45, 'rely': 0.16,
             'relheight': 0.13, 'relwidth': 0.15},
            {'text': 'Z',
             'relx': 0.65, 'rely': 0.16,
             'relheight': 0.13, 'relwidth': 0.15},
            {'text': 'Right',
             'relx': 0.04, 'rely': 0.30,
             'relheight': 0.13, 'relwidth': 0.15},
            {'text': 'Left',
             'relx': 0.04, 'rely': 0.60,
             'relheight': 0.13, 'relwidth': 0.15},
        ],
        'eyepos_option_menu': [
            {'name': 'left_x', 'value': EyeXYZIndex.LEFT_X,
             'relx': 0.19, 'rely': 0.58, },
            {'name': 'left_y','value': EyeXYZIndex.LEFT_Y,
             'relx': 0.39, 'rely': 0.58,},
            {'name': 'left_z', 'value': EyeXYZIndex.LEFT_Z,
             'relx': 0.59, 'rely': 0.58,},
            {'name': 'right_x', 'value': EyeXYZIndex.RIGHT_X,
             'relx': 0.19, 'rely': 0.28,},
            {'name': 'right_y', 'value': EyeXYZIndex.RIGHT_Y,
             'relx': 0.39, 'rely': 0.28,},
            {'name': 'right_z', 'value': EyeXYZIndex.RIGHT_Z,
             'relx': 0.59, 'rely': 0.28,}
        ],
    },
    'ok_button': {
        'text': 'ok',
        'relx': 0.40, 'rely': .94,
        'relheight': 0.04, 'relwidth': 0.20}
}
