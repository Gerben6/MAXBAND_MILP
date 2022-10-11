import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from math import ceil, floor


class ProcessResults:

    def __init__(self, inputs, outputs):
        self.input_dict: dict = inputs
        self.nSignals = int(self.input_dict['SingleInputs']['nsignals'])
        self.d = np.array(np.cumsum([0.0] + [float(d) for d in self.input_dict['SegmentInputs']['outbound_d']]))
        self.d_ = np.array(np.cumsum([0.0] + [float(d_) for d_ in self.input_dict['SegmentInputs']['inbound_d']]))
        self.r = [float(r) for r in self.input_dict['SignalInputs']['outbound_r']]
        self.r_ = [float(r_) for r_ in self.input_dict['SignalInputs']['inbound_r']]
        self.l = [float(l) for l in self.input_dict['SignalInputs']['outbound_l']]
        self.l_ = [float(l) for l in self.input_dict['SignalInputs']['inbound_l']]
        ## TODO: Ingtegrate Deltas as propor input, for now set to all zeros
        self.Deltas = np.zeros(self.nSignals)
        self.tau: list = [float(tau) for tau in self.input_dict['SignalInputs']['outbound_tau']]
        self.tau_: list = [float(tau_) for tau_ in self.input_dict['SignalInputs']['inbound_tau']]
        self.leftturnleadlag = self.input_dict['Selections']['leftturnleadlag']
        self.tau_sum_flag = self.input_dict['Selections']['tau_sum_flag']

        self.output_dict: dict = outputs
        self.OB_band = self.output_dict['OB_band']
        self.IB_band = self.output_dict['IB_band']
        self.inv_CT = self.output_dict['inv_CT']
        self.OB_w = self.output_dict['OB_w']
        self.IB_w = self.output_dict['IB_w']
        self.OB_t = self.output_dict['OB_t']
        self.IB_t = self.output_dict['IB_t']
        self.offsets = self.output_dict['offsets']
        if self.leftturnleadlag:
            self.OB_delta = self.output_dict['OB_delta']
            self.IB_delta = self.output_dict['IB_delta']

        self.s_OB_b = self.compute_OB_startband_timings()
        self.s_IB_b = self.compute_IB_startband_timings()

        self.e_OB_b = self.compute_OB_endband_timings()
        self.e_IB_b = self.compute_IB_endband_timings()

        self.OB_red = self.compute_OB_red_timings()
        self.IB_red = self.compute_IB_red_timings()

        if self.leftturnleadlag:
            self.OB_left = self.compute_OB_leftturn_timings()
            self.IB_left = self.compute_IB_leftturn_timings()

        self.OB_speeds = self.get_segment_speeds(self.OB_t, self.d, 1)
        self.IB_speeds = self.get_segment_speeds(self.IB_t, self.d_, 1)

    def get_OB_startband_origin(self) -> float:
        if self.leftturnleadlag:
            return self.l[0] * self.OB_delta[0] - self.l_[0] * self.IB_delta[0] + self.r[0] - 0.5 * self.r_[0] + self.OB_w[0] + self.tau[0]

        if not self.leftturnleadlag:
            return self.Deltas[0] + 0.5 * self.r[0] + self.OB_w[0] + self.tau[0]

    def get_IB_startband_origin(self) -> float:
        return -0.5 * self.r_[0] - self.IB_w[0] + self.tau_[0] - self.IB_band

    def compute_OB_startband_timings(self) -> np.array:
        s_OB_b = np.zeros((self.nSignals, 2))  # intersection nr, arrival / departure
        s_OB_b[0, 0] = self.get_OB_startband_origin()
        s_OB_b[0, 1] = s_OB_b[0, 0] - self.tau[0]
        for i in range(self.nSignals - 1):
            s_OB_b[i + 1, 0] = s_OB_b[i, 1] + self.OB_t[i]
            s_OB_b[i + 1, 1] = s_OB_b[i + 1, 0] - self.tau[i + 1]
        return s_OB_b

    def compute_IB_startband_timings(self) -> np.array:
        s_IB_b = np.zeros((self.nSignals, 2))  # intersection nr, arrival / departure
        s_IB_b[0, 0] = self.get_IB_startband_origin()
        s_IB_b[0, 1] = s_IB_b[0, 0] - self.tau_[0]
        for i in range(self.nSignals - 1):
            s_IB_b[i + 1, 1] = s_IB_b[i, 0] - self.IB_t[i]
            s_IB_b[i + 1, 0] = s_IB_b[i + 1, 1] + self.tau_[i + 1]
        return s_IB_b

    def compute_OB_endband_timings(self) -> np.array:
        e_OB_b = np.zeros((self.nSignals, 2))
        if self.tau_sum_flag:
            for i in range(self.nSignals):
                e_OB_b[i, :] = self.s_OB_b[i, 1] + self.OB_band + np.sum(self.tau[:i + 1])
        elif not self.tau_sum_flag:
            e_OB_b = self.s_OB_b + self.OB_band
        return e_OB_b

    def compute_IB_endband_timings(self) -> np.array:
        e_IB_b = np.zeros((self.nSignals, 2))
        if self.tau_sum_flag:
            for i in range(self.nSignals):
                e_IB_b[i, :] = self.s_IB_b[i, 1] + self.IB_band + np.sum(self.tau_[:self.nSignals - 1 - i])
        elif not self.tau_sum_flag:
            e_IB_b = self.s_IB_b + self.IB_band
        return e_IB_b

    def compute_OB_red_timings(self) -> np.array:  # =end red
        OB_red = np.zeros((self.nSignals, 2))  # intersection nr, start/end
        for i in range(self.nSignals):
            OB_red[i, 1] = self.s_OB_b[i, 1] - self.OB_w[i]
            OB_red[i, 0] = OB_red[i, 1] - self.r[i]
        return OB_red

    def compute_IB_red_timings(self) -> np.array:  # =end red
        IB_red = np.zeros((self.nSignals, 2))  # intersection nr, start/end
        for i in range(self.nSignals):
            if not self.tau_sum_flag:
                IB_red[i, 0] = self.e_IB_b[i, 1] + self.IB_w[i]
            elif self.tau_sum_flag:
                IB_red[i, 0] = self.e_IB_b[i, 1] + self.IB_w[i] - np.sum(self.tau_[:self.nSignals - 1 - i])
            IB_red[i, 1] = IB_red[i, 0] + self.r_[i]
        return IB_red

    def compute_OB_leftturn_timings(self) -> np.array:  # take note that outbound left turn is part of inbound red time
        OB_left = np.zeros((self.nSignals, 2))
        for i in range(self.nSignals):
            if self.OB_delta[i] == 0:  # left turn before inbound green so ends at end of inbound red
                OB_left[i, 1] = self.IB_red[i, 1]
                OB_left[i, 0] = OB_left[i, 1] - self.l[i]
            elif self.OB_delta[i] == 1:  # left turn after
                OB_left[i, 0] = self.IB_red[i, 0]
                OB_left[i, 1] = OB_left[i, 0] + self.l[i]
        return OB_left

    def compute_IB_leftturn_timings(self) -> np.array:  # take note that inbound left turn is part of outbound red time
        IB_left = np.zeros((self.nSignals, 2))  # intersection nr, start/end
        for i in range(self.nSignals):
            if self.IB_delta[i] == 0:  # left turn before outbound green so ends at end of OB_red
                IB_left[i, 1] = self.OB_red[i, 1]
                IB_left[i, 0] = IB_left[i, 1] - self.l_[i]
            elif self.IB_delta[i] == 1:  # left turn after outbound green so start at start of OB_red
                IB_left[i, 0] = self.OB_red[i, 0]
                IB_left[i, 1] = IB_left[i, 0] + self.l_[i]
        return IB_left

    def get_segment_speeds(self, t, d, decimals=2) -> np.array:
        speeds = [round(((d[i + 1] - d[i]) * self.inv_CT / t[i]) * 3.6, decimals) for i in range(len(t))]
        return speeds

    def get_processed_results_dict(self) -> dict:
        processed_results_dict = {}
        processed_results_dict['s_OB_b'] = self.s_OB_b
        processed_results_dict['s_IB_b'] = self.s_IB_b
        processed_results_dict['e_OB_b'] = self.e_OB_b
        processed_results_dict['e_IB_b'] = self.e_IB_b
        processed_results_dict['OB_red'] = self.OB_red
        processed_results_dict['IB_red'] = self.IB_red
        processed_results_dict['OB_left'] = self.OB_left
        processed_results_dict['IB_left'] = self.IB_left
        processed_results_dict['OB_speeds'] = self.OB_speeds
        processed_results_dict['IB_speeds'] = self.IB_speeds
        return processed_results_dict

    # Function used to create the plot
    def plot_MAXBAND(self, fig, intersection_names=None) -> plt.subplot:
        newd = sorted(np.concatenate((self.d, self.d)))
        newd_ = sorted(np.concatenate((self.d_, self.d_)))
        max_nr_cycles = ceil(self.e_OB_b[-1, 0])
        min_nr_cycles = floor(self.s_IB_b[-1, 1])
        axx = fig.add_subplot(111)
        axx.set_xlabel('Cycles')
        axx.set_xlim(0, max_nr_cycles + 1)
        axx.set_xticks(np.arange(0, max_nr_cycles + 1, 1))
        axx.plot(self.s_OB_b.flatten(), newd, color='lightgreen', label='Outbound band')
        axx.plot(self.e_OB_b.flatten(), newd, color='lightgreen')
        axx.plot(self.s_OB_b.flatten() + 1, newd, color='lightgreen')
        axx.plot(self.e_OB_b.flatten() + 1, newd, color='lightgreen')
        axx.plot(np.flip(self.s_IB_b, axis=1).flatten() + 3, newd_, color='darkgreen', label='Inbound band')
        axx.plot(np.flip(self.e_IB_b, axis=1).flatten() + 3, newd_, color='darkgreen')  # flip because drawing in reverse
        axx.plot(np.flip(self.s_IB_b, axis=1).flatten() + 4, newd_, color='darkgreen')
        axx.plot(np.flip(self.e_IB_b, axis=1).flatten() + 4, newd_, color='darkgreen')
        axx.plot(np.flip(self.s_IB_b, axis=1).flatten() + 5, newd_, color='darkgreen')
        axx.plot(np.flip(self.e_IB_b, axis=1).flatten() + 5, newd_, color='darkgreen')
        handles, labels = plt.gca().get_legend_handles_labels()
        line1 = Line2D([0], [0], label='Outbound red', color='lightcoral')
        line2 = Line2D([0], [0], ls='dashed', label='Inbound red', color='darkred')

        # plot outbound red times
        for j, dis in enumerate(self.d):
            for s in range(-2, max_nr_cycles + 2):
                axx.hlines(dis, self.OB_red[j, 0] - s, self.OB_red[j, 1] - s, color='lightcoral', lw=1.3)

        # plot inbound red times
        for k, dis_ in enumerate(self.d_):
            for s in range(max_nr_cycles + 4):
                axx.hlines(dis_, self.IB_red[k, 0] + s, self.IB_red[k, 1] + s, color='darkred', lw=1.3, linestyle='dashed')

        if self.leftturnleadlag:
            line3 = Line2D([0], [0], label='Outbound left turn', color='darkblue')
            line4 = Line2D([0], [0], ls='dashed', label='Inbound left turn', color='blue')
            handles.extend([line1, line2, line3, line4])
            # plot outbound left turn times
            for l, dis_ in enumerate(self.d_):
                for s in range(max_nr_cycles + 4):
                    axx.hlines(dis_, self.OB_left[l, 0] + s, self.OB_left[l, 1] + s, color='darkblue', lw=1.5)

            # plot inbound left turn times
            for m, dis in enumerate(self.d):
                for s in range(-2, max_nr_cycles + 2):
                    axx.hlines(dis, self.IB_left[m, 0] - s, self.IB_left[m, 1] - s, color='blue', lw=1.5, linestyle='dashed')

        elif not self.leftturnleadlag:
            handles.extend([line1, line2])
        axx.legend(handles=handles)
        axx.set_yticks(self.d)
        if intersection_names is None:
            axx.set_yticklabels([f'TLC_{i} - {dd} m' for i, dd in enumerate(self.d)])
        elif intersection_names is not None:
            axx.set_yticklabels([f'TLC_{intersection_names[i]} - {dd} m' for i, dd in enumerate(self.d)])
        axx.set_title('Maxband_MILP LP2')
        for i in range(max_nr_cycles + 1):
            axx.axvline(i, color='black', lw=0.3)

        return axx
