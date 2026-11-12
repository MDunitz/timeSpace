"""Decade-consistent ticks for log axes spanning many orders of magnitude.

Bokeh's default LogTicker labels every k-th decade and draws its 2x-9x minor
ticks only in the decade just below each label, leaving the other k-1 decades
bare. This ticker labels every k-th decade (k from DECADE_STEPS, chosen per
viewport) and puts a minor tick on every decade in between; once the view is
narrow enough to label every decade it switches to the 2x-9x subdivisions.
It recomputes on pan and zoom.
"""

from bokeh.models import CustomJSTicker

DESIRED_MAJOR_TICKS = 8
DECADE_STEPS = [1, 2, 3, 5, 10, 20]

_DECADES = """
const lo = Math.log10(Math.min(cb_data.start, cb_data.end))
const hi = Math.log10(Math.max(cb_data.start, cb_data.end))
const step = steps.find((k) => (hi - lo) / k <= desired) ?? steps[steps.length - 1]
const n0 = Math.ceil(lo - 1e-9)
const n1 = Math.floor(hi + 1e-9)
const lo_full = Math.floor(lo)
"""

_MAJOR_CODE = _DECADES + """
const ticks = []
for (let n = n0; n <= n1; n++) {
  if (((n % step) + step) % step === 0) ticks.push(10 ** n)
}
return ticks
"""

_MINOR_CODE = _DECADES + """
const ticks = []
for (let n = lo_full; n <= n1; n++) {
  if (step === 1) {
    for (let m = 2; m <= 9; m++) ticks.push(m * 10 ** n)
  } else if (((n % step) + step) % step !== 0) {
    ticks.push(10 ** n)
  }
}
return ticks
"""


def decade_log_ticker(desired=DESIRED_MAJOR_TICKS, steps=DECADE_STEPS):
    """Ticker with labels every k decades and a minor tick on every other decade."""
    args = dict(desired=desired, steps=list(steps))
    return CustomJSTicker(args=args, major_code=_MAJOR_CODE, minor_code=_MINOR_CODE)


def apply_decade_ticks(p, desired=DESIRED_MAJOR_TICKS):
    """Put decade-consistent tickers on both log axes of a figure."""
    for axis in (p.xaxis[0], p.yaxis[0]):
        axis.ticker = decade_log_ticker(desired=desired)
    return p
