__author__ = 'aleaf'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import operator
from pst import *


class Plot(object):
    """
    Base class for assembling a plot using matplotlib

    """
    def __init__(self, data, kind=None, by=None, subplots=False, sharex=True,
                 sharey=False, use_index=True,
                 figsize=None, grid=None, legend=True, legend_title='',
                 ax=None, fig=None, title=None, xlim=None, ylim=None,
                 xticks=None, yticks=None, xlabel=None, ylabel=None, units=None,
                 sort_columns=False, fontsize=None,
                 secondary_y=False, colormap=None,
                 layout=None, **kwds):

        self.data = data
        self.by = by

        self.kind = kind

        self.sort_columns = sort_columns

        self.subplots = subplots
        self.sharex = sharex
        self.sharey = sharey
        self.figsize = figsize
        self.layout = layout

        self.xticks = xticks
        self.yticks = yticks
        self.xlim = xlim
        self.ylim = ylim
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.units = units
        self.title = title
        self.use_index = use_index

        self.fontsize = fontsize


        if grid is None:
            grid = False if secondary_y else True

        self.grid = grid
        self.legend = legend
        self.legend_title = legend_title
        self.legend_handles = []
        self.legend_labels = []

        for attr in self._pop_attributes:
            value = kwds.pop(attr, self._attr_defaults.get(attr, None))
            setattr(self, attr, value)

        self.ax = ax
        self.fig = fig
        self.axes = None

        if 'cmap' in kwds and colormap:
            raise TypeError("Only specify one of `cmap` and `colormap`.")
        elif 'cmap' in kwds:
            self.colormap = kwds.pop('cmap')
        else:
            self.colormap = colormap

        self.kwds = kwds


    def generate(self):

        self._make_plot()
        self._make_legend()



class One2onePlot(Plot):

    def __init__(self, data, x, y, groupinfo, **kwargs):

        Plot.__init__(self, data, **kwargs)
        if x is None or y is None:
            raise ValueError( 'scatter requires and x and y column')
        if pd.lib.is_integer(x) and not self.data.columns.holds_integer():
            x = self.data.columns[x]
        if pd.lib.is_integer(y) and not self.data.columns.holds_integer():
            y = self.data.columns[y]

        self.x = x
        self.y = y
        self.groupinfo = groupinfo

        # format x and y labels
        if self.xlabel is None:
            self.xlabel = str(self.x)
        if self.ylabel is None:
            self.ylabel = str(self.y)
        if self.units is not None:
            self.xlabel += ', {}'.format(self.units)
            self.ylabel += ', {}'.format(self.units)

        # dictionary supplied for groupinfo
        if isinstance(self.groupinfo, dict):
            # only attempt to plot groups that are in Res dataframe
            groups = list(set(self.groupinfo.keys()).intersection(set(self.groups)))
        # list of group names supplied
        elif isinstance(self.groupinfo, list):
            groups = self.groupinfo
            groupinfo = dict(zip(self.groupinfo, [{}] * len(self.groupinfo)))
        elif isinstance(self.groupinfo, str):
            groups = [self.groupinfo]
            groupinfo = {self.groupinfo: {}}
        else:
            raise ValueError('Invalid input for groupinfo.')

    def _make_plot(self):

        # adjustments to matplotlib defaults (can be overidden by groupinfo arguments)
        mpl.rcParams.update({'patch.linewidth': 0.25})

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)

        max, min = -999999.9, 999999.9

        color_cycle = self.ax._get_lines.color_cycle
        legend_order = {}
        knt = 0
        for grp in self.groups:

            # set keyword arguments dict and label for each group
            kwargs = self.groupinfo.get(grp, {})
            label = kwargs.get('label', grp)

            g = self.df[self.df.Group == grp.lower()]

            x, y = self.data[self.x], self.data[self.y]

            s = self.ax.scatter(x, y, **kwargs)
            legend_order[label] = s.get_zorder()

            # keep track of min/max for one2one line
            if np.max([x, y]) > max:
                max = np.max([g.Measured, g.Modelled])
            if np.min([x, y]) < min:
                min = np.min([g.Measured, g.Modelled])

        if self.legend: self._make_legend()

        #plot one2one line
        plt.plot(np.arange(min, max+1), np.arange(min, max+1), color='r', zorder=0)

        self.ax.set_ylabel()
        self.ax.set_xlabel('Measured, {}'.format(self.units))
        self.ax.set_title(self.title)
        self.ax.set_ylim(min, max)
        self.ax.set_xlim(min, max)


    def _make_legend(self):

        handles, labels = self.ax.get_legend_handles_labels()

        # weed out duplicate legend entries (from multiple PEST groups in single category)
        # enforce drawing order in legend
        u_handles, u_labels = [], []
        legend_order = sorted(self._legend_order.items(), key=operator.itemgetter(1))
        legend_order.reverse()

        for item in legend_order:
            u_handles.append([handles[i] for i, l in enumerate(labels) if l==item[0]][0])
            u_labels.append(item[0])

        lg = plt.legend(u_handles, u_labels, title=self.legend_title, loc='lower right',
                        scatterpoints=1, labelspacing=1.5, ncol=1, columnspacing=1)

        plt.setp(lg.get_title(), fontsize=12, fontweight='bold')


def plot_one2one(data, x=None, y=None, groupinfo=[], **kwds):

    plot_obj = One2onePlot(data, x, y, groupinfo, **kwds)
    plot_obj.draw()

    return plot_obj.ax