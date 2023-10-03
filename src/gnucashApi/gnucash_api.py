"""
API for accessing a database file from GNUcash software.

Limitation: Only SQLite database files are currently supported.

"""

import sqlite3
import datetime
import numpy as np
import pandas as pd
import jinja2
import pathlib

from .tree_search import TreeSearch
from .gnucash_report import ReportItem

class GnuCashDataAPI():
    """
    Access GnuCash created SQL-Lite File to get all transactions (splits)
    and Account names and information.
    """
    def __init__(self, database_file:str):
        """
        Initialize GnuCash API object

        Parameter:
            database_file: Local Path to GnuCash-File
        """

        # Initialize the SQLite3 Connection to the GnuCash Database
        # IMPORTANT: For using this modul, you need to save the GnuCash-File in SQLite-Format
        self.sql_connection = sqlite3.connect(database_file)

        # Get all Columns from Accounts table
        sql_string = "SELECT * FROM accounts;"
        self.df_accounts = pd.read_sql(sql_string, self.sql_connection)

        # Initialize a TreeSearch object
        self.account_tree = TreeSearch(self.df_accounts, 'guid', 'parent_guid')

        # Get guid of the root account
        str_root_acc = self._get_root_account_guid()

        # Get all Splits and in addition transaction information of the splits
        sql_string = ("SELECT t.enter_date,"
                     "t.post_date,"
                     "t.currency_guid,"
                     "t.description,"
                     "splits.value_num,"
                     "splits.value_denom,"
                     "splits.account_guid "
                     "FROM transactions as t "
                     "INNER JOIN splits ON t.guid=splits.tx_guid;")

        self.df_splits = pd.read_sql(sql_string,
                                     self.sql_connection,
                                     parse_dates=['enter_date', 'post_date'])

        self.df_splits['post_month'] = self.df_splits['post_date'].dt.strftime("%Y-%m")

        # Get Commodity information for stocks, foreign currencies, etc. and take the latest price
        sql_string = ("SELECT c.guid, "
                     "p.commodity_guid, "
                     "p.currency_guid, "
                     "p.value_num, "
                     "p.value_denom, "
                     "MAX(date(p.[date])) as date "
                     "FROM commodities c "
                     "INNER JOIN prices p "
                     "ON c.guid = p.commodity_guid "
                     "GROUP BY p.commodity_guid  "
                     f"HAVING p.currency_guid='{str_root_acc}';")

        self.df_commodities = pd.read_sql(sql_string,
                                          self.sql_connection,
                                          parse_dates={'date':"%Y-%m-%d"})

        # Join Splits and Commodities in order to convert all splits in the
        # currency of the root account
        self.df_splits = pd.merge(left=self.df_splits,
                                  right=self.df_commodities,
                                  left_on='currency_guid',
                                  right_on='commodity_guid',
                                  suffixes=('', '_commodities'),
                                  how='left')

        # All Splits that have the root currency
        idx = self.df_splits['currency_guid'] == str_root_acc

        # Calculate the price of the split
        self.df_splits['price'] = self.df_splits['value_num'] / self.df_splits['value_denom']

        # Calculate the price of the splits which are not in the root currency --> ~idx
        self.df_splits.loc[~idx, 'price'] = (self.df_splits[~idx]['value_num'] /
                                             self.df_splits[~idx]['value_denom'] *
                                             self.df_splits[~idx]['value_num_commodities'] /
                                             self.df_splits[~idx]['value_denom_commodities'])

        self._report_items = []

    def _get_root_account_guid(self)->str:
        """
        Returns the commodity guid of the the root account
        """
        # filter root account from dataframe with accounts
        idx_root_acc = ((self.df_accounts['account_type'] == "ROOT") &
                        (self.df_accounts['name'] == "Root Account"))

        str_commodity_root_acc = self.df_accounts[idx_root_acc]['commodity_guid'].values[0]

        return str_commodity_root_acc

    def get_account_guid(self, name:str)->str:
        """ get a guid for a given account name.

        Keyword Arguments:
            name:   Account name as string

        Returns a guid as string for a certain account name.
        """
        idx = self.df_accounts['name'] == name
        if idx.sum() == 1:
            return self.df_accounts[idx]['guid'].values[0]
        else:
            raise RuntimeError(f"{idx.sum()} Datasets found")

    def group_child_accounts_monthly(self, parent_guid:str, start_date:datetime.date=None,
                                     end_date:datetime.date=None)->pd.DataFrame:
        """
        Groups all (direct) child accounts for a given parent account guid. All splits will be sumed up
        (including the ones from the child accounts) monthly. Additionally the start and end date can be given for
        further filtering.

        Keyword Arguments:
            parent_guid:   String of the Parent-Account ID
            start_date:    Datetime object of the Start-Date
            end_date:      Datetime object of the End-Date

        Return:
            df_grouped: DataFrame Object where index is like "%Y-%m" and
                        columns are direct subaccounts of the specified parent_guid
        """
        # get direct child accounts for a specified parent account
        direct_children = self.account_tree.get_direct_sub_nodes(parent_guid)

        # initializing index vector for filtering dates
        idx_date_range = np.ones((len(self.df_splits),)).astype(bool)

        if start_date is not None:
            # if a start_date is given
            idx_date_range = (idx_date_range) & (self.df_splits['post_date']>=start_date)

        if end_date is not None:
            # if an end_date is given
            idx_date_range = (idx_date_range) & (self.df_splits['post_date']<=end_date)

        # Create a pandas dataframe that index contains all available month-year entries
        df_grouped = pd.DataFrame(index =
                            self.df_splits[idx_date_range]['post_month'].sort_values().unique())

        for child in direct_children:
            # iterate over all direct children and get all sub/child accounts
            lst_children = self.account_tree.get_sub_nodes(child['guid'])
            if child['placeholder'] == 0:
                # append to list if child account is not a placeholder account
                lst_children.append(child['guid'])

            # filter all splits that belong to the sub account and their children, considering also the valid
            # date range
            idx_splits = (self.df_splits['account_guid'].isin(lst_children)) & (idx_date_range)

            # Add direct child account and sum up all splits
            df_grouped[child['name']] = self.df_splits[idx_splits].groupby(by='post_month')['price'].agg('sum')

        # fill all na values with 0
        df_grouped.fillna(value=0, inplace=True)

        return df_grouped

    def get_top_accounts(self, data_frame:pd.DataFrame, top_number:int=8, sum_axis:int=1)->pd.DataFrame:
        """
        It firstly sum up all Accounts and order it accordingly. Accounts which
        have a lower Summation than the TOP-Accounts will be summed up and
        named with "others"

        Keyword Argumgents:
            data_frame:      Pandas DataFrame which shall be trimmed
            top_number:      Total Number of Accounts in the results
            axis:            Depending on data_frame the direction to sum up

        Return:
            data_frame_top:  DataFrame with the reduced ammount of Accounts
        """
        if sum_axis == 1:
            df_top_items = data_frame.sum(axis=0).sort_values(ascending=False).index
            data_frame_top = data_frame[df_top_items[:top_number]].copy()
            data_frame_top['others'] = data_frame[df_top_items[top_number:]].sum(axis=1).copy()

        elif sum_axis == 0:
            df_top_items = data_frame.sort_values(ascending=False)
            data_frame_top = df_top_items.iloc[:top_number]
            data_frame_top['others'] = df_top_items.iloc[top_number:].sum()

        data_frame_top.fillna(value=0, inplace=True)
        return data_frame_top

    def create_report_item(self, dataframe:(pd.DataFrame, pd.Series), title:str=None, show_total:bool=True,
                           symbol:str="&euro;", kind:str='stackedbar', **kwargs):
        """
        Generate a ReportItem which can be read by a JINJA2-Template in order to generate a html-Outputfile

        Keyword Arguments:
            dataframe:  Pandas DataFrame or DataSeries to display in plot
            title:      Plot title
            show_total: Adds a final column or row which is displaying the total sum
            symbol:     E.g. currency symbol, needs to be in html
            kind:       Which kind of plot, currently 'stackedbar' and 'pie' are supported
            **kwargs:   Keyword Arguments for matplotlib.pyplot.axis
        """
        report_item = ReportItem(dataframe=dataframe, title=title, show_total=show_total,
                                 symbol=symbol)
        report_item.create_figure(kind, **kwargs)
        report_item.convert_for_html()
        self._report_items.append(report_item)

    def create_report(self, time_period:str, output_file_path:str):
        """ Create a html file based on a jinja2 template

        Keyword Arguments:
            time_period:        Time period as string for the hole report, equal to report title
            output_file_path:   Ouput path for the jinja2 report as html file
        """
        template_folder = pathlib.Path(__file__).parent.joinpath("templates")
        template_loader = jinja2.FileSystemLoader(searchpath=template_folder)
        template_environment = jinja2.Environment(loader=template_loader)
        template_name = "report.template"

        template_object = template_environment.get_template(template_name)
        output = template_object.render(timePeriod=time_period, ReportItems=self._report_items)

        with open(output_file_path, 'w', encoding="utf-8") as html_file:
            html_file.write(output)
