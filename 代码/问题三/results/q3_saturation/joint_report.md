# Q3 Performance-Saturation Search Report

- Claim: `saturated_minimum`
- Objective: `p30_all_saturation` (maximize P30(all); tie-break by P30(reachable), then smaller max delay)
- Coverage hard constraints: C1 >= 0.999, C2 >= 0.95
- Forward-window parameters: s_step=20, forward_window_s=200, max_window_gain=0.01, max_gain_per_100=0.005
- Samples: 289 times, 832 coverage points, 30 communication points
- Decision status: `saturated`
- Selected scale: S = 1680 satellites
- Window end: 1880 satellites
- Window maximum P30(all): 0.8611303344867358
- Cumulative window gain: 0.0047090641530445065
- Gain per 100 satellites: 0.0023545320765222533
