#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 11:20:29 2019

@author: sebastian
"""

import pandas as pd
import datetime as dt
import jinja2
from matplotlib import rcParams
import os
from Reportitem import ReportItem
from GnucashAcc import gnuCashAccess

path = r"/home/sebastian/Dokumente/Documents@Sebastian/Bank/GnuCashSoftware/Privatvermögen.db.sql.gnucash"
gnuCash = gnuCashAccess(path)     

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ["Arial", 
                               "Helvetica", 
                               "sans-serif"]


            
ReportItems = []

# Get only the Splits until one year ahead from last month
today = dt.datetime.today()
first = today.replace(day=1, hour=23, minute=59, second=59)
endDate = first - dt.timedelta(days=1)
startDate = endDate.replace(hour=0, minute=0, second=0) - dt.timedelta(days=365)

# Get Monthly Expenses
monthlyExp = gnuCash.getSplits(ParentID='2550a442ee387d7550de6b9e6d61f47a',
                               startDate=startDate,
                               endDate=endDate)

monthlyExpTOP = gnuCash.getTOP(monthlyExp)
monthlyRepItem = ReportItem(monthlyExpTOP, "Monthly Expenses")

monthlyRepItem.create_figure(kind='stackedbar',
                             args={'ylabel':'Expense [EUR]',
                                   'xlabel':'Month'})
monthlyRepItem.ConvertForHtml()

ReportItems.append(monthlyRepItem)

# Get Monthly Costs for Cars
monthlyFahrtkosten = gnuCash.getSplits(ParentID=r'1542bb4cdae5b30b21ee37aecc0fdd41',
                                       startDate=startDate,
                                       endDate=endDate)

monthlyFahrtRepItem = ReportItem(monthlyFahrtkosten, "Monthly Expenses for Vehicles")
monthlyFahrtRepItem.create_figure(kind='stackedbar',
                                  args={'ylabel':'Expense [EUR]',
                                        'xlabel':'Month'})
monthlyFahrtRepItem.ConvertForHtml()
ReportItems.append(monthlyFahrtRepItem)

# Get yearly averaged Expenses
avgMonthlyExp = (monthlyExp.mean()).clip(lower=0).sort_values(ascending=False)
avgMonthlyExpTOP = gnuCash.getTOP(avgMonthlyExp, axis=0)
AVGmonthlyRepItem = ReportItem(avgMonthlyExpTOP, 
                               "Yearly Averaged monthly Expenses",
                               showTotal=False)
AVGmonthlyRepItem.create_figure(kind='pie',
                                )

ReportItems.append(AVGmonthlyRepItem)

# Get the two highest Cost accounts
TOP1Exp = gnuCash.getSplits(gnuCash.getAccGuid(avgMonthlyExpTOP.index[0]),
                            startDate=startDate,
                            endDate=endDate).mean()

TOP1RepItem = ReportItem(TOP1Exp, "TOP1 highest Expense Account: " + avgMonthlyExpTOP.index[0],
                         showTotal=False)
TOP1RepItem.create_figure(kind='pie')
ReportItems.append(TOP1RepItem)

TOP2Exp = gnuCash.getSplits(gnuCash.getAccGuid(avgMonthlyExpTOP.index[1]),
                            startDate=startDate,
                            endDate=endDate).mean()

TOP2RepItem = ReportItem(TOP2Exp, "TOP2 highest Expense Account: " + avgMonthlyExpTOP.index[1],
                         showTotal=False)
TOP2RepItem.create_figure(kind='pie')
ReportItems.append(TOP2RepItem)


# Get Yearly Income
monthlyInc = gnuCash.getSplits(ParentID='b728ef9459c3c3bf43804322884e5438',
                               startDate=startDate,
                               endDate=endDate)

monthlyInc *= -1
monthlyIncRepItem = ReportItem(monthlyInc, "Monthly Income")

monthlyIncRepItem.create_figure(kind='stackedbar',
                             args={'ylabel':'Income [EUR]',
                                   'xlabel':'Month'})
monthlyIncRepItem.ConvertForHtml()

ReportItems.append(monthlyIncRepItem)


# Balance Accounts
overview = pd.DataFrame()
overview['Income'] = monthlyInc.sum(axis=1)
overview['Expenses'] = monthlyExp.sum(axis=1)
overview['Balance'] = overview['Income']-overview['Expenses']

monthlyOvRepItem = ReportItem(overview, "Account Balance", showTotal=False)
monthlyOvRepItem.create_figure(kind='bar',
                               args={'ylabel':'Amount [EUR]',
                                   'xlabel':'Month'})
monthlyOvRepItem.ConvertForHtml()
ReportItems.append(monthlyOvRepItem)

# Average Balance
mean_overview = overview.mean()
monthlyOvAVGRepItem = ReportItem(mean_overview, "AVG Account Balance", showTotal=False)
monthlyOvAVGRepItem.create_figure(kind='bar',
                                  args={'ylabel':'Average Amount [EUR]',
                                        'xlabel':'Typ'})
ReportItems.append(monthlyOvAVGRepItem)


# Cummulated Stacked Assets
monthlyAssets = gnuCash.getSplits(ParentID="e94985e1c61e0169ef59236dcb9bc683").cumsum()
idx = (monthlyAssets.index >= startDate.strftime("%Y-%m")) & (monthlyAssets.index <= endDate.strftime("%Y-%m"))

monthlyAssetsRepItem = ReportItem(monthlyAssets[idx], "Cummulated Assets", showTotal=True)
monthlyAssetsRepItem.create_figure(kind='stackedbar',
                                  args={'ylabel':'Cummulated Assets [EUR]',
                                        'xlabel':'Month'})
monthlyAssetsRepItem.ConvertForHtml()
ReportItems.append(monthlyAssetsRepItem)


templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "report.template"
template = templateEnv.get_template(TEMPLATE_FILE)
outputText = template.render(timePeriod=startDate.strftime("%d.%m.%Y") +" - " \
                             + endDate.strftime("%d.%m.%Y"),
                             ReportItems=ReportItems)

#
root = r"/home/sebastian"
file = endDate.strftime("%Y%m%d") + "_PrivateFinanceReport.html" 
html_file = open(os.path.join(root, file), 'w')
html_file.write(outputText)
html_file.close()
