import panel as pn
import ElectraDAQLib as edl
import pandas as pd
import numpy as np
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, HoverTool, Legend
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.palettes import Set1
import itertools
palette = Set1[9]

pn.extension()

system = edl.System()
system.initialize()
system.set_write_frequency(10)
system.read_all()

temperature_instruments = [inst for inst in system.instruments if inst.measure =="Temperature"]
pressure_instruments = [inst for inst in system.instruments if inst.measure == "Pressure"]

def writers_status():
    df = pd.DataFrame({'name': [writer.name for writer in system.writers],
                       'status': [writer.status for writer in system.writers],
                       # last timestamp writer successfully wrote, with microseconds and tz removed for display
                       'last write': [writer.last_write_time.replace(microsecond=0, tzinfo=None) for writer in system.writers]})
    return df



def tag_info():
    df = pd.DataFrame({'name': [inst.tag_label for inst in system.instruments],
                       'pv': [round(inst.pv,2) for inst in system.instruments],
                       'unit': [inst.unit for inst in system.instruments]
                       }, index=[inst.tag for inst in system.instruments])
    return df

# def measure_plot(source, measure: str, labels=[], plot_width=700, plot_height=400, x_range=None):
#     colors = itertools.cycle(palette)
#     plot = figure(x_axis_label='Time', y_axis_label=measure, plot_width=plot_width, plot_height=plot_height,
#                   x_range=x_range)
#     plot.xaxis.formatter = DatetimeTickFormatter(minutes='%H:%M', seconds='%H:%M:%S')
#     plot.add_layout(Legend(), 'right')

def update():
    system.read_all()
    system.write_to_db()
    # layout[1] = system.data.iloc[-1].transpose()
    layout[1] = plots[0]
    layout[2].object = tag_info()
    layout[3].object = writers_status()
    source.data = system.data

plots = []
# plotlayout = pn.pane.Bokeh(column(temperature_plot, pressure_plot))

source = ColumnDataSource(system.data)
# print(source.data)
measures_set = set([inst.measure for inst in system.instruments])
measures = list(measures_set)

for measure in measures:
    instruments = [inst for inst in system.instruments if inst.measure == f"{measure}"]
    plot = figure(width=700, height=400, x_axis_label='Time', y_axis_label=f"{measure}")
    for inst in instruments:
        plot.line('index', inst.tag_label, source=source)
    plots.append(plot)

layout = pn.Row('hello', plots[0], tag_info(), writers_status())


pn.state.add_periodic_callback(update, period=1000)

layout.servable()
# plotlayout.servable()

