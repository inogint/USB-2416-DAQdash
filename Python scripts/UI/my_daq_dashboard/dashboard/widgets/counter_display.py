import tkinter as tk
from mcculw import ul
from utils.events import on_drag_start, on_drag_motion, right_click_menu

class CounterDisplay(tk.Label):
    def __init__(self, master, board_num, counter_num=0, **kwargs):
        super().__init__(master, text='Counter: 0', font=('Helvetica', 14), height=2, width=20, bg='lightgrey', **kwargs)
        self.board_num = board_num
        self.counter_num = counter_num
        self.value = 0  # Add a value attribute
        self.locked = False
        self.update_display_id = None  # To store the after callback ID
        self.custom_name = "Counter"  # Add a custom name attribute
        self.bind("<Button-1>", on_drag_start)
        self.bind("<B1-Motion>", on_drag_motion)
        self.bind("<Button-3>", lambda event: right_click_menu(event, self))
        self.update_display()

    def update_display(self):
        try:
            self.value = ul.c_in(self.board_num, self.counter_num)
            self.config(text=f"{self.custom_name}: {self.value}")
            self.update_display_id = self.after(500, self.update_display)
        except tk.TclError:
            # This exception occurs if the widget is destroyed while the callback is still scheduled
            return

    def rename(self, new_name):
        self.custom_name = new_name
        self.config(text=f"{self.custom_name}: {self.value}")

    def remove_widget(self):
        if self.update_display_id:
            self.after_cancel(self.update_display_id)  # Cancel the scheduled update
        self.destroy()