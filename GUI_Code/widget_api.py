'''
API to draw the widgets with various options
'''

import Tkinter as tk
import ttk

class WidgetAPI():
    # Common methods for drawing widget
    @staticmethod
    def draw_canvas(parent, canvas_dict):

        canvas = tk.Canvas(parent, background="white", borderwidth="2",
                           selectbackground="#c4c4c4")
        canvas.place(relx=canvas_dict['relx'], rely=canvas_dict['rely'],
                     relheight=canvas_dict['relheight'], relwidth=canvas_dict['relwidth'])
        return canvas

    @staticmethod
    def draw_scrolledtext(parent, scrolledtext_dict):
        stext = ScrolledText(parent, background="white", font="TkTextFont", setgrid="1",
                             insertborderwidth="3", relief=tk.RAISED, selectbackground="#c4c4c4",
                             width=scrolledtext_dict['width'], wrap=tk.NONE)

        stext.place(relx=scrolledtext_dict['relx'], rely=scrolledtext_dict['rely'],
                    relheight=scrolledtext_dict['relheight'], relwidth=scrolledtext_dict['relwidth'])
        return stext

    @staticmethod
    def draw_label(parent, label_dict):

        label = tk.Label(parent)
        if label_dict.get('relx') and label_dict.get('rely'):
            label.place(relx=label_dict['relx'],
                        rely=label_dict['rely'],
                        relheight=label_dict['relheight'],
                        relwidth=label_dict['relwidth']
                        )
            label.configure(anchor=tk.W)
            label.configure(compound="left")
            label.configure(justify=tk.LEFT)
            label.configure(activebackground="#f9f9f9")

        if label_dict.get('textvariable'):
            label.configure(textvariable=label_dict['textvariable'])
        if label_dict.get('text'):
            label.configure(text=label_dict['text'])
        if label_dict.get('width'):
            label.configure(width=label_dict['width'])
        return label

    @staticmethod
    def draw_frame(parent, frame_dict):

        frame_obj = tk.Frame(parent)
        if (not frame_dict.get('relheight') and
                not frame_dict.get('relwidth')):
            frame_obj.place(relx=frame_dict['relx'],
                            rely=frame_dict['rely'])
        else:
            frame_obj.place(relx=frame_dict['relx'], rely=frame_dict['rely'],
                            relheight=frame_dict['relheight'],
                            relwidth=frame_dict['relwidth'])
        frame_obj.configure(relief=tk.GROOVE)
        frame_obj.configure(borderwidth="2")
        frame_obj.configure(relief=tk.GROOVE)
        frame_obj.configure(background='#d9d9d9')
        if frame_dict.get('width'):
            frame_obj.configure(width=frame_dict['width'])
        if frame_dict.get('height'):
            frame_obj.configure(height=frame_dict['height'])
        return frame_obj

    @staticmethod
    def draw_check_button(parent, check_button_dict):
        checkbutton = tk.Checkbutton(parent, onvalue=1, offvalue=0, anchor=tk.W,
                                     activebackground="#d9d9d9", compound="left",
                                     justify=tk.LEFT, overrelief="raised",
                                     text=check_button_dict['text'],
                                     variable=check_button_dict['variable']
                                     )
        checkbutton.place(relx=check_button_dict['relx'], rely=check_button_dict['rely'],
                          relheight=check_button_dict['relheight'], relwidth=check_button_dict['relwidth'])

        if check_button_dict.get('command'):
            checkbutton.configure(command=check_button_dict['command'])
        if check_button_dict.get('color'):
            checkbutton.configure(activeforeground=check_button_dict['color'])
            checkbutton.configure(foreground=check_button_dict['color'])
        if check_button_dict.get('onvalue') is not None:
            checkbutton.configure(onvalue=check_button_dict['onvalue'])
        if check_button_dict.get('offvalue') is not None:
            checkbutton.configure(offvalue=check_button_dict['offvalue'])
        if check_button_dict.get('state') is not None:
            checkbutton.configure(state=check_button_dict['state'])
        return checkbutton

    @staticmethod
    def draw_spin_box(parent, spinbox_dict):
        spinbox = tk.Spinbox(parent, from_=spinbox_dict['from_val'], to=spinbox_dict['to_val'],
                             increment=spinbox_dict['increment'], background="white",
                             activebackground="#f9f9f9", highlightbackground="black",
                             textvariable=spinbox_dict['textvariable'])
        spinbox.place(relx=spinbox_dict['relx'], rely=spinbox_dict['rely'],
                      relheight=spinbox_dict['relheight'], relwidth=spinbox_dict['relwidth'])
        if spinbox_dict.get('color'):
            spinbox.configure(foreground=spinbox_dict['color'])
            spinbox.configure(selectbackground=spinbox_dict['color'])
        if spinbox_dict.get('func_callback', None) is not None:
            spinbox.configure(command=spinbox_dict['func_callback'])
            spinbox.bind('<Return>', spinbox_dict['func_callback'])
            spinbox.bind('<Key>', spinbox_dict['func_callback'])
        return spinbox

    @staticmethod
    def draw_button(parent, button_dict):
        button = tk.Button(parent, activebackground="#d9d9d9", text=button_dict['text'])
        if button_dict.get('relheight') and button_dict.get('relwidth'):
            button.place(relx=button_dict['relx'], rely=button_dict['rely'],
                         relheight= button_dict['relheight'], relwidth=button_dict['relwidth'])
        if button_dict.get('state', None) is not None:
            button.configure(state=button_dict['state'])
        if button_dict.get('command', None) is not None:
            button.configure(command=button_dict['command'])
        if button_dict.get('anchor', None) is not None:
            button.configure(anchor=button_dict['anchor'])
        button.configure(justify=tk.LEFT)

        return button

    @staticmethod
    def draw_entry(parent, entry_dict):
        ent = tk.Entry(parent, background="white", font="TkFixedFont",
                       selectbackground="#c4c4c4")
        if entry_dict.get('relx') and entry_dict.get('rely'):
            if entry_dict.get('relheight') and entry_dict.get('relwidth'):
                ent.place(relx=entry_dict['relx'], rely=entry_dict['rely'],
                          relheight=entry_dict['relheight'], relwidth=entry_dict['relwidth'])
            elif (entry_dict.get('relheight') and entry_dict.get('relwidth', None) is None):
                ent.place(relx=entry_dict['relx'], rely=entry_dict['rely'], relheight=entry_dict['relheight'])

        if entry_dict.get('width'):
            ent.configure(width=entry_dict['width'])
        if entry_dict.get('height'):
            ent.configure(height=entry_dict['height'])
        if entry_dict.get('value', None) is not None:
            ent.insert(0, entry_dict['value'])
        if entry_dict.get('textvariable', None) is not None:
            ent.configure(textvariable=entry_dict['textvariable'])
        if entry_dict.get('state') is not None:
            ent.configure(state=entry_dict['state'])
        return ent

    @staticmethod
    def draw_radio_button(parent, radio_button_dict):
        rb = tk.Radiobutton(parent)
        rb.place(relx=radio_button_dict['relx'],
                 rely=radio_button_dict['rely'],
                 relheight=radio_button_dict['relheight'],
                 relwidth=radio_button_dict['relwidth'])
        rb.configure(activebackground="#d9d9d9")
        rb.configure(anchor=tk.NW)
        rb.configure(compound="left")
        rb.configure(justify=tk.LEFT)
        rb.configure(text=radio_button_dict['text'])
        rb.configure(variable=radio_button_dict['variable'])
        rb.configure(value=radio_button_dict['value'])
        rb.configure(command=radio_button_dict['command'])
        rb.deselect()
        return rb

    @staticmethod
    def drawa_option_menu(parent, optionmenu_dict, *values):
        om_obj = tk.OptionMenu(parent, optionmenu_dict['variable'], *values)

        om_obj.place(relx=optionmenu_dict['relx'], rely=optionmenu_dict['rely'])
        om_obj.configure(width=5)
        if optionmenu_dict.get('state'):
            om_obj.configure(state=optionmenu_dict['state'])
        return om_obj

    def draw_scrollable_frame(self, parent, frame_dict):
        frame = tk.Frame(parent, relief=tk.GROOVE, borderwidth="2")
        frame.place(relx=frame_dict['relx'], rely=frame_dict['rely'],
                    relheight=frame_dict['relheight'], relwidth=frame_dict['relwidth'])
        # Create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(frame, bd=0, highlightthickness=0,
                           yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)
        # canvas.place(relx=0.01, rely=0.01, relheight=1.0, relwidth=.60)
        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        #
        # Create a frame inside the canvas which will be scrolled with it
        interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # Track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas' width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)
        return interior

WidgetApi = WidgetAPI()

# The following code is added to facilitate the scrolled widgets for text box.
class AutoScroll(object):
    '''
    Configure the scrollbars for a widget.
    '''

    def __init__(self, master):
        try:
            vsb = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        except:
            pass
        hsb = ttk.Scrollbar(master, orient='horizontal', command=self.xview)

        try:
            self.configure(yscrollcommand=self._autoscroll(vsb))
        except:
            pass
        self.configure(xscrollcommand=self._autoscroll(hsb))

        self.grid(column=0, row=0, sticky='nsew')
        try:
            vsb.grid(column=1, row=0, sticky='ns')
        except:
            pass
        hsb.grid(column=0, row=1, sticky='ew')

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        # Copy geometry methods of master (taken from ScrolledText.py)

        methods = tk.Pack.__dict__.keys() + tk.Grid.__dict__.keys() \
              + tk.Place.__dict__.keys()

        for meth in methods:
            if meth[0] != '_' and meth not in ('config', 'configure'):
                setattr(self, meth, getattr(master, meth))

    @staticmethod
    def _autoscroll(sbar):
        '''Hide and show scrollbar as needed.'''
        def wrapped(first, last):
            first, last = float(first), float(last)
            if first <= 0 and last >= 1:
                sbar.grid_remove()
            else:
                sbar.grid()
            sbar.set(first, last)
        return wrapped

    def __str__(self):
        return str(self.master)

def _create_container(func):
    '''Creates a ttk frame with a given master, and use this new frame to
    place the scrollbars and the widget.'''
    def wrapped(cls, master, **kw):
        container = ttk.Frame(master)
        return func(cls, container, **kw)
    return wrapped

class ScrolledText(AutoScroll, tk.Text):
    '''A standard Tkinter Text widget with scrollbars that will
    automatically show/hide as needed.'''
    @_create_container
    def __init__(self, master, **kw):
        tk.Text.__init__(self, master, **kw)
        AutoScroll.__init__(self, master)