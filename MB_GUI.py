import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from Run_MAXBAND import RunMaxband
from Process_Results import ProcessResults
from config import Config
from Utilities import create_tooltip, tooltips
import matplotlib as matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

Cfg = Config()

status_dict = {
    2: 'Solution Found',  # Indicating that the problem is solvable, but potentially a local optimum
    1: 'Optimal Solution Found',  # Global optimum, problem solved
    0: 'No Solution Found',  # Still working on the problem
    -1: 'No Solution Exists',  # The problem is infeasible
    -2: 'Solution is Unbounded'  # The problem is unbounded
}


def check_float(new_val) -> bool:
    valid = False
    try:
        if isinstance(float(new_val), float):
            valid = True
    except ValueError:
        print(f"Must enter a float, which {new_val} is not")
        valid = False
    return valid


class MaxbandGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('MAXBAND MILP')
        self.protocol("WM_DELETE_WINDOW", self.quit_program)
        self.geometry("1500x900")
        self.min_signals = 2
        self.max_signals = 10
        self.current_nsignals = 7

        self.single_inputs = ['nsignals', 'c_min', 'c_max', 'v_min', 'v_max', 'inv_dv_min', 'inv_dv_max', 'k']
        self.single_entry_variables = dict.fromkeys(self.single_inputs)
        self.single_entries: dict = dict.fromkeys(self.single_inputs)
        self.single_entry_labels: dict = dict.fromkeys(self.single_inputs)

        self.segment_inputs = ['outbound_d', 'inbound_d']
        self.segment_entry_variables = dict.fromkeys(self.segment_inputs)
        self.segment_entries: dict = dict.fromkeys(self.segment_inputs)
        self.segment_side_entry_labels: dict = dict.fromkeys(self.segment_inputs)
        self.segment_top_entry_labels: list = []

        self.signal_inputs = ['outbound_r', 'inbound_r', 'outbound_l', 'inbound_l', 'outbound_tau', 'inbound_tau']
        self.signal_entry_variables = dict.fromkeys(self.signal_inputs)
        self.signal_entries: dict = dict.fromkeys(self.signal_inputs)
        self.signal_side_entry_labels: dict = dict.fromkeys(self.signal_inputs)
        self.signal_top_entry_labels: list = []

        self.constraint_flags: list[str] = ['leftturnleadlag', 'lt_leadlag_flag', 'lt_leadlead_flag', 'lt_laglag_flag',
                                            'mi_mj_max_1_flag', 'm_max_1_flag', 'tau_cstr_flag', 'tau_sum_flag',
                                            'w_0_flag', 'w_mono_flag']
        self.checkbutton_variables: dict = dict.fromkeys(self.constraint_flags)
        self.constraint_checkbuttons: dict = dict.fromkeys(self.constraint_flags)
        self.constraint_checkbutton_labels: dict = dict.fromkeys(self.constraint_flags)

        self.inputs: dict = {}
        self.outputs: dict = {}
        self.status = None
        self.run_counter = 0

        self.print_labels: dict = {}
        self.figure_canvas = None
        self.figure_toolbar = None

        self.check_signals = (self.register(self.check_signals), '%P')
        self.check_float_wrapper = (self.register(check_float), '%P')
        self.__create_widgets()

    def __create_widgets(self) -> None:
        self.create_segment_inputs()
        self.create_signal_inputs()
        self.create_single_inputs()
        self.create_constraint_selections()
        self.create_run_maxband_button()

        self.draw_widgets()
        self.fill_from_config()
        self.create_widget_tooltips()

    def quit_program(self) -> None:
        print('Shutting down')
        self.quit()
        self.destroy()

    def create_segment_inputs(self) -> None:
        outbound_d_list: list = []
        inbound_d_list: list = []
        segment_side_labels = ['Outbound length [m]', 'Inbound length [m]']

        for i in range(self.current_nsignals-1):
            outbound_d_list.append(tk.StringVar())
            inbound_d_list.append(tk.StringVar())

        self.segment_entry_variables: dict = {
            'outbound_d': outbound_d_list,
            'inbound_d': inbound_d_list
        }

        for key in self.segment_entries:
            self.segment_entries[key] = [None] * (self.current_nsignals - 1)

        for i, segment_input in enumerate(self.segment_inputs):
            self.segment_side_entry_labels[segment_input] = ttk.Label(self, text=segment_side_labels[i])
            for segment_index in range(self.current_nsignals-1):
                self.segment_entries[segment_input][segment_index] = \
                    ttk.Entry(self,
                              textvariable=self.segment_entry_variables[segment_input][segment_index],
                              validatecommand=self.check_float_wrapper,
                              validate='key',
                              width=6)

        for i in range(self.current_nsignals-1):
            self.segment_top_entry_labels.append(ttk.Label(self, text=f'Segment {i + 1}'))

    def create_signal_inputs(self) -> None:
        outbound_r_list: list = []
        inbound_r_list: list = []
        outbound_l_list: list = []
        inbound_l_list: list = []
        outbound_tau_list: list = []
        inbound_tau_list: list = []

        for i in range(self.current_nsignals):
            outbound_r_list.append(tk.StringVar())
            inbound_r_list.append(tk.StringVar())
            outbound_l_list.append(tk.StringVar())
            inbound_l_list.append(tk.StringVar())
            outbound_tau_list.append(tk.StringVar())
            inbound_tau_list.append(tk.StringVar())

        self.signal_entry_variables: dict = {
            'outbound_r': outbound_r_list,
            'inbound_r': inbound_r_list,
            'outbound_l': outbound_l_list,
            'inbound_l': inbound_l_list,
            'outbound_tau': outbound_tau_list,
            'inbound_tau': inbound_tau_list
        }

        for key in self.signal_entries:
            self.signal_entries[key] = [None] * self.current_nsignals

        side_labels = ['Outbound red time [cycles]', 'Inbound red time [cycles]',
                       'Outbound left turn time [cycles]', 'Inbound left turn time [cycles]',
                       'Outbound queue clearance time [cycles]', 'Inbound queue clearance time [cycles]']

        for i, signal_input in enumerate(self.signal_inputs):
            self.signal_side_entry_labels[signal_input] = ttk.Label(self, text=side_labels[i])
            for signal_index in range(self.current_nsignals):
                self.signal_entries[signal_input][signal_index] = \
                    ttk.Entry(self,
                              textvariable=self.signal_entry_variables[signal_input][signal_index],
                              validatecommand=self.check_float_wrapper,
                              validate='key',
                              width=6)

        for i in range(self.current_nsignals):
            self.signal_top_entry_labels.append(ttk.Label(self, text=f'Signal {i + 1}'))

    def create_single_inputs(self) -> None:
        single_input_labels = ['nsignals [-]', 'c_min [s]', 'c_max [s]', 'v_min [km/h]', 'v_max [km/h]',
                               'inv_dv_min [h/km]', 'inv_dv_max [h/km]', 'k [-]']

        self.single_entry_variables: dict = {
            'nsignals': tk.StringVar(),
            'c_min': tk.StringVar(),
            'c_max': tk.StringVar(),
            'v_min': tk.StringVar(),
            'v_max': tk.StringVar(),
            'inv_dv_min': tk.StringVar(),
            'inv_dv_max': tk.StringVar(),
            'k': tk.StringVar()
        }

        self.single_entries['nsignals'] = ttk.Spinbox(self,
                                                      textvariable=self.single_entry_variables['nsignals'],
                                                      from_=self.min_signals,
                                                      to=self.max_signals,
                                                      increment=1,
                                                      validatecommand=self.check_signals,
                                                      validate='key',
                                                      width=3)
        self.single_entries['nsignals'].bind('<<Increment>>', self.increase_nsignals)
        self.single_entries['nsignals'].bind('<<Decrement>>', self.decrease_nsignals)
        self.single_entry_variables['nsignals'].set(self.current_nsignals)

        for single_input in self.single_inputs[1:]:
            self.single_entries[single_input] = \
                ttk.Entry(self,
                          textvariable=self.single_entry_variables[single_input],
                          validatecommand=self.check_float_wrapper,
                          validate='key',
                          width=4)

        for i in range(len(self.single_inputs)):
            self.single_entry_labels[self.single_inputs[i]] = ttk.Label(self, text=single_input_labels[i])

    def create_constraint_selections(self) -> None:
        self.checkbutton_variables: dict = {
            'leftturnleadlag': tk.BooleanVar(),
            'lt_leadlag_flag': tk.BooleanVar(),
            'lt_leadlead_flag': tk.BooleanVar(),
            'lt_laglag_flag': tk.BooleanVar(),
            'mi_mj_max_1_flag': tk.BooleanVar(),
            'm_max_1_flag': tk.BooleanVar(),
            'tau_cstr_flag': tk.BooleanVar(),
            'tau_sum_flag': tk.BooleanVar(),
            'w_0_flag': tk.BooleanVar(),
            'w_mono_flag': tk.BooleanVar()
        }
        for i, flag in enumerate(self.constraint_flags):
            checkbutton = ttk.Checkbutton(master=self, name=flag, variable=self.checkbutton_variables[flag],
                                          onvalue=True, offvalue=False)
            self.constraint_checkbuttons[flag] = checkbutton
            self.constraint_checkbutton_labels[flag] = ttk.Label(master=self, text=flag)

    def create_run_maxband_button(self) -> None:
        run_maxband_button = ttk.Button(self, text='Run Maxband', command=self.maxband_process)
        run_maxband_button.grid(column=2, row=13)

    def draw_widgets(self) -> None:
        single_inputs_header = ttk.Label(self, text='Single Inputs', font='Helvetica 12 bold')
        single_inputs_header.grid(column=0, row=0, columnspan=2)
        for i, key in enumerate(self.single_entries):
            self.single_entry_labels[key].grid(column=0, row=i+1)
            self.single_entries[key].grid(column=1, row=i+1)

        segment_inputs_header = ttk.Label(self, text='Segment Inputs', font='Helvetica 12 bold')
        segment_inputs_header.grid(column=2, row=0)
        for i, segment_input in enumerate(self.segment_inputs):
            self.segment_side_entry_labels[segment_input].grid(column=2, row=i+1)
            for segment_index in range(self.current_nsignals-1):
                self.segment_entries[segment_input][segment_index].grid(column=segment_index+3, row=i+1)
        for i in range(self.current_nsignals-1):
            self.segment_top_entry_labels[i].grid(column=i+3, row=0)

        signal_inputs_header = ttk.Label(self, text='Signal Inputs', font='Helvetica 12 bold')
        signal_inputs_header.grid(column=2, row=4)
        for i, signal_input in enumerate(self.signal_inputs):
            self.signal_side_entry_labels[signal_input].grid(column=2, row=i+5)
            for signal_index in range(self.current_nsignals):
                self.signal_entries[signal_input][signal_index].grid(column=signal_index+3, row=i+5)
        for i in range(self.current_nsignals):
            self.signal_top_entry_labels[i].grid(column=i+3, row=4)

        for i, check_button in enumerate(self.constraint_flags):
            self.constraint_checkbuttons[check_button].grid(column=1, row=i+10)
            self.constraint_checkbutton_labels[check_button].grid(column=0, row=i+10)

    def fill_from_config(self) -> None:
        if not Cfg.check_for_config_file():  # There is no config to fill from
            return
        single_input_dict = Cfg.get_single_input_config()
        for key in self.single_entry_variables:
            self.single_entry_variables[key].set(single_input_dict[key])

        segment_input_dict = Cfg.get_segment_input_config()
        for key in self.segment_entry_variables:
            segment_input_list = list(segment_input_dict[key].strip("['']").split("', '"))
            for segment in range(self.current_nsignals-1):
                self.segment_entry_variables[key][segment].set(segment_input_list[segment])

        signal_input_dict = Cfg.get_signal_input_config()
        for key in self.signal_entry_variables:
            signal_input_list = list(signal_input_dict[key].strip("['']").split("', '"))
            for signal in range(self.current_nsignals):
                self.signal_entry_variables[key][signal].set(signal_input_list[signal])

        selection_input_dict = Cfg.get_selection_input_config()
        for key in self.checkbutton_variables:
            self.checkbutton_variables[key].set(selection_input_dict[key])

    def get_single_inputs(self) -> dict:
        single_inputs = dict.fromkeys(self.single_inputs)
        for inputs in self.single_inputs:
            single_inputs[inputs] = self.single_entry_variables[inputs].get()
        return single_inputs

    def get_segment_inputs(self) -> dict:
        segment_inputs = dict.fromkeys(self.segment_inputs)
        for inputs in self.segment_inputs:
            segment_inputs[inputs] = list([inp.get() for inp in self.segment_entries[inputs]])
        return segment_inputs

    def get_signal_inputs(self) -> dict:
        signal_inputs = dict.fromkeys(self.signal_inputs)
        for inputs in self.signal_inputs:
            signal_inputs[inputs] = list([inp.get() for inp in self.signal_entries[inputs]])
        return signal_inputs

    def get_selections(self) -> dict:
        selections = dict.fromkeys(self.constraint_flags)
        for flag in self.constraint_flags:
            selections[flag] = self.checkbutton_variables[flag].get()
        return selections

    def get_all_inputs(self) -> dict:
        all_inputs = dict()
        all_inputs['SingleInputs'] = self.get_single_inputs()
        all_inputs['SegmentInputs'] = self.get_segment_inputs()
        all_inputs['SignalInputs'] = self.get_signal_inputs()
        all_inputs['Selections'] = self.get_selections()
        return all_inputs

    def increase_nsignals(self, event) -> None:
        self.current_nsignals = int(self.single_entry_variables['nsignals'].get())
        print(self.current_nsignals, len(self.signal_entry_variables[self.signal_inputs[0]]))
        if self.current_nsignals >= 10 or len(self.signal_entry_variables[self.signal_inputs[0]]) == self.max_signals:
            print('Cannot go higher')
            return
        for i, key in enumerate(self.segment_entries):
            self.segment_entry_variables[key].append(tk.StringVar())
            self.segment_entries[key].append(ttk.Entry(self,
                                                       textvariable=self.segment_entry_variables[key][-1],
                                                       validatecommand=self.check_float_wrapper,
                                                       validate='key',
                                                       width=6))
            self.segment_entries[key][-1].grid(column=self.current_nsignals+2, row=i+1)

        self.segment_top_entry_labels.append(ttk.Label(self, text=f'Segment {self.current_nsignals}'))
        self.segment_top_entry_labels[-1].grid(column=self.current_nsignals+2, row=0)

        for i, key in enumerate(self.signal_inputs):
            self.signal_entry_variables[key].append(tk.StringVar())
            self.signal_entries[key].append(ttk.Entry(self,
                                                      textvariable=self.signal_entry_variables[key][-1],
                                                      validatecommand=self.check_float_wrapper,
                                                      validate='key',
                                                      width=6))
            self.signal_entries[key][-1].grid(column=self.current_nsignals+3, row=i+5)

        self.signal_top_entry_labels.append(ttk.Label(self, text=f'Signal {self.current_nsignals+1}'))
        self.signal_top_entry_labels[-1].grid(column=self.current_nsignals+3, row=4)

    def decrease_nsignals(self, event) -> None:
        #TODO: investigate usage of widget.forget() instead of destroy().
        # Make this method more robust... sometimes doesn't work
        # Pack forget means the widgets still exsist, so they can cause memory leak if repeatedly created
        self.current_nsignals = int(self.single_entry_variables['nsignals'].get())
        print(self.current_nsignals, len(self.signal_entry_variables[self.signal_inputs[0]]))
        if self.current_nsignals <= 2 or len(self.signal_entry_variables[self.signal_inputs[0]]) == self.min_signals:
            print('Cannot go lower')
            return
        for key in self.segment_entries:
            self.segment_entries[key][self.current_nsignals-2].destroy()
            self.segment_entry_variables[key].pop()
        self.segment_top_entry_labels[self.current_nsignals-2].destroy()

        for key in self.signal_inputs:
            self.signal_entries[key][self.current_nsignals-1].destroy()
            self.signal_entry_variables[key].pop()
        self.signal_top_entry_labels[self.current_nsignals-1].destroy()

    def check_signals(self, new_val) -> bool:
        valid = False
        try:
            if isinstance(int(new_val), int):
                valid = True
            if int(new_val) < self.min_signals:
                print(f"Minimum value is {self.min_signals}")
                valid = False
            if int(new_val) > self.max_signals:
                print(f"Maximum value is {self.max_signals}")
                valid = False
        except ValueError:
            print(f"Must enter an integer, which {new_val} is not")
            valid = False
        return valid

    def create_widget_tooltips(self) -> None:
        for label in self.single_entry_labels:
            create_tooltip(self.single_entry_labels[label], tooltips[label])
        for label in self.segment_side_entry_labels:
            create_tooltip(self.segment_side_entry_labels[label], tooltips[label])
        for label in self.signal_side_entry_labels:
            create_tooltip(self.signal_side_entry_labels[label], tooltips[label])
        for label in self.constraint_checkbutton_labels:
            create_tooltip(self.constraint_checkbutton_labels[label], tooltips[label])

    def maxband_process(self) -> None:
        """"Handles the run_maxband button press, destroying previous results, gathering all input, saving input to
        config, running maxband and finally printing and plotting the new results"""
        self.destroy_previous_print_results()
        self.destroy_previous_plot_frame()
        self.inputs = self.get_all_inputs()
        Cfg.store_dict_into_config_file(self.inputs)
        rm = RunMaxband(self.inputs)
        self.outputs, self.status = rm.run_maxband()
        self.run_counter += 1
        PR = ProcessResults(self.inputs, self.outputs)
        processed_results = PR.get_processed_results_dict()
        self.create_print_labels(processed_results)
        self.draw_print_labels()
        if int(self.status) != 1:
            return
        self.create_plot_frame(PR)
        self.draw_plot_frame()

    def create_print_labels(self, processed_results) -> None:
        self.print_labels['status_label'] = ttk.Label(self, text=f'Problem status: {status_dict[self.status]}')
        if int(self.status) != 1:
            return
        self.print_labels['ct_label'] = ttk.Label(self, text=f'Cycle Time: {1/self.outputs["inv_CT"]:.1f} [s]')

        if float(self.inputs['SingleInputs']['k']) == 1:  # outbound bandwidth equals inbound bandwidth
            self.print_labels['band_label'] = ttk.Label(self, text=f'Bandwidth: {self.outputs["OB_band"]/self.outputs["inv_CT"]:.1f} [s]')
            self.print_labels['frac_band_label'] = ttk.Label(self, text=f'Fractional bandwidth: {self.outputs["OB_band"]:.2f} [cycles]')

        elif float(self.inputs['SingleInputs']['k']) != 1:
            self.print_labels['ob_band_label'] = ttk.Label(self, text=f'Outbound bandwidth: {self.outputs["OB_band"]/self.outputs["inv_CT"]:.1f} [s]')
            self.print_labels['ob_frac_band_label'] = ttk.Label(self, text=f'Fractional outbound bandwidth: {self.outputs["OB_band"]:.2f} [cycles]')
            self.print_labels['ib_band_label'] = ttk.Label(self, text=f'Inbound bandwidth: {self.outputs["IB_band"]/self.outputs["inv_CT"]:.1f} [s]')
            self.print_labels['ib_frac_band_label'] = ttk.Label(self, text=f'Fractional inbound bandwidth: {self.outputs["IB_band"]:.2f} [cycles]')

        self.print_labels['ob_speeds_label'] = ttk.Label(self, text=f'Outbound speeds: {processed_results["OB_speeds"]} [km/h]')
        self.print_labels['ib_speeds_label'] = ttk.Label(self, text=f'Inbound speeds: {processed_results["IB_speeds"]} [km/h]')

    def draw_print_labels(self) -> None:
        for i, key in enumerate(self.print_labels):
            self.print_labels[key].grid(column=0, row=19+i, columnspan=3, sticky='W')

    def destroy_previous_print_results(self) -> None:
        if self.run_counter == 0:  # First run, there is no output, return
            return
        for key in self.print_labels:
            self.print_labels[key].destroy()
        self.print_labels: dict = {}

    def create_plot_frame(self, PR) -> None:
        # TODO: implement a way to enter intersection names dynamically
        # intersection_names = ['2016', '2017', '2018', '2019', '2020', '2021', '2024']
        fig = Figure(figsize=(8, 5))
        # fig.patch.set_facecolor('skyblue')  # this can set the color around the plot, inside the frame
        # TODO: Implement some plot customization options
        PR.plot_MAXBAND(fig)
        fig.tight_layout()
        self.figure_canvas = FigureCanvasTkAgg(fig, self)
        self.figure_toolbar = NavigationToolbar2Tk(self.figure_canvas, self, pack_toolbar=False)

    def draw_plot_frame(self) -> None:
        self.figure_canvas.get_tk_widget().grid(column=3, row=12, columnspan=50, rowspan=28, sticky='NSEW')
        self.figure_toolbar.grid(columns=3, row=12+28, columnspan=50)

    def destroy_previous_plot_frame(self) -> None:
        if self.run_counter == 0:
            return
        self.figure_canvas.get_tk_widget().destroy()
        self.figure_canvas = None
        self.figure_toolbar.destroy()
        self.figure_toolbar = None
