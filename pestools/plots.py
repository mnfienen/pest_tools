__author__ = 'aleaf'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
from matplotlib.colors import ListedColormap
from matplotlib.collections import PatchCollection, LineCollection
import matplotlib.lines as mlines
import operator

#from pst import *


class Plot(object):
    """
    Base class for assembling a plot using matplotlib

    This plotting structure is loosely based on pandas (albeit greatly simplified). Some of the structure may be
    to complicated for our needs, and we may want add additional functionality and shift parts of it around
    as needed. But hopefully it will provide a starting point to work off of.

    The overall goal is to centralize plotting code for consistency and to maximize extensibility

    """
    def __init__(self, df, kind=None, by=None, subplots=None, sharex=True,
                 sharey=False, use_index=True,
                 figsize=(11, 8.5), grid=None, legend=True, legend_title='',
                 ax=None, fig=None, title=None, xlim=None, ylim=None,
                 xticks=None, yticks=None, xlabel=None, ylabel=None, units=None,
                 sort_columns=False, fontsize=None,
                 secondary_y=False,
                 layout=None, **kwds):

        self.df = df
        self.by = by

        self.kind = kind

        self.sort_columns = sort_columns

        self.imagegrid = None
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

        self.ax = ax
        self.fig = fig
        self.axes = None
        self.layout = layout

        self.kwds = kwds

    def _parse_groups(self):

        # dictionary supplied for groupinfo
        if isinstance(self.groupinfo, dict):
            # only attempt to plot groups that are in Res dataframe
            self.groupinfo = dict((k.lower(), v) for k, v in self.groupinfo.iteritems())
            self.groups = list(set(self.groupinfo.keys()).intersection(set(self.groups)))

        # list or array of group names supplied
        elif isinstance(self.groupinfo, list) or isinstance(self.groupinfo, np.ndarray):
            self.groupinfo = [g.lower() for g in self.groupinfo]
            self.groups = list(set(self.groupinfo).intersection(set(self.groups)))
            self.groupinfo = dict(zip(self.groupinfo, [{}] * len(self.groupinfo)))

        elif isinstance(self.groupinfo, str):
            self.groupinfo = self.groupinfo.lower()
            self.groups = list(set([self.groupinfo]).intersection(set(self.groups)))
            self.groupinfo = {self.groupinfo: {}}

        else:
            raise ValueError('Invalid input for groupinfo.')

        if len(self.groups) == 0:
            raise IndexError('Specified groups not found in residuals file.')

    def _adorn_subplots(self):
        to_adorn = self.axes
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_xlabel(self.xlabel)
        if self.title:
            self.ax.set_title(self.title)

    def log_trans(self, x, pos):
        # Reformat tick labels out of log space
        # x : value
        # pos : position
        return '%d' % (10**x)

    def draw(self):
        plt.draw_if_interactive()

    def generate(self):

        self._initialize()
        self._make_plot()
        self._adorn_subplots()
        if self.legend:
            self._make_legend()

    def _initialize(self):

        if self.imagegrid is not None:

            from mpl_toolkits.axes_grid1 import ImageGrid

            self.fig = plt.figure(1, (4., 4.))
            self.axes = ImageGrid(self.fig, 111, nrows_ncols=self.layout, axes_pad=0.1)


        elif self.subplots is not None:
            raise AssertionError('Subplots not implemented yet.')
            # This needs some work. The main reason to use subplots instead of axes_grid1 seems to be
            # the ability to have different y-scales (e.g. for histograms, for example)
            # otherwise spatial plots and images are easier with axes_grid1
        else:
            if self.ax is None:
                # this will need to be extended to accommodate subplots
                fig = plt.figure(figsize=self.figsize)
                ax = fig.add_subplot(111)
            else:
                fig = self.ax.get_figure()
                if self.figsize is not None:
                    fig.set_size_inches(self.figsize)

            self.fig = fig
            self.axes = [ax]
            self.ax = ax

class Hist(Plot):
    """Makes a grid of histograms
    """


    def __init__(self, df, values, by, groupinfo, layout, **kwds):

        Plot.__init__(self, df, **kwds)
        """
        df : DataFrame,
            Pandas DataFrame

        values: string or int
            Column in df containing values for histogram

        groupinfo: dict, list, or string
            If string, name of group in "Group" column of df to plot. Multiple groups
            in "Group" column of df can be specified using a list. A dictionary can be used to
            specify a title and subplot number for each group.

        **kwds:
            Keyword arguments to matplotlib.pyplot.hist
        """

        self.values = values
        self.by = by
        self.groupinfo = groupinfo
        self.groups = np.unique(self.df.Group)
        self.layout = layout

        self._parse_groups()

        # need to expand this to support arbitrary labels
        self.titles = [k for k in self.groupinfo.iterkeys()]

    def _make_plot(self):

        # default keyword settings, which can be overriden by submitted keywords
        # order of priority is default, then keywords entered for whole plot,
        # then keywords supplied for individual group
        kwds = {'bins': 100., 'sharex': True}
        kwds.update(self.kwds)

        hist_df = self.df.ix[self.df.Group.isin(self.groups), [self.by, self.values]]
        self.ax = hist_df.hist(by=self.by, layout=self.layout, **kwds)

        self.fig = self.ax[0][0].get_figure()

        #for i, ax in enumerate(self.axes.ravel()):
        #    ax.set_title(self.titles[i], loc='Left', fontsize='9')

        self.fig.text(0.5, 0.02, 'Error', ha='center')
        self.fig.text(0.02, 0.5, 'Number of Observations', va='center', rotation='vertical')
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, bottom=0.15)
        '''
        for i, sp in enumerate(self.subplots):

            # get the groups for each subplot from the groupinfo dictionary
            groups = [k for k, v in self.groupinfo.iteritems() if v['subplot'] ==self.subplots[i]]
            inds = [True if g in groups else False for g in self.df.Group]
            g = self.df.ix[inds, self.values]

            g.hist(ax=self.axes[i], **kwds)

            self.axes[i].set_title(sp)
        '''

    def _make_legend(self):
        pass


class ScatterPlot(Plot):
    """Makes one-to-one plot of two dataframe columns, using pyplot.scatter"""

    def __init__(self, df, x, y, groupinfo, line_kwds={}, legend_kwds={}, **kwds):

        Plot.__init__(self, df, **kwds)
        """

        Parameters
        ----------
        df : DataFrame,
            Pandas DataFrame

        x: string or int
            Column in df containing values to plot on the x-axis

        y: string or int
            Column in df containing values to plot on the y-axis

        groupinfo: dict, list, or string
            If string, name of group in "Group" column of df to plot. Multiple groups
            in "Group" column of df can be specified using a list. A dictionary
            can be supplied to indicate the groups to plot (as keys), with item consisting of
            a dictionary of keywork arguments to Matplotlib.pyplot to customize the plotting of each group.

        line_kwds: dict, optional
            Additional keyword arguments to Matplotlib.pyplot.plot, for controlling appearance of one-to-one line.
            See http://matplotlib.org/api/pyplot_api.html

        **kwds:
            Additional keyword arguments to Matplotlib.pyplot.scatter and Matplotlib.pyplot.hexbin,
            for controlling appearance scatter or hexbin plot. Order of priority for keywords is:
                * keywords supplied in groupinfo for individual groups
                * **kwds entered for whole plot
                * default settings

            (need to figure out how to differentiate documentation with inheritance,
            and how to duplicate it in the plotting method!)
            See http://matplotlib.org/api/pyplot_api.html

        Notes
        ------

        """
        if x is None or y is None:
            raise ValueError( 'scatter requires and x and y column')
        if pd.lib.is_integer(x) and not self.df.columns.holds_integer():
            x = self.df.columns[x]
        if pd.lib.is_integer(y) and not self.df.columns.holds_integer():
            y = self.df.columns[y]

        self.x = x
        self.y = y
        self.groupinfo = groupinfo
        self.groups = np.unique(self.df.Group)
        self.line_kwds = line_kwds
        self.legend_kwds = legend_kwds
        self._legend_order = {}
        self.max, self.min = -999999.9, 999999.9

        # format x and y labels
        if self.xlabel is None:
            self.xlabel = str(self.x)
        if self.ylabel is None:
            self.ylabel = str(self.y)
        if self.units is not None:
            self.xlabel += ', {}'.format(self.units)
            self.ylabel += ', {}'.format(self.units)

        # get information on groups to plot from supplied string, list, or dict
        self._parse_groups()


class SpatialPlot(ScatterPlot):
    """Plots residuals in plan view.
    """

    def __init__(self, df, x, y, values, groupinfo,
                 colorby=None,
                 color_values=None,
                 overunder_colors=('Red', 'Navy'),
                 colorbar_label=None,
                 minimum_marker_size=10,
                 marker_scale=1,
                 legend_values=None,
                 units='',
                 legend_kwds={}, **kwds):

        ScatterPlot.__init__(self, df, x, y, groupinfo, legend_kwds=legend_kwds, **kwds)
        """
        df : DataFrame,
            Pandas DataFrame

        values: string or int
            Column in df containing values to plot spatially

        by: string
            Column in dataframe containing grouping criteria for subplots
            (one group per subplot)

        groupinfo: dict, list, or string
            If string, name of group in "Group" column of df to plot. Multiple groups
            in "Group" column of df can be specified using a list. A dictionary can be used to
            specify a title and subplot number for each group.

        layout: tuple of ints
            Specifies the layout for subplots (rows, columns).

        **kwds:
            Keyword arguments to matplotlib.pyplot.hist
        """
        self.values = values
        if color_values is None:
            self.color_values = self.values
        else:
            self.color_values = color_values

        self.scatter_df = self.df.ix[self.df.Group.isin(self.groups)]

        self.colorby = colorby
        self.overunder_colors = overunder_colors # to specify colors instead of a colormap
        self.ylabel = 'Northing'
        self.xlabel = 'Easting'
        self.cb_label = colorbar_label

        self.minimum_marker_size = minimum_marker_size
        self.marker_scale = marker_scale

        self.lg_values = np.array([])
        if legend_values is None:
            for arr in [np.array([int(np.min(self.scatter_df[self.values]))]),
                        self.scatter_df[self.values].quantile(q=[0.002, 0.023, .159, .841, .977, 0.998]).values,
                        np.array([int(np.max(self.scatter_df[self.values]))])]:
                self.lg_values = np.append(self.lg_values, arr)
        else:
            self.lg_values = np.array(legend_values)
        self.units = units


        # default keyword settings, which can be overriden by submitted keywords
        # order of priority is default, then keywords entered for whole plot,
        # then keywords supplied for individual group
        self.kwds = {'marker': 'o', 'alpha': 0.8, 'cmap': 'coolwarm', #'lw': 0,
                     'edgecolor': None, 'linewidths': 0,
                     'antialiased': True, 'zorder': 10}
        self.kwds.update(kwds)

        self.lg_kwds = {'title': 'Explanation', 'loc': 'best',
                        'borderaxespad': 0,
                        'borderpad': 1,
                        'framealpha': 0.8,
                        'scatterpoints': 1,
                        'labelspacing': 1,
                        'ncol': 1,
                        'numpoints': 1}

        self.lg_kwds.update(self.legend_kwds)

        self.cmap = cm.get_cmap(self.kwds.pop('cmap'))

    def scale_markers(self, values):

        max = np.max(np.abs(self.scatter_df[self.values]))
        scale = self.marker_scale * 200 / max
        scaled = np.abs(values) * scale

        #size = 2 + 0.75 * value
        return scaled + self.minimum_marker_size

    def add_shapefile(self, shp,
                      s=20, fc='0.8', ec='k', lw=1, alpha=1,
                      zorder=0,
                      convert_coordinates=1,
                      reset_extent=False,
                      **kwargs):
        """Add points, lines or polygons from a shapefile to the map
        """
        try:
            from shapely.ops import transform
            from descartes import PolygonPatch
            from Mapping import read_shapefile
        except:
            raise Exception("add_shapefile() method requires shapely, descartes, and fiona."
                            "\nSee the readme file for installation instructions.")

        df = read_shapefile(shp)

        if convert_coordinates != 1:
            df['geometry'] = [transform(lambda x, y, z=None: (x * convert_coordinates,
                                                              y * convert_coordinates), g)
                              for g in df.geometry]

        if 'Polygon' in df.geometry[0].type:
            print "building PatchCollection..."
            patches = []
            for i, g in enumerate(df.geometry.tolist()):
                patches.append(PolygonPatch(g, fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=zorder, **kwargs))

            collection = PatchCollection(patches, match_original=True)
            self.ax.add_collection(collection)

        elif 'LineString' in df.geometry[0].type:
            print "building LineCollection..."
            lines = []
            for i, g in enumerate(df.geometry.tolist()):
                if 'Multi' not in g.type:
                    x, y = g.xy
                    lines.append(zip(x, y))
                # plot each line in a multilinestring
                else:
                    for l in g:
                        x, y = l.xy
                        lines.append(zip(x, y))

            collection = LineCollection(lines, colors=ec, linewidths=lw, alpha=alpha, zorder=zorder, **kwargs)
            #lc.set_edgecolor(ec)
            #lc.set_alpha(alpha)
            #lc.set_lw(lw)
            self.ax.add_collection(collection)

        else:
            print "plotting points..."
            x = np.array([g.x for g in df.geometry])
            y = np.array([g.y for g in df.geometry])

            collection = self.ax.scatter(x, y, s=s, c=fc, ec=ec, lw=lw, alpha=alpha, zorder=zorder, **kwargs)

        if reset_extent:
            xmin = np.min([g.bounds[0] for g in df.geometry])
            xmax = np.max([g.bounds[2] for g in df.geometry])
            ymin = np.min([g.bounds[1] for g in df.geometry])
            ymax = np.max([g.bounds[3] for g in df.geometry])
            self.ax.set_xlim(xmin, xmax)
            self.ax.set_ylim(ymin, ymax)

        return collection

    def _make_plot(self):

        sizes = self.scale_markers(self.scatter_df[self.values])

        # parse colorscheme
        cb = False
        if self.colorby == 'graduated':
            colors = self.scatter_df[self.color_values]
            cb = True
        elif self.colorby == 'binary':
            colors = np.sign(self.scatter_df[self.color_values])
            self.cmap = ListedColormap([self.overunder_colors[1], self.overunder_colors[0]])
        elif self.colorby == 'pct_diff':
            colors = [self.scatter_df['pct_diff']]
            cb = True
            self.cb_label = 'Percent Difference'
        else:
            colors = self.colorby

        self.adjusted_cmap = Normalized_cmap(self.cmap, colors)


        self.scatter_df.plot(kind='scatter',
                             x=self.x, y=self.y, c=colors, s=sizes,
                             cmap=self.adjusted_cmap.cm, colorbar=cb, ax=self.ax,
                             layout=self.layout, **self.kwds)

        # set the colorbar label
        if self.colorby == 'graduated' or self.colorby == 'pct_diff':
            self.ax.figure.axes[1].set_ylabel(self.cb_label)

    def _make_legend(self):

        # turn off autoscaling by setting the x and ylim
        self.ax.set_xlim(self.ax.get_xlim())
        self.ax.set_ylim(self.ax.get_ylim())


        lg_values = self.lg_values
        lg_sizes = np.sqrt(self.scale_markers(lg_values)) # plt.scatter sizes are points**2
        lg_prefix = ''

        if self.colorby == 'graduated':
            lg_colors = (lg_values - lg_values[0])/float(lg_values[-1] - lg_values[0])
            lg_colors = [self.adjusted_cmap.cm(c) for c in lg_colors]
        elif self.colorby == 'pct_diff':
            lg_values = np.sort(lg_values[lg_values > 0])[::-1]
            lg_sizes = lg_sizes[lg_values > 0]
            lg_colors = ['k' for k in lg_values]
            lg_prefix = '+/-'
        elif self.colorby == 'binary':
            lg_colors = [self.adjusted_cmap.cm(c) for c in np.sign(lg_values)]
        else:
            lg_colors = [self.colorby for k in lg_values]

        lg_labels = ['{} {:,.0f} {}'.format(lg_prefix, lg_values[0], self.units)] + \
                    ['{} {:,.0f}'.format(lg_prefix, v) for v in lg_values[1:]]

        lg_handles = []
        for s in range(len(lg_sizes)):
            h = mlines.Line2D([], [], marker=self.kwds['marker'], markersize=lg_sizes[s],
                            markerfacecolor=lg_colors[s], alpha=self.kwds['alpha'],
                            markeredgecolor=None, markeredgewidth=0.25,
                            linestyle='')
            lg_handles.append(h)

        self.lg = self.ax.legend(lg_handles, lg_labels, **self.lg_kwds)

        plt.setp(self.lg.get_title(), fontsize=12, fontweight='bold')
        self.lg.set_zorder(self.kwds.get('zorder', 20))

        plt.tight_layout()


class One2onePlot(ScatterPlot):
    """Makes one-to-one plot of two dataframe columns, using pyplot.scatter"""

    def __init__(self, df, x, y, groupinfo, error_bars_obs=False, line_kwds={}, **kwds):

        ScatterPlot.__init__(self, df, x, y, groupinfo, line_kwds=line_kwds, **kwds)
        self.error_bars_obs = error_bars_obs

    def _make_plot(self):

        # use matplotlib's color cycle to plot each group as a different color by default
        color_cycle = self.ax._get_lines.color_cycle

        for grp in self.groups:

            # default keyword settings, which can be overriden by submitted keywords
            # order of priority is default, then keywords entered for whole plot,
            # then keywords supplied for individual group
            kwds = {'label': grp, 'c': next(color_cycle), 'linewidth': 0.25}
            kwds.update(self.kwds)
            kwds.update(self.groupinfo.get(grp, {}))
            label = kwds.get('label', grp)

            g = self.df[self.df.Group == grp]

            x, y = g[self.x], g[self.y]

            if self.error_bars_obs:
                s = self.ax.scatter(x, y, **kwds)
                serr = self.ax.errorbar(x,y, yerr=g.Error, ls='none',**kwds)
            else:
                s = self.ax.scatter(x, y, **kwds)
            self._legend_order[label] = s.get_zorder()

            # keep track of min/max for one2one line
            if np.max([x, y]) > self.max:
                self.max = np.max([g.Measured, g.Modelled])
            if np.min([x, y]) < self.min:
                self.min = np.min([g.Measured, g.Modelled])

        #plot one2one line
        data_range = self.max-self.min
        line_kwds = {'color': 'r', 'zorder': 0}
        line_kwds.update(self.line_kwds)
        plt.plot(np.arange(self.min-.05*data_range, self.max+.05*data_range+1),
                 np.arange(self.min-.05*data_range, self.max+.05*data_range+1), **line_kwds)
        plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)
        plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)


        self.ax.set_ylim(self.min-.05*data_range, self.max+.05*data_range)
        self.ax.set_xlim(self.min-.05*data_range, self.max+.05*data_range)

    def _make_legend(self):

        if self.legend:
            handles, labels = self.ax.get_legend_handles_labels()

            # weed out duplicate legend entries (from multiple PEST groups in single category)
            # enforce drawing order in legend
            u_handles, u_labels = [], []
            legend_order = sorted(self._legend_order.items(), key=operator.itemgetter(1))
            legend_order.reverse()

            for item in legend_order:
                u_handles.append([handles[i] for i, l in enumerate(labels) if l==item[0]][0])
                u_labels.append(item[0])

            lg = plt.legend(u_handles, u_labels, title=self.legend_title, loc='lower right', fontsize=8,
                            scatterpoints=1, labelspacing=1.5, ncol=1, columnspacing=1)

            plt.setp(lg.get_title(), fontsize=9, fontweight='bold')
            lg.set_zorder(100)


class HexbinPlot(One2onePlot):
    """Makes a hexbin plot of two dataframe columns, pyplot.hexbin"""

    def _make_plot(self):

        # overrides _make_plot() method in One2onePlot; inherits everything else
        x = self.df[self.df['Group'].isin(self.groups)]['Measured'].values
        y = self.df[self.df['Group'].isin(self.groups)]['Modelled'].values
        self.min, self.max = np.min([x, y]), np.max([x, y])

        # default keyword settings, which can be overriden by submitted keywords
        kwds = {'bins': 'log', 'mincnt': 1, 'extent': (self.min, self.max, self.min, self.max),
                'alpha': 1.0, 'edgecolors': 'none'}
        kwds.update(self.kwds)
        self.kwds = kwds

        plt.hexbin(x, y, **self.kwds)

        #plot one2one line
        line_kwds = dict(color='k', alpha=0.5, zorder=1)
        line_kwds.update(self.line_kwds)
        plt.plot(np.arange(self.min, self.max+1), np.arange(self.min, self.max+1), **line_kwds)

        #self.ax.set_ylim(np.min(y), np.max(y))
        #self.ax.set_xlim(self.min, self.max)

    def _make_legend(self):

        if self.legend:
            # put this here for now, may want to restructure later
            cb = plt.colorbar()
            if self.kwds['bins'] == 'log':
                cb.formatter = mpl.ticker.FuncFormatter(self.log_trans)
                cb.update_ticks()
                cb.set_label('Bin counts')
            else:
                cb.set_label('Bin counts')


class BarPloth(Plot):
    def __init__(self, df, values_col, group_col=None, color_dict = None, alt_labels = None, **kwargs):
        Plot.__init__(self, df, **kwargs)
        '''
        Make horizontal bar graph
        Parameters
        ----------
        df : DataFrame,
            Pandas DataFrame

        values_col: string
            Column in df containing values to plot as the length of the bars
            the 'width' parameter for matplotlib.pyplot.barh
            
        group_col : string, optional
            Column in df containing group for each value.  Will be used to color
            bars based on groups
            
        color_dict : dict, optional
            Dictionary of alternate colors for groups.  Keys are groups and values
            are colors.  Can be tuple such as (0.8, 0.1, 0.1, 1.0), or other
            standard matplotlib recognized color
            
        alt_labels : dict, optional
            Dictionary of alternative labels to use. Keys are raw PEST names.
            Values are preferred lables or descriptions
        '''
        
        self.df = df
        self.values_col = values_col
        self.group_col = group_col
        self.color_dict = color_dict
        self.alt_labels = alt_labels
        
        if self.ylabel is None:
            self.ylabel = str(self.values_col)

    def _make_plot(self, ):
        
        values = self.df[self.values_col].values
        bottom = np.arange(len(values))
        
        # Assign colors for each group
        # Will be overriden by kwds if provoded for color
        if self.group_col != None:            
            # Use provided colormap or use Set1 as default
            if 'cmap' in self.kwds:
                cmap = plt.get_cmap(self.kwds['cmap'])
                del self.kwds['cmap']
            else:
                #Default of jet is ugly
                #cmap = plt.get_cmap()
                cmap = plt.get_cmap('Set2')
            _color_dict = dict()
            unique_par_groups = np.asarray(self.df.drop_duplicates(subset = self.group_col)[self.group_col])
            for i in range(len(unique_par_groups)):
                # If color is provied for paragroup in color_dict parameter than use it               
                try:
                    _color_dict[unique_par_groups[i]] = self.color_dict[unique_par_groups[i]]
                except:
                    color = cmap(1.*i/len(unique_par_groups))
                    _color_dict[unique_par_groups[i]] = color
            
            self.colors = []
            for par_group in self.df[self.group_col].values:            
                self.colors.append(_color_dict[par_group])
        else:
            self.colors = None
            
        # default keyword settings, which can be overriden by submitted keywords
        kwds = {'align' : 'center', 'color' : self.colors}
        kwds.update(self.kwds)
        self.kwds = kwds
        
        plt.barh(bottom, values, **self.kwds)
        
        plt.ylim(-1, len(bottom))

        if self.alt_labels == None:
            plt.yticks(np.arange(len(self.df.index)), self.df.index)
        else:
            # Make sure all keys are lower
            self.alt_labels = dict((k.lower(), v) for k, v in self.alt_labels.iteritems())
            labels = []
            for label in self.df.index:
                if label in self.alt_labels:
                    labels.append(self.alt_labels[label])
                else:
                    labels.append(label)
            plt.yticks(np.arange(len(labels)), labels)

        plt.xlabel(self.xlabel)
        plt.tight_layout()

    def _make_legend(self):
        # This needs work, or maybe not needed?
        None


class HeatMap(Plot):
    def __init__(self, df,  vmin=None, vmax=None, label_rows=True, label_cols=True,
                 square=True, **kwargs):
        Plot.__init__(self, df, **kwargs)
        '''
        Heatmap of values in DataFram that represent a matrix (Cov, Cor, Eig)
        Parameters
        ----------
        df : DataFrame,
            Pandas DataFrame

        '''
        self.label_rows = label_rows
        self.label_cols = label_cols
        self.plot_data = df.values
        # Reverse the rows so the plot looks like the matrix
        self.plot_data = self.plot_data[::-1]
        self.data = df.ix[::-1]
        self.row_labels = self.data.index.values
        self.col_labels = self.data.columns.values
        self.square = square
        if vmin is None:
            self.vmin = np.min(self.plot_data)
        else:
            self.vmin = vmin
        if vmax is None:
            self.vmax = np.max(self.plot_data)
        else:
            self.vmax = vmax
        
    def _make_plot(self):
        if self.ylabel == None:
            self.ylabel = ''
        if self.xlabel == None:
            self.xlabel = ''
        
        if 'cmap' in self.kwds:
            self.cmap = plt.get_cmap(self.kwds['cmap'])
            del self.kwds['cmap']
        else:
            self.cmap = "RdBu_r"
                   
        plt.pcolormesh(self.plot_data, vmin=self.vmin, vmax=self.vmax, cmap = self.cmap, **self.kwds)
        ax = plt.gca()
        # Set ticks
        ticks = np.arange(0,len(self.row_labels),1) +0.5      
        plt.xticks(ticks)
        plt.yticks(ticks)
     
        # Remove tick marks
        for mark in ax.get_xticklines() + ax.get_yticklines():
            mark.set_markersize(0)        
        
        # Set x lables
        ax.xaxis.set_ticks_position('top')
        if self.label_cols is True:
            ax.set_xticklabels(self.col_labels, rotation="vertical")
        else:
            ax.set_xticklabels('')

        if self.label_rows is True:
            ax.set_yticklabels(self.row_labels)
        else:
            ax.set_yticklabels('')
      
        ax = plt.gca()
        # Set the axis limits
        #ax.set(xlim=(0, self.data.shape[1]), ylim=(0, self.data.shape[0]))
        if self.square == True:
            ax.set_aspect("equal")
        
        # Set up so pars and cor value show in lower left as mouse moved
        def _format_coord(x, y):
            #x = int(x + 0.5)
            #y = int(y + 0.5)
            try:
                label_row = self.row_labels[y]
                label_col = self.col_labels[x]
                return "%.3f %s | %s" % (self.plot_data[y, x], label_row, label_col)
            except IndexError:
                return ""
       
        ax.format_coord = _format_coord  
        
    def _make_legend(self):
        if self.legend:
            # put this here for now, may want to restructure later
            cb = plt.colorbar()
            cb.set_label('Parameter Correlation ')

 
class IdentBar(Plot):
    def __init__(self, ident_df, nsingular, nbars=20, **kwargs):
        Plot.__init__(self, ident_df, **kwargs)

        self.N = nsingular
        self.nbars = nbars
        self._df_Nvalues = self.df[self.df.columns[0:self.N]].copy()
        self._df_Nvalues['ident'] = self._df_Nvalues.sum(axis=1)
        self._df_Nvalues = self._df_Nvalues.sort(columns=['ident'], ascending=False)

    def _make_plot(self):
        # need to come up with a way to meaningfully plot out parameters with highest identifiabilities
        # this line plots the nbars most identifiable parameters, using eigenvectors 1 through nbars

        axmain = plt.subplot2grid((1, 15), (0, 0), colspan=13)
        b = self._df_Nvalues.ix[0:20][self._df_Nvalues.columns[:-1]].plot(ax=axmain, kind='bar', stacked=True, width=0.8, colormap='jet_r')
        b.legend_ = None
        axmain.set_ylabel('Identifiability')
        axmain.tick_params(axis='x', labelsize=6)

    def _make_legend(self):
        # make colorbar from scratch (Mike's code)
        ax1 = plt.subplot2grid((1, 15), (0, 13))
        norm = mpl.colors.Normalize(vmin=1, vmax=self.N)
        cb_bounds = np.linspace(0, self.N, self.N+1).astype(int)[1:]
        cb_axis = np.arange(0, self.N+1, int(self.N/10.0))
        cb_axis[0] = 1
        cb = mpl.colorbar.ColorbarBase(ax1, cmap=cm.jet_r, norm=norm, boundaries=cb_bounds, orientation='vertical')
        cb.set_ticks(cb_axis)
        cb.set_ticklabels(cb_axis)
        cb.set_label('Number of singular values considered')


class Normalized_cmap:

    def __init__(self, cmap, values):

        self.values = values
        self.cmap = cmap

        self.normalize_cmap()
        self.start = 0
        self.start = 1
        self.cm = self.shiftedColorMap(self.cmap, 0, self.midpoint, 1)

    def normalize_cmap(self):
        """Computes start, midpoint, and end values (between 0 and 1), to make
        a colormap using shiftedColorMap(), which will be
        * centered on zero
        * if the midpoint is > 0.5, start = 0, end is < 1
        * if the midpoint is < 0.5, the start is between 0 and 0.5, end = 1.

        Could not get this to produce a consistent midpoint color with the shiftedColorMap fn
        Using 0 and 1 for the start, stop produces a consistent midpoint color, at the cost of
        having outliers with same color intensity, regardless of their magnitudes
        """
        vmax, vmin = np.max(self.values), np.min(self.values)
        self.midpoint = 1 - vmax/(vmax + abs(vmin))
        if self.midpoint > 0.5:
            self.start, self.stop = 0, 0.5 + (1-self.midpoint)
        else:
            self.start, self.stop = 0.5 - self.midpoint, 1

    def shiftedColorMap(self, cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
        '''
        Function to offset the "center" of a colormap. Useful for
        data with a negative min and positive max and you want the
        middle of the colormap's dynamic range to be at zero. From:
        http://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib

        Input
        -----
          cmap : The matplotlib colormap to be altered
          start : Offset from lowest point in the colormap's range.
              Defaults to 0.0 (no lower ofset). Should be between
              0.0 and `midpoint`.
          midpoint : The new center of the colormap. Defaults to
              0.5 (no shift). Should be between 0.0 and 1.0. In
              general, this should be  1 - vmax/(vmax + abs(vmin))
              For example if your data range from -15.0 to +5.0 and
              you want the center of the colormap at 0.0, `midpoint`
              should be set to  1 - 5/(5 + 15)) or 0.75
          stop : Offset from highets point in the colormap's range.
              Defaults to 1.0 (no upper ofset). Should be between
              `midpoint` and 1.0.
        '''

        cdict = {
            'red': [],
            'green': [],
            'blue': [],
            'alpha': []
        }

        # regular index to compute the colors
        reg_index = np.linspace(start, stop, 257)

        # shifted index to match the data
        shift_index = np.hstack([
            np.linspace(0.0, midpoint, 128, endpoint=False),
            np.linspace(midpoint, 1.0, 129, endpoint=True)
        ])

        for ri, si in zip(reg_index, shift_index):
            r, g, b, a = cmap(ri)

            cdict['red'].append((si, r, r))
            cdict['green'].append((si, g, g))
            cdict['blue'].append((si, b, b))
            cdict['alpha'].append((si, a, a))

        newcmap = mpl.colors.LinearSegmentedColormap(name, cdict)
        plt.register_cmap(cmap=newcmap)

        return newcmap
