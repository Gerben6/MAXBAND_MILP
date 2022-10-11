import tkinter as tk
from tkinter import ttk


tooltips = {
    'nsignals': 'The number of intersection in the arterial. Must be greater than 2 and less than or equal to 10.',
    'c_min': 'The minimum value of the cycle time in seconds.',
    'c_max': 'The maximum value of the cycle time in seconds.',
    'v_min': 'The minimum segment speed in kilometres per hour.',
    'v_max': 'The maximum segment speed in kilometres per hour.',
    'inv_dv_min': 'Lower limit (becomes negative) on the change in reciprocal speed between subsequent segments '
                  '(1/-inv_dv_min < 1/vi - 1/vj) [m/s]^-1.',
    'inv_dv_max': 'Upper limit on the change in reciprocal speed between subsequent segments '
                  '(1/vi - 1/vj < 1/inv_dv_max)  [m/s]^-1.',
    'k': 'Factor for a band target ratio. The inbound band is given k times as much weight as the outbound band. '
         'So to favor outbound: (0 <= k < 1) or inbound (1 < k < inf) direction. k = 1 enforces equal bandwidths.',
    'outbound_d': 'Distances of the segments in the outbound direction in meters.',
    'inbound_d': 'Distances of the segments in the inbound direction in meters. Note that the origin is the same so '
                 'either the inbound, or the outbound distances have to be specified in reverse.',
    'outbound_r': 'Fraction of the cycle unavailable for the outbound band [cycles].',
    'inbound_r': 'Fraction of the cycle unavailable for the inbound band [cycles].',
    'outbound_l': 'Fraction of the cycle needed for the outbound left-turn [cycles]. Must be greater than the '
                  'inbound red time of the same signal.',
    'inbound_l': 'Fraction of the cycle needed for the inbound left-turn [cycles]. Must be greater than the '
                  'outbound red time of the same signal.',
    'outbound_tau': 'Fraction of the cycle needed for outbound queue-clearance time [cycles].',
    'inbound_tau': 'Fraction of the cycle needed for inbound queue-clearance time [cycles].',
    'leftturnleadlag': 'Enables the optimization of left-turn locations',
    'lt_leadlag_flag': 'Restricts the left-turn patterns to only lead-lag or lag-lead.',
    'lt_leadlead_flag': 'Restricts the left-turn patterns to only lead-lead or lag-lag.',
    'lt_laglag_flag': 'Restricts the left-turn patterns to only lag-lag.',
    'mi_mj_max_1_flag': 'Forces that any 2 subsequent segments be offset by at most 1 cycle',
    'm_max_1_flag': 'Forces that each segment be offset by at most 1 cycle.',
    'tau_cstr_flag': 'Requires that the downstream intersection provide enough bandwidth for the queue clearance time '
                     'of the first upstream intersection',
    'tau_sum_flag': 'Requires that the downstream intersection provide enough bandwidth for the queue clearance time '
                     'of all previous upstream intersections',
    'w_0_flag': 'Requires that the start of green at the first intersection of the arterial is part of the band.',
    'w_mono_flag': 'Restricts distance from the end of red to the start of the band to only be allowed to increase '
                   'when heading downstream the arterial'
}


class ToolTip(object):

    def __init__(self, widget):
        self.text = None
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        """Display text in tooltip window"""
        self.text = text
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = ttk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                          font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def create_tooltip(widget, text):
    tooltip = ToolTip(widget)

    def enter(event):
        tooltip.showtip(text)

    def leave(event):
        tooltip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
