# main.py

import tkinter as tk
from dashboard.app import DashboardApp
from scan_to_file import ScanToFile
from utils.device_utils import initialize_device, set_channel_settings

if __name__ == '__main__':
    root = tk.Tk()
    app = DashboardApp(root)
    
    # Initialize device and set channel settings
    device = initialize_device(0)
    channels = [0, 1, 2, 3]  # Example channel list, adjust as necessary
    set_channel_settings(0, channels)
    
    root.mainloop()
    
    # Initialize ScanToFile for live data display and channel selection
    scanner = ScanToFile(board_num=0, rate=1000, file_name='output.csv')
    scanner.root.mainloop()
