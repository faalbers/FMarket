import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from pandas import test
from pyparsing import line
import seaborn as sns
import pandas as pd
import numpy as np

class Plot:
    def __init__(self,
            size=[1,1],
            figsize=(10, 8),
            dpi=100,
            width_ratios    = [1.0],
            height_ratios   = [1.0],
            reset_index     = False,
            grid            = 'weekly',
            annotate        = True,
            sharex          = True,
            sharey          = True,
            ):
        self.size = size
        self.width_ratios = width_ratios
        self.height_ratios = height_ratios
        self.reset_index = reset_index
        self.grid = grid
        self.annotate = annotate
        
        # set for color blind
        plt.style.use('tableau-colorblind10')

        # make sure ratios are correct
        if size[0] != len(self.height_ratios):
            self.height_ratios = [1.0] * size[0]
        if size[1] != len(self.width_ratios):
            self.width_ratios = [1.0] * size[1]

        self.__fig, self.__axs = plt.subplots(
            self.size[0],
            self.size[1], 
            gridspec_kw={
                'height_ratios': self.height_ratios,
                'width_ratios': self.width_ratios},
                sharex=sharex,
                sharey=sharey,
                figsize=figsize,
                dpi=dpi,
                )

    def plot(self, df, position=(0,0), title=None, ylabel=None, alpha=1.0):
        ax = self.__get_axis(position)

        # reset indices if needed
        if self.reset_index:
            df = df.copy()
            df.reset_index(inplace=True, drop=True)
        
        for column in df.columns:
            ax.plot(df.index, df[column], label=column, alpha=alpha)

        if  title and not ax.get_title(): ax.set_title(title)
        if  ylabel and not ax.get_ylabel(): ax.set_ylabel(ylabel, fontweight='bold')
    
    def scatter(self, df, position=(0,0), title=None, size=20, alpha=1.0):
        ax = self.__get_axis(position)

        # reset indices if needed
        if self.reset_index:
            df = df.copy()
            df.reset_index(inplace=True, drop=True)
        
        # sns.scatterplot(data = df, ax=ax, s=size, alpha=alpha)
        for column in df.columns:
            ax.scatter(df.index, df[column], label=column, s=size, alpha=alpha)
        
        if  not ax.get_title() and title: ax.set_title(title)

    def pie(self, s, position=(0,0), title=None):
        ax = self.__get_axis(position)
        # ax.pie(s.values, labels=s.index, autopct="%1.1f%%", startangle=90)
        total = s.sum()
        wedges, texts, autotexts = ax.pie(
            s.values,
            # labels=s.index,
            autopct=lambda pct: f"{pct:.1f}%",
            # autopct=lambda pct: '%.2f%% \n$ %.2f' % (pct, pct * total / 100),
            textprops={
                "fontsize": 8,
                "color": "white"
            },
            startangle=90,
            # labeldistance=0.55,   # move labels inside
            # pctdistance=0.75      # move percentages inside
            )
        ax.legend(
            wedges,
            ['%s: %.2f' % (label, value) for label, value in s.items()],
            title="Holdings",
            bbox_to_anchor=(1, 1),
            )
        ax.axis('off')
        ax.set_position([-0.2, 0.0, 1.0, 1.0])

        if  not ax.get_title() and title: ax.set_title(title)

    def show(self):
        self.__finnish_plot()
        plt.show()

    def fig(self):
        self.__finnish_plot()
        return self.__fig
    
    def __finnish_plot(self):
        # add axis settings
        if isinstance(self.__axs, np.ndarray):
            for row in self.__axs:
                if len(self.__axs.shape) == 2:
                    for column in row:
                        self.__axis_settings(column)
                else:
                    self.__axis_settings(row)
        else:
            self.__axis_settings(self.__axs)

        # plt.tight_layout()

    def __axis_settings(self, ax):
        # set grid
        if self.reset_index:
            grid_major = 7*5*4
            grid_minor = 7*5
            ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major))
            ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor))
            ax.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major', alpha=0.7)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor', alpha=0.5)
        else:
            if self.grid == 'weekly':
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
            elif self.grid == 'monthly':
                ax.xaxis.set_major_locator(mdates.YearLocator())
                ax.xaxis.set_minor_locator(mdates.MonthLocator())
                ax.xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: mdates.num2date(x).strftime("%b")[0])
)
            ax.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major', alpha=0.7)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor', alpha=0.5)
        
        # set annotate
        if self.annotate:
            for child in ax.get_children():
                label = child.get_label()
                if isinstance(child, mpl.lines.Line2D):
                    color = child.get_color()
                    annotate_x = child.get_data()[0][-1]
                    annotate_y = child.get_data()[1][-1]
                    ax.annotate(label, xy=(annotate_x, annotate_y),
                        fontsize=8, fontweight='bold', xytext=(2, 0), textcoords='offset points', color=color)
                if isinstance(child, mpl.collections.PathCollection):
                    color = child.get_facecolor()[0]
                    points = child.get_offsets()
                    points = points.filled(np.nan)
                    points = points[~np.isnan(points).any(axis=1)]
                    annotate_x = points[-1][0]
                    annotate_y = points[-1][1]
                    ax.annotate(label, xy=(annotate_x, annotate_y),
                        fontsize=8, fontweight='bold', xytext=(2, 0), textcoords='offset points', color=color)
        else:
            ax.legend().set_visible(True)
    
    def __get_axis(self, position=(0,0)):
        if isinstance(self.__axs, np.ndarray):
            if len(self.__axs.shape) == 2:
                return self.__axs[position]
            else:
                return self.__axs[position[0]]
        else:
            return self.__axs
