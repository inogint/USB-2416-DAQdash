import tkinter as tk
from mcculw import ul
from mcculw.enums import DigitalPortType
from mcculw.ul import ULError
from utils.events import on_drag_start, on_drag_motion, right_click_menu

class DigitalInBinaryIndicator(tk.Label):
    def __init__(self, master, board_num, port_type, **kwargs):
        super().__init__(master, text='Digital In: 0', font=('Helvetica', 14), height=2, width=20, bg='lightgrey', **kwargs)
        self.board_num = board_num
        self.port_type = port_type
        self.locked = False
        self.value = 0  # Add a value attribute
        self.custom_name = "Digital In"  # Add a custom name attribute
        self.bind("<Button-1>", on_drag_start)
        self.bind("<B1-Motion>", on_drag_motion)
        self.bind("<Button-3>", lambda event: right_click_menu(event, self))
        self.update_indicator()

    def update_indicator(self):
        try:
            self.value = ul.d_in(self.board_num, self.port_type)
            self.config(text=f"{self.custom_name} {self.port_type.name}: {self.value}")
            self.after(100, self.update_indicator)  # Refresh every 100ms
        except ULError as e:
            print(f"Error reading digital input: {e}")

    def rename(self, new_name):
        self.custom_name = new_name
        self.config(text=f"{self.custom_name} {self.port_type.name}: {self.value}")