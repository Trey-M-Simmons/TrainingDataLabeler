from pathlib import Path
import pandas as pd
import numpy as np
import os
import PIL
import math
import copy

#an item is some image or video that needs to be labeled and is contained inside of a group
class Item:
    def __init__(self, fileName = "unknown.unknown", directory = "."):
        self.fileName = fileName
        self.fileType = Path(fileName).suffix
        self.directory = directory
        self.itemNum = -1

#A group is a node of a tree where each group holds a list of items and a list of child groups
class Group:
    def __init__(self, items = None, subjects = [], creator = [], collection = -1, tags = [], page = 0, parent = None):
        
        if(items == None):
            items = []
        #items inside of this node
        self.items = items

        #labeling/description of the items in this group
        self.subjects = subjects
        self.creator = creator
        self.collection = collection # -1 means it is NOT a part of a collection
        self.tags = tags
        self.page = page #used for things like books or comic panels

        self.parent = parent #if this group is the root of the tree, parent will be None
        self.childGroups = []

        #determines if this is a new group or one pulled from the database, if new = -1
        self.groupNum = -1
    
    ###### Child Group methods ######
    #all new child groups will be initialized with the current groups labeling
    def createChildGroup(self):
        newGroup = Group([], copy.deepcopy(self.subjects), copy.deepcopy(self.creator), self.collection, copy.deepcopy(self.tags), self.page, self)
        self.childGroups.append(newGroup)

    #moves a child group to a different pos in the list
    def moveChild(self, movingIndex, moveToIndex):
        self.childGroups.insert(movingIndex, moveToIndex)
        self.childGroups.remove(movingIndex)
    
    #deleted child groups items will be added back to parent
    def deleteChild(self, childGroup):
       #if(childGroup in self.childGroups):
            #add the deleted child group's own children groups to the parent
            self.childGroups += childGroup.childGroups
            #add the deleted child group's items to the parents items
            self.items += childGroup.items
            #actually delete the child group
            self.childGroups.remove(childGroup)
    
    ###### Labeler Methods #######
        ##### add label #####
    def addLabeler(self, labelList, newLabel):
        if(newLabel not in labelList):
            labelList.append(newLabel)
    
    def addCreatorLabel(self, newLabel):
        self.addLabeler(self.creator, newLabel)
    
    def addSubjectLabel(self, newLabel):
        self.addLabeler(self.subjects, newLabel)

    def addTagLabel(self, newLabel):
        self.addLabeler(self.tags, newLabel)

        ###### remove label ######
    def removeLabeler(self, labelList, label):
        if(label in labelList):
            labelList.remove(label)

    def removeCreatorLabel(self, label):
        self.removeLabeler(self.creator, label)
    
    def removeSubjectsLabel(self, label):
        self.removeLabeler(self.subjects, label)

    def removeTagsLabel(self, label):
        self.removeLabeler(self.tags, label)

    ###### Items Methods ######
    #changes the order of the items in the list
    def moveItem(self, movingIndex, moveToIndex):
        movingItem = self.items[movingIndex]
        self.items.remove(movingItem)
        self.items.insert(moveToIndex, movingItem)
    
    #given a list of file names, populate the items list 
    def populateItems(self, fileNameList, directory):
        for file in fileNameList:
            self.items.append(Item(fileName=file, directory=directory))
        
    def giveToChild(self, itemIndex, childIndex):
        #add item to the childs item list
        self.childGroups[childIndex].items.append(self.items[itemIndex])
        self.items.remove(self.items[itemIndex]) #remove from parent item list

    def giveToParent(self, itemIndex):
        if(self.parent != None):
            self.parent.items.append(self.items[itemIndex])
            self.items.pop(itemIndex)

    
    def addItem(self, item):
        if(item not in self.items):
            self.items.append(item)

    def removeItem(self, item):
        if (item in self.items):
            self.items.remove(item)

    def addItemInFrontOf(self, item, newItem):
        if(item != newItem):#if the two items are the same, do nothing
            if(item in self.items):
                #if item already exists, remove it before moving it
                if(newItem in self.items):
                    self.removeItem(newItem)
                self.items.insert(self.items.index(item), newItem)
            else: #fallback
                self.addItem(newItem)
    


####### DataBase Write/Read ##########

#helper func, makes sure that the returned group num is unique
def getGroupNum(GroupObj, GroupDf):
    groupNum = GroupObj.groupNum

    if(groupNum == -1):
        #get new num
        groupNum = GroupDf["groupNumber"].max()#will return nan if df empty
        #correct nan if groupDf is empty
        if(math.isnan(groupNum)):
            groupNum = 0
        else:
            groupNum +=1 
    
    return groupNum

def getItemNum(ItemObj, ItemDf):#very similar to getGroupNum
    itemNum = ItemObj.itemNum

    if(itemNum == -1):
        #get new num
        itemNum = ItemDf["itemNumber"].max()
        if(pd.isna(itemNum)):
            itemNum = 0
        else:
            itemNum +=1
    
    return itemNum


#writes the file to the new location
def writeNewFile(newFileName, oldFileName, oldFileDirect, newFileDirect):

    if os.path.exists(oldFileDirect + "\\" + oldFileName):
        PIL.Image.open(oldFileDirect + "\\" + oldFileName).save(newFileDirect + "\\" + newFileName)
        os.remove(oldFileDirect + "\\" + oldFileName)
    else:
        print(f"Failed to find file: {oldFileName}")

#writes a group to the group csv, all of its items to the items csv, and rights new files
def writeGroup(Group, GroupDf, ItemDf, parentGroupNum, oldFileDirect, newFileDirect):

    childGroupNum = getGroupNum(GroupObj=Group, GroupDf=GroupDf)
    
    #write/update the group to the DF
    GroupDf.loc[childGroupNum] = [childGroupNum, parentGroupNum, " ".join(Group.subjects), " ".join(Group.creator), " ".join(Group.tags), str(Group.page)]

    #write items to csv/write new file
    for item in Group.items:
        itemNum = getItemNum(ItemObj=item, ItemDf=ItemDf) #may want to rewrite later so that itemNum is iterated instead
        newFileName = str(itemNum) + item.fileType

        ItemDf.loc[itemNum] = [itemNum, childGroupNum, newFileName]
        writeNewFile(newFileName=newFileName, newFileDirect=newFileDirect, oldFileName=item.fileName, oldFileDirect=oldFileDirect)
    
    #delete items/let garbage collect
    Group.items = []

#writes the group before recursively traversing tree
def traverseTree(ParentGroup, GroupDf, ItemDf, parentGroupNum, oldFileDirect, newFileDirect):
    writeGroup(ParentGroup, GroupDf, ItemDf, parentGroupNum, oldFileDirect=oldFileDirect, newFileDirect=newFileDirect)
    for Child in ParentGroup.childGroups:
        traverseTree(ParentGroup=Child, GroupDf=GroupDf, ItemDf=ItemDf, parentGroupNum=parentGroupNum)
    
    ParentGroup.childGroups = []
    

def writeTreeBoot(rootGroup, databaseDirect, oldFileDirect, newFileDirect):

    ItemsDf = pd.read_csv(databaseDirect + "ItemData.csv")
    GroupDf = pd.read_csv(databaseDirect + "GroupData.csv")

    #the root group is not written to the database, so each of its children is 
    #considered its own tree 
    for groupTree in rootGroup.childGroups:
        rootGroupNum = getGroupNum(GroupObj=groupTree, GroupDf=GroupDf)

        traverseTree(ParentGroup=groupTree, GroupDf=GroupDf, ItemDf=ItemsDf, 
                    parentGroupNum=rootGroupNum, oldFileDirect=oldFileDirect, newFileDirect=newFileDirect)

    rootGroup.childGroups = []

    #save database
    ItemsDf.to_csv(databaseDirect + "ItemData.csv", index=False)
    GroupDf.to_csv(databaseDirect + "GroupData.csv", index=False)
            

#return an array of all files in the directory
def getAllFiles(directory):
    PathObj = Path(directory)
    validFileTypes = [".jpg", ".jpeg", ".png"]
    return [f.name for f in PathObj.iterdir() if (f.is_file() and (f.suffix.lower() in validFileTypes))]


