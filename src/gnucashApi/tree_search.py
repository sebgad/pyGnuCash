"""
Tree search module for GNUcash API. Main Function is to build a tree like structure from a flat list.
"""

import pandas

class TreeSearch():
    """
    Performs a Tree search from a flat List, where each node has an unique ID and an parent ID.

    Attributes:
        _nodes:                 Pandas Dataframes where each row is one node
        _node_id_name:          Column name of the Node ID
        _node_parent_id_name:   Column name of the Parent Node ID
        _child_lookup:          Dictionary where the key value contains the ID of the node and the value contains a
                                list of the (direct) children (only one level) below
    """
    def __init__(self, nodes:pandas.DataFrame, node_id_name:str, node_parent_id_name:str):
        """
        Class Initialization

        Keyword Arguments:
            nodes:                Pandas Dataframes where each row is one node
            node_id_name:         Column name of the NodeID, e.g. 'guid'
            node_parent_id_name:  Column name of the parent NodeID, e.g. 'parent_guid'
        """
        self._nodes = nodes
        self._node_id_name = node_id_name
        self._node_parent_id_name = node_parent_id_name
        self._child_lookup = {}

        # define Parent and Child-Lookup Dictionary for tree-Search Function. Result will be a dictionary, where
        # Keys represent Parents and values All direct children
        for _, node in self._nodes.iterrows():
            if node[self._node_parent_id_name] is not None:
                # Child node has parents, so it is not the root node
                parent_id = node[self._node_parent_id_name]

                # get all sub nodes for the given ParentID
                sub_nodes = self._child_lookup.get(parent_id)
                if not sub_nodes:
                    # When there are no sub nodes yet for the given ParentID, initialize list
                    sub_nodes = self._child_lookup[parent_id] = []
                # Append node to the given subnode
                sub_nodes.append(node.copy())

    def get_sub_nodes(self, parent_node_id:str):
        """ Returns all Sub nodes to a given ParentID.

        Keyword Arguments:
            parent_node_id:     ID of the Parent Node

        Returns all Sub nodes as list
        """
        search_list = []
        tree_search_list = self._search_tree(parent_node_id, search_list)

        return tree_search_list

    def get_direct_sub_nodes(self, parent_node_id:str):
        """ Returns only the direct sub node to a given root node.

        Keyword Arguments:
            parent_node_id:     ID of the Parent Node

        Returns all direct sub nodes as list
        """
        return self._child_lookup.get(parent_node_id)

    def _search_tree(self, parent_node_id:str, search_list=None):
        """
        Search the Tree from top node to bottom nodes and returns a list of a specified Field of
        all children of a node.

        Keyword Arguments:
            parent_node_id:     ID of the parent Node
        """

        if search_list is None:
            search_list = []

        # get all direct subnodes from a given ParentID
        sub_nodes = self._child_lookup.get(parent_node_id, [])

        if len(sub_nodes) > 0:
            # more then one sub_node is available
            for node in sub_nodes:
                # Append nodeID value to the search list
                search_list.append(node[self._node_id_name])

                # Recursive call of search tree function, to get all children to a given ParentNodeID
                self._search_tree(node[self._node_id_name], search_list)

        return search_list
