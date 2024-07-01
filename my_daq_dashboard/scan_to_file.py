# scan_to_file.py

from ctypes import c_double, cast, POINTER, addressof, sizeof
from time import sleep
from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw.device_info import DaqDeviceInfo
import tkinter as tk
from tkinter import scrolledtext, Checkbutton, IntVar
from utils.device_utils import initialize_device, set_channel_settings

class ScanToFile:
    def __init__(self, board_num, rate, file_name, buffer_size_seconds=2, num_buffers_to_write=5):
        self.board_num = board_num
        self.rate = rate
        self.file_name = file_name
        self.buffer_size_seconds = buffer_size_seconds
        self.num_buffers_to_write = num_buffers_to_write
        self.memhandle = None
        self.channel_vars = []
        self.selected_channels = []

        # Set up the Tkinter window for live data display and channel selection
        self.root = tk.Tk()
        self.root.title("Channel Selection and Live Data Display")
        self.setup_channel_selection()
        self.text_area = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.text_area.pack()
        self.start_button = tk.Button(self.root, text="Start Scan", command=self.start_scan)
        self.start_button.pack()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_channel_selection(self):
        # Validate device and get available channels
        daq_dev_info = self.validate_device()
        ai_info = daq_dev_info.get_ai_info()
        num_chans = ai_info.num_chans

        # Create checkboxes for each channel
        for i in range(num_chans):
            var = IntVar()
            chk = Checkbutton(self.root, text=f"Channel {i}", variable=var)
            chk.pack(anchor=tk.W)
            self.channel_vars.append((var, i))

    def validate_device(self):
        daq_dev_info = DaqDeviceInfo(self.board_num)
        if not daq_dev_info.supports_analog_input:
            raise Exception('Error: The DAQ device does not support analog input')
        return daq_dev_info

    def configure_scan(self, ai_info):
        self.selected_channels = [i for var, i in self.channel_vars if var.get() == 1]
        set_channel_settings(self.board_num, self.selected_channels)  # Add this line
        num_chans = len(self.selected_channels)
        points_per_channel = max(self.rate * self.buffer_size_seconds, 10)

        if ai_info.packet_size != 1:
            packet_size = ai_info.packet_size
            remainder = points_per_channel % packet_size
            if remainder != 0:
                points_per_channel += packet_size - remainder

        ul_buffer_count = points_per_channel * num_chans
        points_to_write = ul_buffer_count * self.num_buffers_to_write
        write_chunk_size = int(ul_buffer_count / 10)

        return ul_buffer_count, points_to_write, write_chunk_size


    def start_scan(self):
        self.run_scan()

    def run_scan(self):
        try:
            daq_dev_info = self.validate_device()
            ai_info = daq_dev_info.get_ai_info()
            ul_buffer_count, points_to_write, write_chunk_size = self.configure_scan(ai_info)
            ai_range = ai_info.supported_ranges[0]
            scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA)

            self.memhandle = ul.scaled_win_buf_alloc(ul_buffer_count)
            if not self.memhandle:
                raise Exception('Failed to allocate memory')

            write_chunk_array = (c_double * write_chunk_size)()
            ul.a_in_scan(self.board_num, self.selected_channels[0], self.selected_channels[-1], ul_buffer_count, self.rate, ai_range, self.memhandle, scan_options)

            status = Status.IDLE
            while status == Status.IDLE:
                status, _, _ = ul.get_status(self.board_num, FunctionType.AIFUNCTION)

            with open(self.file_name, 'w') as f:
                print(f'Writing data to {self.file_name}')
                for chan_num in self.selected_channels:
                    f.write(f'Channel {chan_num},')
                    self.text_area.insert(tk.END, f'Channel {chan_num},\n')
                f.write('\n')
                self.text_area.insert(tk.END, '\n')

                prev_count = 0
                prev_index = 0
                while status != Status.IDLE:
                    status, curr_count, _ = ul.get_status(self.board_num, FunctionType.AIFUNCTION)
                    new_data_count = curr_count - prev_count

                    if new_data_count > ul_buffer_count:
                        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
                        print('A buffer overrun occurred')
                        break

                    if new_data_count >= write_chunk_size:
                        if prev_index + write_chunk_size > ul_buffer_count - 1:
                            first_chunk_size = ul_buffer_count - prev_index
                            second_chunk_size = write_chunk_size - first_chunk_size
                            ul.scaled_win_buf_to_array(self.memhandle, write_chunk_array, prev_index, first_chunk_size)
                            second_chunk_pointer = cast(addressof(write_chunk_array) + first_chunk_size * sizeof(c_double), POINTER(c_double))
                            ul.scaled_win_buf_to_array(self.memhandle, second_chunk_pointer, 0, second_chunk_size)
                        else:
                            ul.scaled_win_buf_to_array(self.memhandle, write_chunk_array, prev_index, write_chunk_size)

                        for i in range(write_chunk_size):
                            value = write_chunk_array[i]
                            f.write(f'{value},')
                            self.text_area.insert(tk.END, f'{value}, ')
                            self.text_area.see(tk.END)
                            if (i + 1) % len(self.selected_channels) == 0:
                                f.write('\n')
                                self.text_area.insert(tk.END, '\n')

                        prev_count += write_chunk_size
                        prev_index += write_chunk_size
                        prev_index %= ul_buffer_count

                    if prev_count >= points_to_write:
                        break

                    self.root.update_idletasks()
                    self.root.update()
                    sleep(0.1)

            ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
        except Exception as e:
            print('\n', e)
        finally:
            print('Done')
            if self.memhandle:
                ul.win_buf_free(self.memhandle)
            ul.release_daq_device(self.board_num)
            self.root.destroy()

    def on_closing(self):
        self.root.destroy()

if __name__ == '__main__':
    scanner = ScanToFile(board_num=0, rate=1000, file_name='output.csv')
    scanner.root.mainloop()
