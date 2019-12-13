
import pandas as pd
import sqlite3
import datetime as dt
import matplotlib
import matplotlib.pyplot as plt
import jinja2
import pdfkit
from pprint import pprint

pd.set_option('display.max_columns', 20)

path = r"/home/sebastian/Dokumente/Bank/GnuCashSoftware/Privatvermögen.db.sql.gnucash"

con = sqlite3.connect(path)

#Guid für Aufwendungen:2550a442ee387d7550de6b9e6d61f47a
sqlString = ("SELECT * FROM accounts;")

dfAccounts = pd.read_sql(sqlString, con)

sqlString = ("SELECT t.enter_date,"
             "splits.value_num,"
             "splits.value_denom,"
             "splits.account_guid, "
             "accounts.name,"
             "accounts.account_type, "
             "accounts.placeholder " 
             "FROM transactions as t "
             "INNER JOIN splits ON t.guid=splits.tx_guid "
             "INNER JOIN accounts ON splits.account_guid=accounts.guid;")

dfSplits = pd.read_sql(sqlString, 
                       con, 
                       parse_dates=['enter_date'])


#dfAccounts.rename(columns={'guid':'id', 'parent_guid':'ManagerID'}, inplace=True)
#dfAccounts['ManagerID'].iloc[0] ='aa6db7071cf4296b7dc11c5e7ea9583d'
dfAccounts = dfAccounts[~(dfAccounts.guid == r'62bbd1264c4c4cb82e83f5a27fb2c50d')]
nodes = dfAccounts[['guid', 'parent_guid', 'placeholder']].to_dict(orient='records')

#nodes = dfAccounts[['id', 'ManagerID']].to_dict(orient='records')

class treeAccounts():
    def __init__(self, flatDict, fldID, fldParentID):
        self.nameID = fldID
        self.nameParentID = fldParentID
        self.flatDict = flatDict
        self.parent, self.childLookup = self.flat2Tree()
        self.hierarchie = self.build_hierarchy(self.parent, self.childLookup)
        self.lst = []
        
    def flat2Tree(self):
        child_lookup = dict()
        for child in self.flatDict:
            if child["parent_guid"] is not None:
                parent_id = child["parent_guid"]
                children = child_lookup.get(parent_id)
                if not children:
                    children = child_lookup[parent_id] = list()
                children.append(child.copy())
            else:
                parent = child.copy()
        return parent, child_lookup

    def build_hierarchy(self, parent, childLookup):
        children = childLookup.get(parent["guid"], list())
        for child in children:
            self.build_hierarchy(child, childLookup)
        if children:
            parent['children'] = children
        else:   
            parent['children'] = None
        return parent
    
    def _finditem(self, obj, key):
        if key in obj[self.nameID]: return obj['children']
        for k, v in obj.items():
            if isinstance(v,list):
                for list_item in v:
                    item = self._finditem(list_item, key)
                    if item is not None:
                        return item
    
    def _childs2List(self, obj, accList=[]):
#        if obj['children'] is None: accList.append(obj['guid'])
        if isinstance(obj['children'], list):
            for list_item in obj['children']:
                if list_item['children'] is not None:
                    item = self._childs2List(list_item)
                    return item
                else:
                    accList.append(obj['guid'])
            
        return accList
    
    def _flatlist(self, rootkey):
        children = self._finditem(self.hierarchie, rootkey)    
        accList = []
        
        for child in children:
            accList.extend(self._childs2List(child))
        
        return accList
                
                
        
#        elif obj['children'] is None:
#            guilst.append(obj['guid'])
            
#            return self.guilst
            
#            return item
        
#        return obj['children']
#                if item is not None:
#                    return item
#        for k, v in children.items():
            
#            for list_item in v:
#                item = self._childs2List(list_item['children'])
#                if item is not None:
#                    return item
        

tree = treeAccounts(nodes, "guid", "parent_guid")
children = tree._finditem(tree.hierarchie, r"2550a442ee387d7550de6b9e6d61f47a")
acc = tree._childs2List(children[1])
#acc = tree._flatlist(r"2550a442ee387d7550de6b9e6d61f47a")
#employees = [
#    {"id": 0, "job": "CEO", "ManagerID": 0, "name": "John Smith"},
#    {"id": 1, "job": "Medical Manager", "ManagerID": 0, "name": "Medic 1"},
#    {"id": 2, "job": "Medical Assist", "ManagerID": 1, "name": "Medic 2"},
#    {"id": 3, "job": "ICT Manager", "ManagerID": 0, "name": "ICT 1"},
#    {"id": 4, "job": "ICT Assist", "ManagerID": 3, "name": "ICT 2"},
#    {"id": 5, "job": "ICT Junior", "ManagerID": 4, "name": "ICT 3"}
#]

#parent, child_lookup = to_lookup(nodes)
#hierarchy = build_hierarchy(parent, child_lookup)


#def pop_list(nodes=None, parent=None, node_list=[]):
#    if parent == r'aa6db7071cf4296b7dc11c5e7ea9583d':
#        return node_list
#    for node in nodes:
#        if node['parent_guid'] == parent:
#            node_list.append(node['guid'])
#            next_parent = node['guid']
#            pop_list(nodes, next_parent, node_list)
#    
#    return node_list

#idxExpenses = dfAccounts.parent_guid == r"2550a442ee387d7550de6b9e6d61f47a"
#
#for index, expense in dfAccounts[idxExpenses].iterrows():
#    node_list = []
#    sumList = pop_list(nodes, expense.guid)
#    sumExpense = 0
#    print(expense.guid)
#    print(sumList)
#    print("\n\n")
    




#Main Accounts
#idx = df['parent_guid'] == '2550a442ee387d7550de6b9e6d61f47a'

#for index, MainAcc in df[idx].iterrows():
#   idxChilds = df[~idx]['parent_guid'] == MainAcc['guid']
    
    

#df['price'] = df.value_num / df.value_denom
#
#today = dt.date.today()
#first = today.replace(day=1)
#endDate = first - dt.timedelta(days=1)
#startDate = endDate - dt.timedelta(days=364)
#
#idxDate = (df.enter_date >= pd.Timestamp(startDate)) & (df.enter_date<=pd.Timestamp(endDate))
#idxAccType = df.account_type == "EXPENSE"
#
#templateLoader = jinja2.FileSystemLoader(searchpath="./")
#templateEnv = jinja2.Environment(loader=templateLoader)
#TEMPLATE_FILE = "report.template"
#template = templateEnv.get_template(TEMPLATE_FILE)
#
#dfSeries = df[idxDate & idxAccType].groupby("name").agg('sum')['price']/ 365*30.5
#dfSeries = pd.DataFrame(dfSeries).reset_index()
#
#f, ax = plt.subplots(constrained_layout=True, 
#                     figsize=(16,8))
#
#dfSeries.sort_values(by="price").plot.barh(x='name', ax=ax)
#
#f.savefig('out.svg')
#
#outputText = template.render(df=dfSeries,
#                             timePeriod=startDate.strftime("%d.%m.%Y") + " - " + endDate.strftime("%d.%m.%y"),
#                             produced_services_plot='out.svg')
#html_file = open('output.html', 'w')
#html_file.write(outputText)
#html_file.close()

#pdfkit.from_file("output.html", "output.pdf")




