"""Zero-order-held PID sample state selected solely by an integer video frame."""
from __future__ import annotations
from bisect import bisect_right
import math
from core.mechanism.timeline import source_time_for_frame, validate_timeline, phase_playback

FIELDS = ('target_rad_s', 'error_rad_s', 'integral_state', 'derivative_rad_s2',
          'pwm_duty', 'raw_pwm', 'motor_speed_rad_s', 'encoder_speed_rad_s', 'encoder_count')


class PIDPlayback:
    def __init__(self, payload: dict, timeline: dict):
        self.rows = payload['samples']
        if not self.rows:
            raise ValueError('PID playback requires samples')
        self.times = [float(row['time_s']) for row in self.rows]
        for row in self.rows:
            if not all(math.isfinite(float(row[k])) for k in ('time_s', *FIELDS)):
                raise ValueError('PID playback samples must be finite')
            if type(row['encoder_count']) is not int:
                raise ValueError('PID encoder count must be an integer')
        if any(b <= a for a, b in zip(self.times, self.times[1:])):
            raise ValueError('PID sample times must strictly increase')
        self.gains = payload['pid']
        if not all(math.isfinite(float(self.gains[k])) for k in ('kp', 'ki', 'kd')):
            raise ValueError('PID gains must be finite')
        errors = validate_timeline(timeline, source_range=(self.times[0], self.times[-1]))
        if errors:
            raise ValueError('; '.join(errors))
        if any(p['source_start_sec'] is None for p in timeline['phases']):
            raise ValueError('PID phases require source time')
        self.timeline = timeline
        self.phases = {p['phase_id']: phase_playback(timeline, p) for p in timeline['phases']}

    def state(self, frame: int) -> dict:
        phase, source = source_time_for_frame(self.timeline, frame)
        if source is None or not math.isfinite(source) or not self.times[0]-1e-9 <= source <= self.times[-1]+1e-9:
            raise ValueError('PID source time outside trace')
        # Match the timeline's endpoint tolerance, then preserve ZOH within the trace.
        # Keep the original mapped time in debug output so tolerated drift is observable.
        sample_source = min(self.times[-1], max(self.times[0], source))
        index = max(0, min(len(self.rows)-1, bisect_right(self.times, sample_source + 1e-12)-1))
        row = self.rows[index]
        return {'frame_index': frame, 'phase_id': phase, 'presentation_time_sec': frame/self.timeline['fps'],
                'source_time_sec': source, 'sample_index': index, 'sample_time_sec': self.times[index],
                **{key: row[key] for key in FIELDS},
                'p_term': self.gains['kp']*row['error_rad_s'],
                'i_term': self.gains['ki']*row['integral_state'],
                'd_term': self.gains['kd']*row['derivative_rad_s2'],
                'playback_state': self.phases[phase]['playback_state'],
                'state_policy': 'zero_order_hold_all_recorded_values'}
