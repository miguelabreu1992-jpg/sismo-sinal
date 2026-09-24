"""TouchDesigner helper for 21-station polygon eye motion.

Paste this into a Text DAT or import it from a DAT Execute callback.
The OSC In CHOP/DAT should deliver /sismoPoligono:
  [station_index, amplitude, local_activity]
"""

import math

POLYGON_VERTICES = [
    (0.30 + 0.20 * math.cos(2 * math.pi * index / 21),
     0.50 + 0.24 * math.sin(2 * math.pi * index / 21))
    for index in range(21)
]
FREEZE_ACTIVITY = 1.0
FREEZE_SECONDS = 1.8


def handle_seismic_event(station_index, amplitude, local_activity):
    """Call this from the OSC callback when /sismoPoligono arrives."""
    component = op('/cat_visual')
    station_index = max(0, min(20, int(station_index)))
    target_x, target_y = POLYGON_VERTICES[station_index]

    if float(local_activity) > FREEZE_ACTIVITY:
        component.store('eye_freeze_until', absTime.seconds + FREEZE_SECONDS)
        component.store('eye_target_x', 0.0)
        component.store('eye_target_y', 0.0)
        component.store('eye_active_station', station_index)
        return

    component.store('eye_target_x', target_x)
    component.store('eye_target_y', target_y)
    component.store('eye_active_station', station_index)


def eye_x(offset=0.0):
    """Use this expression on a pupil Transform TOP Translate X."""
    component = op('/cat_visual')
    target = component.fetch('eye_target_x', 0.0)
    if absTime.seconds < component.fetch('eye_freeze_until', -1.0):
        target = 0.0
    return target + offset


def eye_y(offset=0.0):
    """Use this expression on a pupil Transform TOP Translate Y."""
    component = op('/cat_visual')
    target = component.fetch('eye_target_y', 0.0)
    if absTime.seconds < component.fetch('eye_freeze_until', -1.0):
        target = 0.0
    return target + offset
