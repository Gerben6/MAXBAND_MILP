import configparser as configparser
from os.path import exists
from typing import Optional


class Config:

    def __init__(self):
        self.config: configparser.ConfigParser = configparser.ConfigParser(empty_lines_in_values=False)
        self.path: str = 'config.ini'
        self.exist = self.check_for_config_file()
        self.section_names = ['SingleInputs', 'SegmentInputs', 'SignalInputs', 'Selections']
        self.input_dict = self.read_config_into_dict()

    def check_for_config_file(self) -> bool:
        return exists(self.path)

    def read_config_into_dict(self) -> Optional[dict]:
        if not self.exist:
            print('No configfile present')
            return
        self.config.read(self.path)
        input_dict = dict()
        for section in self.section_names:
            if section == 'Selections':
                temp_dict = dict()
                for key in self.config[section]:
                    temp_dict[key] = self.config.getboolean(section, key)
                input_dict[section] = temp_dict
                continue
            input_dict[section] = self.config[section]
        return input_dict

    def store_dict_into_config_file(self, input_dict) -> None:
        for section in self.section_names:
            self.config[section] = input_dict[section]

        with open(self.path, 'w') as configfile:
            self.config.write(configfile)

    def get_single_input_config(self) -> dict:
        return dict(self.input_dict['SingleInputs'])

    def get_segment_input_config(self) -> dict:
        return dict(self.input_dict['SegmentInputs'])

    def get_signal_input_config(self) -> dict:
        return dict(self.input_dict['SignalInputs'])

    def get_selection_input_config(self) -> dict:
        return dict(self.input_dict['Selections'])

# Settings Almere
# nsignals = 7
# c_min = 66
# c_max = 100
# v_min = 30
# v_max = 50
# inv_dv_min = 0.05
# inv_dv_max = 0.05
# k = 1

# outbound_d = ['374', '265', '277', '305', '260', '270']
# inbound_d = ['374', '265', '277', '305', '260', '270']

# outbound_r = ['0.586', '0.585', '0.621', '0.566', '0.647', '0.495', '0.497']
# inbound_r = ['0.619', '0.589', '0.680', '0.576', '0.482', '0.520', '0.557']
# outbound_l = ['0.103', '0.101', '0.113', '0.095', '0.000', '0.091', '0.084']
# inbound_l = ['0.104', '0.104', '0.106', '0.099', '0.429', '0.099', '0.097']
# outbound_tau = ['0.000', '0.030', '0.023', '0.044', '0.038', '0.069', '0.035']
# inbound_tau = ['0.024', '0.038', '0.019', '0.044', '0.020', '0.025', '0.000']
