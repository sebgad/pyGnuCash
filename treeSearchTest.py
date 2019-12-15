#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 20:47:03 2019

@author: sebastian
"""
from treeSearch import TreeSearch
from GnucashAcc import gnuCashAccess

path = r"/home/sebastian/Dokumente/Bank/GnuCashSoftware/Privatvermögen.db.sql.gnucash"
gnuCash = gnuCashAccess(path)   
t = gnuCash.getSplits('2550a442ee387d7550de6b9e6d61f47a')
#dfExpAccounts = groupAcc(dfSplits, dfAccounts, '2550a442ee387d7550de6b9e6d61f47a')
#tree = TreeSearch(gnuCash.dfAccounts, 'guid', 'parent_guid')

#test = tree.searchTree('5ae680287861ddff39edd8a8d48badcd', 'guid')