#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 20:46:30 2019

@author: sebastian Gade
"""

class TreeSearch():
    '''
    Performs a Tree search from a flat List, where each node has an unique
    ID and an parent ID
    

    '''
    def __init__(self, dfNodes, strNodeID, strParentNodeID, strRootID=None):
        '''
        Class Initialization
        
        Parameter:
        - dfNodes: Can be a dict or pandas Dataframes where each row is one 
          node
        - strNodeID: Field name / column Name of the Node's ID
        - strParentNodeID: Field name / column Name of the Node's Parent ID
        - strRootID: ID-String for the root Node, default: None
        '''
        self.dfNodes = dfNodes
        self.strNodeID = strNodeID
        self.strParentNodeID = strParentNodeID
        self.strRootID = strRootID
        
        # define Parent and Child-Lookup Dictionary for tree-Search Function
        self.createChildLookup()
        
    def createChildLookup(self):
        '''
        Creates a Dictionary where the key value contains the ID of the node
        and the value contains a list of the (direct) children (only one level)
        below.
        
        Return:
            - strParent: Parent Node
            - dict_ChildLookup: Dictionary of nodes with children as values
        '''
        self.dictChildLookup = dict()
        
        for index, objChild in self.dfNodes.iterrows():
            if objChild[self.strParentNodeID] is not self.strRootID:
                parent_id = objChild[self.strParentNodeID]
                lstChildren = self.dictChildLookup.get(parent_id)
                if not lstChildren:
                    lstChildren = self.dictChildLookup[parent_id] = list()
                lstChildren.append(objChild.copy())
            else:
                self.strParent = objChild.copy()
                
    def getParentChildren(self, strParentID, strFieldName):
        lstSearchTree = []
        
        lstSearchTree = self._searchTree(strParentID, strFieldName, lstSearchTree)
        
        return lstSearchTree
        
    def _searchTree(self, strParentID, strFieldName, lstSearchTree=[]):
        '''
        Search the Tree from top node to bottom nodes and returns a list 
        of a specified Field of all children of a node.
        '''
        lstChildren = self.dictChildLookup.get(strParentID, list())
        
        if len(lstChildren) > 0:
            for objChild in lstChildren:
                lstSearchTree.append(objChild[self.strNodeID])
                self._searchTree(objChild[self.strNodeID], 
                                strFieldName, 
                                lstSearchTree
                                )
                
        return lstSearchTree
        
            