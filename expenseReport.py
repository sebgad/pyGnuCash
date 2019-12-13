#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 11:20:29 2019

@author: sebastian
"""

import pandas as pd
import datetime as dt
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker
import jinja2
from matplotlib import rcParams
import os
from io import BytesIO
import base64

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ["Arial", 
                               "Helvetica", 
                               "sans-serif"]

class ReportItem():
    def __init__(self, df, title=None):
        self.df = df
        self.figsize = (22, 15)
        self.figsize = np.array(self.figsize)/2.54
        self.title = title
        self.figByteString = BytesIO()
    
    def create_figure(self, kind='bar', args=dict()):
        if kind=='bar':
            f, ax = plt.subplots(constrained_layout=True, 
                                 figsize=self.figsize)

            self.df.sort_index().plot.bar(stacked=True, 
                                 ax=ax,
                                 legend=False)

            if len(args) > 0:
                ax.set(**args)

            plt.xticks(rotation=45)
            ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
            ax.grid(linestyle='dotted')
            ax.grid(False, which='major', axis='x' )
            ax.legend(loc='lower left', 
                      bbox_to_anchor= (0.0, 1.01), 
                      ncol=4, 
                      borderaxespad=0, 
                      frameon=False)
            
            f.savefig(self.figByteString, format='png')
            f.close()
        
    def ConvSpecChar(self):
        mapping = [['ä', '&auml;'],
                   ['ö', '&ouml;'],
                   ['ü', '&uuml;'],
                   ['ß', '&szlig;']]
    
        for mp in mapping:
            if self.df.columns.dtype == 'O':
                self.df.columns = self.df.columns.str.replace(mp[0], mp[1])
            if self.df.index.dtype == 'int64': 
                self.df.index = self.df.index.str.replace(mp[0], mp[1])
            




expAccounts = dfAccounts[ dfAccounts['account_type']=='EXPENSE' ]

root_guid = '2550a442ee387d7550de6b9e6d61f47a'

expMainAccounts = expAccounts[ expAccounts['parent_guid'] == root_guid]

dfSplits['price'] = dfSplits.value_num / dfSplits.value_denom
dfSplits['post_month'] = dfSplits.post_date.dt.strftime("%Y-%m")

#Only Splits from the last year
today = dt.date.today()
first = today.replace(day=1)
endDate = first - dt.timedelta(days=1)
startDate = endDate - dt.timedelta(days=364)

idxDate = (dfSplits.post_date >= pd.Timestamp(startDate)) & (dfSplits.post_date<=pd.Timestamp(endDate))

#Aufwendungen pro Monat
grouped = dfSplits[idxDate].groupby(by=['post_month',
                                        'account_guid']).sum()['price'].reset_index()

merged = pd.merge(left=expAccounts,
                  right=grouped,
                  left_on="guid",
                  right_on="account_guid")

monthlyExp = pd.DataFrame(index=merged['post_month'].unique())

for index, expMainAcc in expMainAccounts.iterrows():
    if expMainAcc['placeholder'] == 0:
        idx = merged['guid'] == expMainAcc['guid']
    else:
        idx = merged['parent_guid'] == expMainAcc['guid']
    if idx.sum()>0:
        monthlyExp[expMainAcc['name']] = merged[idx].groupby(by='post_month').sum()['price']

monthlyExp.fillna(0, inplace=True)
monthlyExp.index.name = "Date"

TOP = monthlyExp.sum().sort_values().index
monthlyExpTOP = monthlyExp[TOP[-8:]]
monthlyExpTOP['others'] = monthlyExp[TOP[:-8]].sum(axis=1)


f, ax = plt.subplots(constrained_layout=True, 
                     figsize=figsize)

monthlyExpTOP.sort_index().plot.bar(stacked=True, 
                                 ax=ax,
                                 legend=False)

ax.set_ylabel('Expense [EUR]')
ax.set_xlabel('Month')
plt.xticks(rotation=45)
ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
ax.grid(linestyle='dotted')
ax.grid(False, which='major', axis='x' )
ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, 
            borderaxespad=0, frameon=False)

IMGmonthlyExp = BytesIO()
f.savefig(IMGmonthlyExp, format='png')
plt.close(f)


idxFahrtkosten = merged.parent_guid == r'5ae680287861ddff39edd8a8d48badcd'
monthlyFahrtkosten = merged[idxFahrtkosten].pivot(index="post_month", columns="name", values="price")
monthlyFahrtkosten.fillna(0, inplace=True)
monthlyFahrtkosten.index.name = "Date"

f, ax = plt.subplots(constrained_layout=True,
                     figsize=figsize)

monthlyFahrtkosten.plot.bar(stacked=True,
                          ax=ax,
                          legend=False)

ax.set_ylabel('Expense [EUR]')
ax.set_xlabel('Month')
plt.xticks(rotation=45)
ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
ax.grid(linestyle='dotted')
ax.grid(False, which='major', axis='x' )
ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, 
            borderaxespad=0, frameon=False)
IMGmonthlyTransExp = BytesIO()
f.savefig(IMGmonthlyTransExp, format='png')
plt.close(f)


f, ax = plt.subplots(constrained_layout=True,
                     figsize=figsize)

avgExp = (monthlyExp.sum()/12).clip(lower=0).round(2).sort_values(ascending=False)
avgExp.index.name = "Accounts"
avgExp.name = "Expenses"
avgExpTOP = avgExp.iloc[:8].round(2)
avgExpTOP['others'] = avgExp.iloc[8:].sum()

avgExpTOP.plot.pie(ax=ax,
                labels=None)

plt.legend(avgExpTOP.index.str[:] + ": " + avgExpTOP.round(2).astype(str) + "€",
           loc='upper left',
           bbox_to_anchor=(.9,.9))
ax.set_ylabel('Expenses')
IMGavgExp = BytesIO()
f.savefig(IMGavgExp, format='png')
plt.close(f)


incAccounts = dfAccounts[ dfAccounts['account_type']=='INCOME' ]
root_guid = 'b728ef9459c3c3bf43804322884e5438'

incMainAccounts = incAccounts[ incAccounts['parent_guid'] == root_guid]

merged = pd.merge(left=incAccounts,
                  right=grouped,
                  left_on="guid",
                  right_on="account_guid")

monthlyInc = pd.DataFrame(index=merged['post_month'].unique())

for index, incMainAcc in incMainAccounts.iterrows():
    if incMainAcc['placeholder'] == 0:
        idx = merged['guid'] == incMainAcc['guid']
    else:
        idx = merged['parent_guid'] == incMainAcc['guid']
    if idx.sum()>0:
        monthlyInc[incMainAcc['name']] = merged[idx].groupby(by='post_month').sum()['price']

monthlyInc *= -1
monthlyInc.fillna(0, inplace=True)
monthlyInc.index.name = "Date"

f, ax = plt.subplots(constrained_layout=True, 
                     figsize=figsize)

monthlyInc.sort_index().plot.bar(stacked=True, 
                                 ax=ax,
                                 legend=False)

ax.set_ylabel('Income [EUR]')
ax.set_xlabel('Month')
plt.xticks(rotation=45)
ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
ax.grid(linestyle='dotted')
ax.grid(False, which='major', axis='x' )
ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, 
            borderaxespad=0, frameon=False)
IMGmonthlyInc=BytesIO()
f.savefig(IMGmonthlyInc, format='png')
plt.close(f)

overview = pd.DataFrame()
overview['Income'] = monthlyInc.sum(axis=1)
overview['Expenses'] = monthlyExp.sum(axis=1)
overview['Balance'] = overview['Income']-overview['Expenses']

f, ax = plt.subplots(constrained_layout=True, 
                     figsize=figsize)

overview.plot.bar(stacked=False, 
                  ax=ax,
                  legend=False)

ax.set_ylabel('Amount [EUR]')
ax.set_xlabel('Month')
plt.xticks(rotation=45)
ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
ax.grid(linestyle='dotted')
ax.grid(False, which='major', axis='x' )
ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, 
            borderaxespad=0, frameon=False)
IMGoverview=BytesIO()
f.savefig(IMGoverview, format='png')
plt.close(f)

f, ax = plt.subplots(constrained_layout=True, 
                     figsize=figsize)

overview.mean().plot.bar(stacked=False, 
                  ax=ax,
                  legend=False)

ax.set_ylabel('Average Amount [EUR]')
ax.set_xlabel('Typ')
plt.xticks(rotation=45)
ax.yaxis.set_major_locator(mticker.MaxNLocator(10))
ax.grid(linestyle='dotted')
ax.grid(False, which='major', axis='x' )
ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, 
            borderaxespad=0, frameon=False)
IMGoverviewAVG=BytesIO()
f.savefig(IMGoverviewAVG, format='png')
plt.close(f)


templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "report.template"
template = templateEnv.get_template(TEMPLATE_FILE)

outputText = template.render(timePeriod=startDate.strftime("%d.%m.%Y") + " - " + endDate.strftime("%d.%m.%Y"),
                             monthlyExp=monthlyExpTOP.reset_index(),
                             IMGmonthlyExp = base64.b64encode(IMGmonthlyExp.getbuffer()).decode('ascii'),
                             monthlyTransExp=monthlyFahrtkosten.reset_index(),
                             IMGmonthlyTransExp=base64.b64encode(IMGmonthlyTransExp.getbuffer()).decode('ascii'),
                             avgExp=avgExp.reset_index(),
                             IMGavgExp = base64.b64encode(IMGavgExp.getbuffer()).decode('ascii'),
                             monthlyInc=monthlyInc.reset_index(),
                             IMGmonthlyInc=base64.b64encode(IMGmonthlyInc.getbuffer()).decode('ascii'),
                             overview=overview.reset_index(),
                             IMGoverview=base64.b64encode(IMGoverview.getbuffer()).decode('ascii'),
                             overviewAVG=overview.mean().reset_index(),
                             IMGoverviewAVG=base64.b64encode(IMGoverviewAVG.getbuffer()).decode('ascii'),
                             )

root = r"/home/sebastian/Dokumente/Bank/Financial Reports"
file = endDate.strftime("%Y%m%d") + "_PrivateFinanceReport.html" 
html_file = open(os.path.join(root, file), 'w')
html_file.write(outputText)
html_file.close()

#pdfkit.from_file(os.path.join(root, file), "output.pdf")