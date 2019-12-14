#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 20:47:03 2019

@author: sebastian
"""

import pandas as pd
import sqlite3
import datetime as dt
import numpy as np
from treeSearch import TreeSearch

pd.set_option('display.max_columns', 20)

path = r"/home/sebastian/Dokumente/Bank/GnuCashSoftware/Privatvermögen.db.sql.gnucash"

class gnuCashAccess():
    def __init__(self, path):
        self.objCon = sqlite3.connect(path)
        sqlString = ("SELECT * FROM accounts;")
        
        self.dfAccounts = pd.read_sql(sqlString, self.objCon)
        self.objAccTree = TreeSearch(self.dfAccounts, 'guid', 'parent_guid')

        sqlString = ("SELECT t.enter_date,"
                     "t.post_date,"
                     "splits.value_num,"
                     "splits.value_denom,"
                     "splits.account_guid "
                     "FROM transactions as t "
                     "INNER JOIN splits ON t.guid=splits.tx_guid;")

        self.Splits = pd.read_sql(sqlString, 
                             self.objCon, 
                             parse_dates=['enter_date', "post_date"])

        self.Splits['price'] = self.Splits.value_num / self.Splits.value_denom
        self.Splits['post_month'] = self.Splits.post_date.dt.strftime("%Y-%m")
        
#    def getSplitsGrouped(self, ParentAccountGuid, GroupBy, Agg, startDate=None, endDate=None):
#        mainGrp = tree.childLookup.get(ParentAccountGuid)
#        
#        idxDateRng = np.ones((len(self.Splits),)).astype(np.bool)
#        
#        if startDate is not None:
#            idxDateRng = (idxDateRng) & (self.Splits['post_date']>=startDate)
#        
#        if endDate is not None:
#            idxDateRng = (idxDateRng) & (self.Splits['post_date']<=endDate)
#        
#        dfgrouped = pd.DataFrame(index=self.Splits[idxDateRng]['post_month'].unique())
#        
#        for member in mainGrp:
#            children = tree.findChildren(member.guid)
#            if member['placeholder'] == 0:
#                children.append(member.guid)
#            
#            idx = (self.Splits['account_guid'].isin(children)) & (idxDateRng)
#            
#            dfgrouped[member['name']] = self.Splits[idx].groupby(by=GroupBy).agg(Agg)['price']
#        
#        return dfgrouped
    
    def TOP(self, df, TOP=8, axis=1):
        if axis == 1:
            TOPitems = df.sum(axis=0).sort_values(ascending=False).index
            dfTOP = df[TOPitems[:TOP]].copy()
            dfTOP['others'] = df[TOPitems[TOP:]].sum(axis=1).copy()
            return dfTOP
        elif axis == 0:
            dfSort = df.sort_values(ascending=False)
            dfTOP = dfSort.iloc[:TOP]
            dfTOP['others'] = dfSort.iloc[TOP:].sum()
            return dfTOP



