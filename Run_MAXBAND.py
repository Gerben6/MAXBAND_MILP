import pulp as lp
import numpy as np
from typing import Tuple

class RunMaxband():

    def __init__(self, inputs):
        self.input_dict = inputs
        self.output_dict = {}

    def run_maxband(self) -> Tuple[dict, str]:
        # TODO: Create an input for the Deltas, for now they are all set to 0
        Deltas = [0, 0, 0, 0, 0, 0, 0]

        # Single inputs
        nSignals = int(self.input_dict['SingleInputs']['nsignals'])
        print(nSignals)
        nSegments = nSignals - 1
        c_min = float(self.input_dict['SingleInputs']['c_min'])
        c_max = float(self.input_dict['SingleInputs']['c_max'])
        v_min = float(self.input_dict['SingleInputs']['v_min'])/3.6  # convert km/h to m/s
        v_max = float(self.input_dict['SingleInputs']['v_max'])/3.6  # convert km/h to m/s
        inv_dv_min = float(self.input_dict['SingleInputs']['inv_dv_min'])
        inv_dv_max = float(self.input_dict['SingleInputs']['inv_dv_max'])
        k = float(self.input_dict['SingleInputs']['k'])

        # Segment inputs
        d = np.array(np.cumsum([0.0]+[float(d) for d in self.input_dict['SegmentInputs']['outbound_d']]))
        d_ = np.array(np.cumsum([0.0]+[float(d_) for d_ in self.input_dict['SegmentInputs']['inbound_d']]))

        # Signal inputs
        r = [float(r) for r in self.input_dict['SignalInputs']['outbound_r']]
        r_ = [float(r_) for r_ in self.input_dict['SignalInputs']['inbound_r']]
        l = [float(l) for l in self.input_dict['SignalInputs']['outbound_l']]
        l_ = [float(l_) for l_ in self.input_dict['SignalInputs']['inbound_l']]
        tau = [float(tau) for tau in self.input_dict['SignalInputs']['outbound_tau']]
        tau_ = [float(tau_) for tau_ in self.input_dict['SignalInputs']['inbound_tau']]

        # cstr_flags
        leftturnleadlag = self.input_dict['Selections']['leftturnleadlag']
        lt_leadlag_flag = self.input_dict['Selections']['lt_leadlag_flag']
        lt_leadlead_flag = self.input_dict['Selections']['lt_leadlead_flag']
        lt_laglag_flag = self.input_dict['Selections']['lt_laglag_flag']
        mi_mj_max_1_flag = self.input_dict['Selections']['mi_mj_max_1_flag']
        m_max_1_flag = self.input_dict['Selections']['m_max_1_flag']
        tau_cstr_flag = self.input_dict['Selections']['tau_cstr_flag']
        tau_sum_flag = self.input_dict['Selections']['tau_sum_flag']
        w_0_flag = self.input_dict['Selections']['w_0_flag']
        w_mono_flag = self.input_dict['Selections']['w_mono_flag']

        # set up the coordination problem, either maximize +b or minimize -b
        # set up the coordination problem, either maximize +b or minimize -b
        coor = lp.LpProblem('Maxband', lp.LpMaximize)

        # Declare the variables, _is used for inbound direction
        b = lp.LpVariable('b', lowBound=0, upBound=None, cat=lp.LpContinuous)  # Outbound bandwidth variable [cycles]
        b_ = lp.LpVariable('b_', lowBound=0, upBound=None, cat=lp.LpContinuous)  # Inbound bandwidth variable [cycles]
        z = lp.LpVariable('z', lowBound=0, upBound=None,
                          cat=lp.LpContinuous)  # Cycle time inverse [1/s], inverse to keep constraints linear
        t = lp.LpVariable.dicts('t', range(nSegments), lowBound=0, upBound=None,
                                cat=lp.LpContinuous)  # Outbound time [cycles] between successive intersections
        t_ = lp.LpVariable.dicts('t_', range(nSegments), lowBound=0, upBound=None,
                                 cat=lp.LpContinuous)  # Inbound time [cycles] between successive intersections
        w = lp.LpVariable.dicts('w', range(nSignals), lowBound=0, upBound=None,
                                cat=lp.LpContinuous)  # Outbound time [cycles] from red to band
        w_ = lp.LpVariable.dicts('w_', range(nSignals), lowBound=0, upBound=None,
                                 cat=lp.LpContinuous)  # Inbound time [cycles] from red to band
        m = lp.LpVariable.dicts('m', range(nSignals), lowBound=None, upBound=None,
                                cat=lp.LpInteger)  # Offset [cycles] between intersections

        if leftturnleadlag:
            delta = lp.LpVariable.dicts('delta', range(nSignals), cat=lp.LpBinary)  # Outbound left-turn order
            delta_ = lp.LpVariable.dicts('delta_', range(nSignals), cat=lp.LpBinary)  # inbound left-turn order

        # Basic Problem contraints
        # Objective function
        coor += b + k * b_, 'Maximize bandwidth'

        # Favored direction constraint
        if k != 1:
            coor += (1 - k) * b_ - (1 - k) * k * b >= 0, 'Favor bandwidth direction'
        elif k == 1:
            coor += b - b_ == 0, 'Equal bandwidths'

        # Max. and Min. cycle time constraints, 'reversed logic' since z is the inverse of C (cycle time)
        coor += c_max * z >= 1, 'Maximum cycle time'
        coor += c_min * z <= 1, 'Minimum cycle time'

        # Bandwidth constraints without requiring enough time for tau, tail of band could hit red
        if not tau_cstr_flag and not tau_sum_flag:
            for i in range(nSignals):
                coor += w[i] + b <= 1 - r[i], 'Outbound Bandwidth constraint S' + str(i)
                coor += w_[i] + b_ <= 1 - r_[i], 'Inbound Bandwidth constraint S' + str(i)

        # Min. and Max. speed constraints
        for i in range(nSegments):
            dist = d[i + 1] - d[i]
            dist_ = d_[i + 1] - d_[i]
            coor += dist * z - v_max * t[i] <= 0, 'Outbound Maximum speed A' + str(i)
            coor += -dist * z + v_min * t[i] <= 0, 'Outbound Minimum speed A' + str(i)
            coor += dist_ * z - v_max * t_[i] <= 0, 'Inbound Maximum speed A' + str(i)
            coor += -dist_ * z + v_min * t_[i] <= 0, 'Inbound Minimum speed A' + str(i)

        # Min. and Max. speed difference constraints
        for i in range(nSegments - 1):
            j = i + 1
            disti = d[i + 1] - d[i]
            distj = d[j + 1] - d[j]
            disti_ = d_[i + 1] - d_[i]
            distj_ = d_[j + 1] - d_[j]
            coor += -disti * distj * inv_dv_max * z + distj * t[i] - disti * t[
                j] <= 0, 'Outbound Max speed diff A' + str(i) + str(j)
            coor += disti * distj * inv_dv_min * z + distj * t[i] - disti * t[
                j] >= 0, 'Outbound Min speed diff A' + str(i) + str(j)
            coor += -disti_ * distj_ * inv_dv_max * z + distj_ * t_[i] - disti_ * t_[
                j] <= 0, 'Inbound Max speed diff A' + str(i) + str(j)
            coor += disti_ * distj_ * inv_dv_min * z + distj_ * t_[i] - disti_ * t_[
                j] >= 0, 'Inbound Min speed diff A' + str(i) + str(j)

        # Offset constraints
        for i in range(nSegments):
            j = i + 1
            if leftturnleadlag:
                coor += w[i] + w_[i] - w[j] - w_[j] + t[i] + t_[i] + delta[i] * l[i] - delta_[i] * l_[i] - delta[j] * l[
                    j] + delta_[j] * l_[j] - m[i] == r[j] - r[i] + tau_[i] + tau[j], 'Offset constraint A' + str(i)
            elif not leftturnleadlag:
                coor += w[i] + w_[i] - w[j] - w_[j] + t[i] + t_[i] + Deltas[i] - Deltas[j] - m[i] == 0.5 * (
                            r[j] + r_[j]) - 0.5 * (r[i] + r_[i]) + (tau_[i] + tau[j]), 'Offset constraint A' + str(i)

        # Additional constraints

        # Bandwidth constraints that require enough time for BOTH the band and queue clearance
        if tau_cstr_flag:
            for i in range(nSignals):
                coor += w[i] + b <= 1 - r[i] - tau[i], 'Outbound Bandwidth queue clearance constraint S' + str(i)
                coor += w_[i] + b_ <= 1 - r_[i], 'Inbound Bandwidth constraint S' + str(i)
                coor += w_[i] >= tau_[i], 'Inbound Bandwidth queue clearance constraint S' + str(i)

        # Bandwidth constraints that require enough time for BOTH the band and all previous queue clearances
        if tau_sum_flag:
            for i in range(nSignals):
                coor += w[i] + b <= 1 - r[i] - np.sum(tau[:i + 1]), 'Outbound Bandwidth sum tau constraint S' + str(i)
                coor += w_[i] + b_ <= 1 - r_[i], 'Inbound Bandwidth constraint S' + str(i)
                coor += w_[i] >= np.sum(tau_[:nSignals - 1 - i]), 'Inbound Bandwidth sum tau constraint S' + str(i)

        # Start band constraint requires that first second of green on first intersection is part of the band
        # Typically tau[0] = 0 (no queue clearance on the first intersection) If for some reason a more specific
        # starting time is desired, tau[0] can be specified to be any value, making it possible to start the band at
        # any specific time moment after red.
        if w_0_flag:
            coor += w[0] == tau[0], 'Outbound start band constraint'
            coor += w_[nSignals - 1] == 1 - r_[nSignals - 1] - b_, 'Inbound start band constraint'

        # Start offset constraints requires that distance from red to band be ever increasing downstream the arterial
        if w_mono_flag:
            for i in range(nSegments):
                coor += w[i] - w[i + 1] <= 0, 'Outbound increasing start offset constraint ' + str(i)
            for i in range(nSegments):
                # coor += w_[i]-w_[i+1] <= 0, 'Inbound increasing start offset constraint '+str(i)
                coor += w_[i + 1] - w_[i] >= r_[i] - r_[i + 1], 'Inbound increasing start offset constraint ' + str(i)

        # Left-turn lead/lag constraints
        # Ensures only pattern 1 or 2 is selected, so lead-lag or lag-lead and NOT pattern 3 or 4: lead-lead or lag-lag
        if lt_leadlag_flag:
            for i in range(nSignals):
                coor += delta[i] + delta_[i] == 1, 'Left-turn lead/lag S' + str(i)

        # Makes sure that only pattern 3 or 4 can be selected so lead-lead or lag-lag
        if lt_leadlead_flag:
            for i in range(nSignals):
                coor += delta[i] - delta_[i] == 0, 'Left-turn lead/lead S' + str(i)

        # Makes sure that only 4 can be selected so only lag-lag
        if lt_laglag_flag:
            for i in range(nSignals):
                coor += delta[i] + delta_[i] == 2, 'Left-turn lag/lag S' + str(i)

        # Gerbens offset constraint: Maximum 1 cycle offset between successive TLC's
        if mi_mj_max_1_flag:
            for i in range(nSegments):
                coor += m[i] + m[i + 1] <= 1, 'Gerbens offset contraint' + str(i)
        if m_max_1_flag:
            for i in range(nSignals):
                coor += m[i] <= 1, 'Gerbens offset contraint' + str(i)

        coor.solve()

        # Retracting results
        self.output_dict['OB_w'] = [w[i].value() for i in range(nSignals)]
        self.output_dict['IB_w'] = [w_[i].value() for i in range(nSignals)]
        self.output_dict['OB_t'] = [t[i].value() for i in range(nSegments)]
        self.output_dict['IB_t'] = [t_[i].value() for i in range(nSegments)]
        self.output_dict['offsets'] = [m[i].value() for i in range(nSegments)]
        self.output_dict['OB_band'] = b.value()
        self.output_dict['IB_band'] = b_.value()
        self.output_dict['inv_CT'] = z.value()
        if leftturnleadlag:
            self.output_dict['OB_delta'] = [delta[i].value() for i in range(nSignals)]
            self.output_dict['IB_delta'] = [delta_[i].value() for i in range(nSignals)]

        return self.output_dict, coor.status
