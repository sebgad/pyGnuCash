#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 19:09:55 2019

@author: sebastian
"""

from io import BytesIO
import base64
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker

class ReportItem():
    '''
    Generate a ReportItem which can be read by a JINJA2-Template in order to generate a html-Outputfile
    '''
    def __init__(self, df, title=None, showTotal=True, symbol="&euro;"):
        '''
        Initialize ReportItem - Object

        Parameter:
            title:      Title which is used in the report Item
            showTotal:  Show Total Sum Columns in Data Table on the right
            symbol:     e.g. currency symbol, displayed in the report
        '''

        self.showTotal = showTotal

        if isinstance(df, pd.DataFrame):
            self.cols = df.columns
            self.cols = ['Date'] + self.cols.tolist()
            self.df = df.reset_index()
            self.df.columns = self.cols

            if showTotal == True:
                self.showTotal = 'column'

        elif isinstance(df, pd.Series):
            self.df = pd.DataFrame(df).reset_index()
            self.cols = ['Typ', 'Amount']
            self.df.columns = self.cols

            if showTotal == True:
                self.showTotal = 'row'

        self.figsize = (23, 15)
        self.figsize = np.array(self.figsize)/2.54
        self.title = title
        self.figByteString = BytesIO()
        self.figByteString64 = None
        self.symbol = symbol
        self.plotKind = None

    def create_figure(self, kind='stackedbar', args=dict()):
        '''
        Creates a Matplotlib Fighure

        Parameters
        ----------
        kind : Plot style: stackedbar, bar and pie
        args : Matplotlib.pyplot arguments

        Returns
        -------
        None.

        '''

        self.plotKind = kind

        f, ax = plt.subplots(constrained_layout=True,
                             figsize=self.figsize)
        if kind=='stackedbar' or kind=='bar':
            if kind=='stackedbar':
                self.df.plot.bar(stacked=True,
                                 ax=ax,
                                 legend=False,
                                 x=self.cols[0])
            elif kind=='bar':
                self.df.plot.bar(stacked=False,
                                 ax=ax,
                                 legend=False,
                                 x=self.cols[0])

            plt.xticks(rotation=45)
            ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
            ax.grid(linestyle='dotted')
            ax.grid(False, which='major', axis='x' )

            ax.legend(loc='lower left',
                  bbox_to_anchor= (0.0, 1.01),
                  ncol=4,
                  borderaxespad=0,
                  frameon=False)

        elif kind=='pie':
            self.df.plot.pie(ax=ax, labels=None, x=self.cols[0], y=self.cols[1], autopct='%1.f%%')
            plt.legend(self.df[self.cols[0]].str[:] + ":" + self.df[self.cols[1]].round(2).astype(str) + "€",
                       loc='upper left',
                       bbox_to_anchor=(.88,.9))

            fsumOverall = self.df.sum()[1]
            self.df = self.df.append({'Typ': 'Total', 'Amount':fsumOverall}, ignore_index=True)

        if len(args) > 0:
            ax.set(**args)
        f.savefig(self.figByteString, format='png')
        self.figByteString64 = base64.b64encode(self.figByteString.getbuffer()).decode('ascii')
        plt.close(f)

    def ConvertForHtml(self):
        '''
        Convert Data Table descriptions (index and columns) to html conform descriptions

        Returns
        -------
        None.

        '''
        if self.showTotal in ['row']:
            self.cols = self.cols + ['Total']
            dfSum = pd.DataFrame({'Amount':self.df.sum(axis=0)}, index=['Total'])
            self.df = pd.concat([self.df, dfSum], axis=0)

        elif self.showTotal in ['column']:
            self.cols = self.cols + ['Total']
            self.df['Total'] = self.df.iloc[:,1:].sum(axis=1)

        elif self.showTotal == 'both':
            print("not implemented yet!")

        self._ConvSpecChar()

    def _ConvSpecChar(self):
        '''
        Replace Special german Characters to display it correctly in html

        Returns
        -------
        None.

        '''
        mapping = [['ä', '&auml;'],
                   ['ö', '&ouml;'],
                   ['ü', '&uuml;'],
                   ['ß', '&szlig;']]

        for mp in mapping:
            if self.df.columns.dtype == 'O':
                self.df.columns = self.df.columns.str.replace(mp[0], mp[1])

            if self.df[self.cols[0]].dtype == 'O':
                self.df[self.cols[0]] = self.df[self.cols[0]].str.replace(mp[0], mp[1])
