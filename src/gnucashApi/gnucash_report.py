"""
Report Creation Module for GNUcash, to generate html reports.
"""

from io import BytesIO
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

class ReportItem():
    """
    Generate a ReportItem which can be read by a JINJA2-Template in order to generate a html-Outputfile

    Attributes:
        show_total:         Show Total Sum Columns in Data Table on the rights
        cols:               Column Names
        data_frame:         Pandas DataFrame object which contains the data for the plot
        figsize:            Figure Size
        title:              Title for Report item
        fig_byte_string:    Byte String for the Matplotlib figure to directly store it in the html file
        fig_byte_string64:  64 Byte representation of the Matplotlib figure output file
        symbol:             E.g. Currency Symbol
        plot_kind:          Plot kind for the Pandas DataFrame Plot
    """
    def __init__(self, dataframe:(pd.DataFrame, pd.Series), title=None, show_total=True, symbol="&euro;"):
        """
        Initialize ReportItem - Object

        Keyword Arguments:
            dataframe:  Pandas DataFrame or Series as database for the plot
            title:      Title which is used in the report Item
            showTotal:  Show Total Sum Columns in Data Table on the right
            symbol:     e.g. currency symbol, displayed in the report
        """

        self.show_total = show_total

        if isinstance(dataframe, pd.DataFrame):
            self.cols = dataframe.columns
            self.cols = ['Date'] + self.cols.tolist()
            self.data_frame = dataframe.reset_index()
            self.data_frame.columns = self.cols

            if show_total is True:
                self.show_total = 'column'

        elif isinstance(dataframe, pd.Series):
            self.data_frame = pd.DataFrame(dataframe).reset_index()
            self.cols = ['Typ', 'Amount']
            self.data_frame.columns = self.cols

            if show_total is True:
                self.show_total = 'row'

        self.figsize = (23, 15)
        self.figsize = np.array(self.figsize)/2.54
        self.title = title
        self.fig_byte_string = BytesIO()
        self.fig_byte_string64 = None
        self.symbol = symbol
        self.plot_kind = None

    def create_figure(self, kind='stackedbar', **kwargs):
        """
        Creates a Matplotlib Fighure

        Keyword Arguments:
            kind :      Plot style: stackedbar, bar and pie
            kwargs:     Matplotlib.pyplot arguments
        """
        self.plot_kind = kind

        figure, plot_axis = plt.subplots(constrained_layout=True, figsize=self.figsize)

        if kind in ['stackedbar', 'bar']:
            if kind=='stackedbar':
                self.data_frame.plot.bar(stacked=True, ax=plot_axis, legend=False, x=self.cols[0])
            elif kind=='bar':
                self.data_frame.plot.bar(stacked=False, ax=plot_axis, legend=False, x=self.cols[0])

            plt.xticks(rotation=45)
            plot_axis.yaxis.set_major_locator(mticker.MaxNLocator(10))
            plot_axis.grid(linestyle='dotted')
            plot_axis.grid(False, which='major', axis='x' )

            plot_axis.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False)

        elif kind=='pie':
            self.data_frame.plot.pie(ax=plot_axis, labels=None, x=self.cols[0], y=self.cols[1], autopct='%1.f%%')
            plt.legend(self.data_frame[self.cols[0]].str[:] + ":" + self.data_frame[self.cols[1]].round(2).astype(str) \
                       + "€", loc='upper left', bbox_to_anchor=(.88,.9))

            sum_overall = self.data_frame.sum()[1]
            self.data_frame = self.data_frame.append({'Typ': 'Total', 'Amount':sum_overall}, ignore_index=True)

        plot_axis.set(**kwargs)
        figure.savefig(self.fig_byte_string, format='png')
        self.fig_byte_string64 = base64.b64encode(self.fig_byte_string.getbuffer()).decode('ascii')
        plt.close(figure)

    def convert_for_html(self):
        """
        Convert Data Table descriptions (index and columns) to html conform descriptions
        """
        if self.show_total in ['row']:
            # Add Total row to the Pandas DataFrame
            self.cols = self.cols + ['Total']
            data_frame_sum = pd.DataFrame({'Amount':self.data_frame.sum(axis=0)}, index=['Total'])
            self.data_frame = pd.concat([self.data_frame, data_frame_sum], axis=0)

        elif self.show_total in ['column']:
            # Add Total column to the Pandas DataFrame
            self.cols = self.cols + ['Total']
            self.data_frame['Total'] = self.data_frame.iloc[:,1:].sum(axis=1)

        elif self.show_total == 'both':
            print("not implemented yet!")

        self._escape_html_chars()

    def _escape_html_chars(self):
        """ Replace Special german Characters to display it correctly in html """
        mappings = [['ä', '&auml;'],
                   ['ö', '&ouml;'],
                   ['ü', '&uuml;'],
                   ['ß', '&szlig;']]

        for mapping in mappings:
            if self.data_frame.columns.dtype == 'O':
                self.data_frame.columns = self.data_frame.columns.str.replace(mapping[0], mapping[1])

            if self.data_frame[self.cols[0]].dtype == 'O':
                self.data_frame[self.cols[0]] = self.data_frame[self.cols[0]].str.replace(mapping[0], mapping[1])
