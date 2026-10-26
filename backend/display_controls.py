"""Values supported by the virtual phone's Android display controls."""
import math


def font_scale(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Text size must be a finite number')
    return round(max(.85, min(1.5, number)), 2)
