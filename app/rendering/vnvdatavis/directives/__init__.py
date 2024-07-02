from . import basic, jmes, iff, slider, forr, include, math, code
from .viz.chartsjs import chartsjs
from .viz.plotly import plotly, plotly_animation
from .viz.apex import apex, line, gauge
from .viz import charts
from .viz.tabulator import table
from .viz.terminal import terminal


def setup(sapp):


    jmes.setup(sapp)
    charts.setup(sapp)
    basic.setup(sapp)
    line.setup(sapp)
    gauge.setup(sapp)
    table.setup(sapp)
    plotly.setup(sapp)
    iff.setup(sapp)
    slider.setup(sapp)
    forr.setup(sapp)
    plotly_animation.setup(sapp)
    apex.setup(sapp)
    chartsjs.setup(sapp)
    include.setup(sapp)
    math.setup(sapp)
    code.setup(sapp)
    terminal.setup(sapp)

def get_context_map():
    return jmes.context_map