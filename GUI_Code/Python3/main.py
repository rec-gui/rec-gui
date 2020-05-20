'''
Main function
'''
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

import threading
import utility as util
from constants import Constant as const
from global_parameters import Globals as globls
from eye_interpret import EyeInterpret
from arbitrator_server import ArbitratorServer
from gui import Gui
import xipppy as xp
from tkinter import messagebox


class Main:
    def __init__(self):
        root = tk.Tk()
        globls.update_gui_parameters(root=root)

        # Main thread which is the GUI thread
        gui = Gui()
        globls.update_gui_parameters(gui_object=gui)

        # Setup thread
        # Set up the thread to do asynchronous socket
        # More can be made if necessary
        self.stop_threads = threading.Event()
        self.stop_threads.clear()

        # # Eye interpreter
        self.eye_interpreter_thread = threading.Thread(target=EyeInterpret)
        self.eye_interpreter_thread.setDaemon(True)
        self.eye_interpreter_thread.start()

        self.arbitrator_server_thread = threading.Thread(target=ArbitratorServer)
        self.arbitrator_server_thread.setDaemon(True)
        self.arbitrator_server_thread.start()

        self.exit_check_periodic_call()

        # Check if Ripple Grapevine is connected
        if messagebox.askyesno("Connect to Ripple?", "Do you want to connect to Ripple?", parent=root):
            try:
                xpConnection = xp.xipppy_open(use_tcp=True)
                xpConnection.__enter__()
                globls.XIPPPY_CONNECTION = True
                print('Connection to Ripple Grapevine established.')
                # Test connection by printing time
                print('Printing time stamp: ', xp.time())
            except Exception as e:
                print('Ripple Grapevine is not connected...')
                globls.XIPPPY_CONNECTION = False
        else:
            print('User declined to connect to Ripple.')
            globls.XIPPPY_CONNECTION = False

        root.mainloop()

    def exit_check_periodic_call(self):
        '''
        cleanup on exit
        :return:
        '''
        # Check every 100ms if program is running or quit
        if globls.is_program_running:
            globls.gui_root.after(100, self.exit_check_periodic_call)
            return

        # self.stop_threads.set()
        # if self.eye_interpreter_thread:
        #     self.eye_interpreter_thread.join(1)
        #     while self.eye_interpreter_thread.is_alive():
        #         continue

        if self.arbitrator_server_thread:
            self.arbitrator_server_thread.join(1)
            while self.arbitrator_server_thread.is_alive():
                # continue
                print('Break code to close arbitrator_server_thread (main: line 74)')
                break

        # self.eye_interpreter_thread = None
        self.arbitrator_server_thread = None

        # Close Ripple connection
        if globls.XIPPPY_CONNECTION:
            xp._close()
            xp._close()
            print('Ripple connection closed.')

        exit(1)

if __name__ == '__main__':
    m = Main()
