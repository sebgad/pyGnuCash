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

class gnuCashAccess():
    '''
    Access GnuCash created SQL-Lite File to get Splits and Accounts
    '''
    def __init__(self, strPath):
        '''
        Initialize GnuCash - Object
        
        Parameter:
            strPath: Local Path to GnuCash-File
        '''
        self.objCon = sqlite3.connect(strPath)
        sqlString = ("SELECT * FROM accounts;")
        
        self.dfAccounts = pd.read_sql(sqlString, self.objCon)
        self.objAccTree = TreeSearch(self.dfAccounts, 'guid', 'parent_guid')
        
        str_root_acc = self._getRootAccGuid()

        sqlString = ("SELECT t.enter_date,"
                     "t.post_date,"
                     "t.currency_guid,"
                     "t.description,"
                     "splits.value_num,"
                     "splits.value_denom,"
                     "splits.account_guid "
                     "FROM transactions as t "
                     "INNER JOIN splits ON t.guid=splits.tx_guid;")

        self.dfSplits = pd.read_sql(sqlString, 
                             self.objCon, 
                             parse_dates=['enter_date', "post_date"])
        
        self.dfSplits['post_month'] = self.dfSplits.post_date.dt.strftime("%Y-%m")
        
        sqlString = ("SELECT 	c.*, "
                     "p.commodity_guid, "
                     "p.currency_guid, "
                     "p.value_num, " 
                     "p.value_denom, "
                     "MAX(date(p.[date])) as date "
                     "FROM commodities c "
                     "INNER JOIN prices p "
                     "ON c.guid = p.commodity_guid "
                     "GROUP BY p.commodity_guid  "
                     "HAVING p.currency_guid='%s';" % str_root_acc)

        self.dfCommodities = pd.read_sql(sqlString, 
                                         self.objCon, 
                                         parse_dates={'date':"%Y-%m-%d"})
        
        self.dfSplits = pd.merge(left=self.dfSplits, 
                                 right=self.dfCommodities,
                                 left_on='currency_guid',
                                 right_on='commodity_guid',
                                 suffixes=('', '_commodities'),
                                 how='left')
        
        idx = self.dfSplits['currency_guid'] == str_root_acc
        self.dfSplits['price'] = self.dfSplits['value_num'] / self.dfSplits['value_denom']
        self.dfSplits.loc[~idx, 'price'] = (self.dfSplits[~idx]['value_num'] / 
                                            self.dfSplits[~idx]['value_denom'] * 
                                            self.dfSplits[~idx]['value_num_commodities'] / 
                                            self.dfSplits[~idx]['value_denom_commodities'])
    
    def _getRootAccGuid(self):
        '''
        '''
        idxRootAcc = ((self.dfAccounts['account_type'] == "ROOT") &
                      (self.dfAccounts['name'] == "Root Account"))
        
        strCommodityRootAcc = self.dfAccounts[idxRootAcc]['commodity_guid'].values[0]
        
        return strCommodityRootAcc
        
    
    def getAccGuid(self, name):
        idx = self.dfAccounts['name'] == name
        if idx.sum() == 1:
            return self.dfAccounts[idx]['guid'].values[0]
        else:
            raise("%s Datasets found" % idx.sum())
    
    def getSplits(self, ParentID, startDate=None, endDate=None):
        '''
        get all Splits, grouped monthly, in a specified Date Range from a specified
        Parent-Account
        
        Parameter:
            ParentID: String of the Parent-Account ID
            startDate: Datetime object of the Start-Date
            endDate: Datetime object of the End-Date
        
        Return:
            df_grouped: DataFrame Object where index is like "%Y-%m" and 
            columns are direct subaccounts of the specified ParentID
        '''
        lst_directChildren = self.objAccTree.dictChildLookup.get(ParentID)
        idxDateRng = np.ones((len(self.dfSplits),)).astype(np.bool)
        
        if startDate is not None:
            idxDateRng = (idxDateRng) & (self.dfSplits['post_date']>=startDate)
        
        if endDate is not None:
            idxDateRng = (idxDateRng) & (self.dfSplits['post_date']<=endDate)
        
        df_month_unique = pd.DataFrame(index=self.dfSplits[idxDateRng]['post_month'].sort_values().unique())
        df_grouped = pd.DataFrame(index=df_month_unique.index)
        
        for childAcc in lst_directChildren:
            lst_children = self.objAccTree.getParentChildren(childAcc['guid'], 'guid')
            if childAcc['placeholder'] == 0:
                lst_children.append(childAcc['guid'])
            
            idx = (self.dfSplits['account_guid'].isin(lst_children)) & (idxDateRng)
            
            df_grouped[childAcc['name']] = self.dfSplits[idx].groupby(by='post_month').agg('sum')['price']
        
        df_grouped.fillna(value=0, inplace=True)
        
        return df_grouped
    
    def getTOP(self, df, TOP=8, axis=1):
        '''
        Reduce the Amount of Accounts by concatenating all Accounts which
        are higher than specified by TOP. 
        
        It firstly sum up all Accounts and order it accordingly. Accounts which
        have a lower Summation than the TOP-Accounts will be summed up and 
        named with "others"
        
        Parameter:
            df: DataFrame-Account with Splits
            TOP: Total Number of Accounts in the results
            axis: Depending on df the direction to sum up
        
        Return:
            dfTOP: DataFrame with the reduced ammount of Accounts
        '''
        if axis == 1:
            TOPitems = df.sum(axis=0).sort_values(ascending=False).index
            dfTOP = df[TOPitems[:TOP]].copy()
            dfTOP['others'] = df[TOPitems[TOP:]].sum(axis=1).copy()
            
        elif axis == 0:
            dfSort = df.sort_values(ascending=False)
            dfTOP = dfSort.iloc[:TOP]
            dfTOP['others'] = dfSort.iloc[TOP:].sum()

        dfTOP.fillna(value=0, inplace=True)
        return dfTOP


