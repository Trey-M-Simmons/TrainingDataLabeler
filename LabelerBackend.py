from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
import pandas as pd
import numpy as np
import os
import PIL
import math
import copy

####### keeps track of the directories ########
class Directories:
    def __init__(self):
        #new directory is where the files will be saved after commiting 
        self._newDataDirectory: str = "./"
        #old directory is where the files are prior to commiting
        self._oldDataDirectory: str = "./"
        
        self._dataBaseDirectory: str = "./DataBase/"
    
    #### get methods ####
    def getNewDataDirect(self)-> str:
        return copy.deepcopy(self._newDataDirectory)
    
    def getOldDataDirect(self)-> str:
        return copy.deepcopy(self._oldDataDirectory)
    
    def getDataBaseDirect(self)-> str:
        return copy.deepcopy(self._dataBaseDirectory)
    
    #### set methods ####
    #helper func to the rest of the set methods
    def _setDirect(direct: str)-> str:
        if(os.path.isdir(direct)):
            if(direct[-1] == "/"):
                return direct
            else:
                return f"{direct}/"
        else:
             raise FileNotFoundError(f"{direct} is NOT a valid directory!")
    
    def setNewDataDirect(self, direct: str):
        self._newDataDirectory = Directories._setDirect(direct)
    
    def setOldDataDirect(self, direct: str):
        self._oldDataDirectory = Directories._setDirect(direct)
    
    def setDataBaseDirect(self, direct: str):
        self._dataBaseDirectory = Directories._setDirect(direct)

#an item is some image or video that needs to be labeled and is contained inside of a group
class Item:
    def __init__(self, fileName = "unknown.unknown", directory = ".", itemNum: int = -1):
        self.fileName = fileName
        self.fileType = Path(fileName).suffix
        self.directory = directory
        self.itemNum = itemNum

#A group is a node of a tree where each group holds a list of items and a list of child groups
class Group:
    def __init__(self, items = None, subjects = [], creator = [], collection = -1, tags = [], page = 0, parent = None, groupNum = -1, directoryObj: Directories= None):
        
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
        self.groupNum = groupNum #note: group number 0 is reserved for the root group
        
        #determines if children have been loaded from the database
        self.childrenLoaded: bool = False
        
        #keeps track of directories
        self.directs = directoryObj
        
        
    
    ###### Child Group methods ######
    #all new child groups will be initialized with the current groups labeling
    def createChildGroup(self)-> None:
        newGroup = Group([], copy.deepcopy(self.subjects), copy.deepcopy(self.creator), self.collection, copy.deepcopy(self.tags), self.page, self)
        self.childGroups.append(newGroup)
    
    #adds an already created child group
    def addChildGroup(self, childGroup)-> None:
        if(childGroup not in self.childGroups):
            self.childGroups.append(childGroup)

    #moves a child group to a different pos in the list
    def moveChild(self, movingIndex, moveToIndex)-> None:
        self.childGroups.insert(movingIndex, moveToIndex)
        self.childGroups.remove(movingIndex)
    
    #deleted child groups items will be added back to parent
    def deleteChild(self, childGroup)-> None:
        #add the deleted child group's own children groups to the parent
        self.childGroups += childGroup.childGroups
        #add the deleted child group's items to the parents items
        self.items += childGroup.items
        #actually delete the child group
        self.childGroups.remove(childGroup)
    
    ###### Labeler Methods #######
        ##### add label #####
    def addLabeler(self, labelList, newLabel)-> None:
        if(newLabel not in labelList):
            labelList.append(newLabel)
    
    def addCreatorLabel(self, newLabel)-> None:
        self.addLabeler(self.creator, newLabel)
    
    def addSubjectLabel(self, newLabel)-> None:
        self.addLabeler(self.subjects, newLabel)

    def addTagLabel(self, newLabel)-> None:
        self.addLabeler(self.tags, newLabel)

        ###### remove label ######
    def removeLabeler(self, labelList, label)-> None:
        if(label in labelList):
            labelList.remove(label)

    def removeCreatorLabel(self, label)-> None:
        self.removeLabeler(self.creator, label)
    
    def removeSubjectsLabel(self, label)-> None:
        self.removeLabeler(self.subjects, label)

    def removeTagsLabel(self, label)-> None:
        self.removeLabeler(self.tags, label)

    ###### Items Methods ######
    #changes the order of the items in the list
    def moveItem(self, movingIndex, moveToIndex)-> None:
        movingItem = self.items[movingIndex]
        self.items.remove(movingItem)
        self.items.insert(moveToIndex, movingItem)
    
    #given a list of file names, populate the items list 
    def populateItems(self, fileNameList, directory)-> None:
        for file in fileNameList:
            self.items.append(Item(fileName=file, directory=directory))
        
    def giveToChild(self, itemIndex, childIndex)-> None:
        #add item to the childs item list
        self.childGroups[childIndex].items.append(self.items[itemIndex])
        self.items.remove(self.items[itemIndex]) #remove from parent item list

    def giveToParent(self, itemIndex)-> None:
        if(self.parent != None):
            self.parent.items.append(self.items[itemIndex])
            self.items.pop(itemIndex)

    def addItem(self, item)-> None:
        if(item not in self.items):
            self.items.append(item)

    def removeItem(self, item)-> None:
        if (item in self.items):
            self.items.remove(item)

    def addItemInFrontOf(self, item, newItem)-> None:
        if(item != newItem):#if the two items are the same, do nothing
            if(item in self.items):
                #if item already exists, remove it before moving it
                if(newItem in self.items):
                    self.removeItem(newItem)
                self.items.insert(self.items.index(item), newItem)
            else: #fallback
                self.addItem(newItem)
    
    ######## Other #########
    
    #mainly used for debug purposes
    def printGroupTree(self, row: int = 0)-> None:
        print(f"Row: {row} Group: {self.groupNum} Subjects: {self.subjects} Creators: {self.creator} Tags: {self.tags}")
        for item in self.items:
            print(f"Item: {item.itemNum} FileName: {item.fileName} Directory: {item.directory}")
            
        for child in self.childGroups:
            child.printGroupTree(row + 1)
            
    ####### load ##########
    
    #loads all of the items from database into memory
    def loadItems(self, GroupDF = pd.DataFrame(), ItemDF = pd.DataFrame())-> None:
        #if the current group is new, then it will not have items in the database
        if(self.groupNum == -1):
            return
        
        databaseDirect = self.directs.getDataBaseDirect()
        imgDirect = self.directs.getOldDataDirect()
            
        groupDirec = f"{databaseDirect}GroupData.csv"
        itemDirec = f"{databaseDirect}ItemData.csv"
        if(GroupDF.empty):
            GroupDF = pd.read_csv(groupDirec)
        if(ItemDF.empty):
            ItemDF = pd.read_csv(itemDirec)
            
        #rows of all of the items of the group
        groupItemsDF =  ItemDF[ItemDF["groupNumber"] == self.groupNum]
        
        for itemRow in groupItemsDF.itertuples(index = False):
            self.addItem(Item(fileName=itemRow.fileName, directory=imgDirect, itemNum = itemRow.itemNumber))
    
    #loads all of the children from the database into memory
    def loadGroupChildren(self, GroupDF = pd.DataFrame(), ItemDF = pd.DataFrame())-> None:
        #if the current group is new, then it will not have children in the database
        if(self.groupNum == -1 or self.childrenLoaded == True):
            return
        
        databaseDirect = self.directs.getDataBaseDirect()
        imgDirect = self.directs.getOldDataDirect()
        groupDirec = f"{databaseDirect}GroupData.csv"
        itemDirec = f"{databaseDirect}ItemData.csv"
        if(GroupDF.empty):
            GroupDF = pd.read_csv(groupDirec)
        if(ItemDF.empty):
            ItemDF = pd.read_csv(itemDirec)
        
        #contains all of the rows with this group as the parent
        groupRootDF = GroupDF[GroupDF["parentNumber"] == self.groupNum]
        #for each group to be loaded
        for row in groupRootDF.itertuples(index=False):
            groupNum: int = int(row.groupNumber)
            
            #get the row of the group that is going to be loaded
            groupRow = GroupDF.loc[GroupDF["groupNumber"] == groupNum]
            
            #get values
            subjects: list[str] = [] if pd.isna(groupRow["subjects"].item()) else groupRow["subjects"].item().split(" ")
            creators: list[str] = [] if pd.isna(groupRow["creators"].item()) else groupRow["creators"].item().split(" ")
            tags: list[str] = [] if pd.isna(groupRow["tags"].item()) else groupRow["tags"].item().split(" ")
            pg: int = 0 if pd.isna(groupRow["pg"].item()) else int(groupRow["pg"].item())
            parentNum: int = int(groupRow["parentNumber"].item())
            
            #create group
            group = Group(items = None, subjects = subjects, creator = creators, collection = -1, tags = tags, page = pg, parent = self, groupNum = groupNum, directoryObj = self.directs)
            #load items
            group.loadItems(GroupDF = GroupDF, ItemDF = ItemDF)
            
            self.addChildGroup(group)
        
        self.childrenLoaded = True
        
    


####### DataBase Write/Read ##########

#used to load the database back into a group tree
#loads files not already in the database into the rootGroup
def initializeGroupTree(directoryObj: Directories) -> Group:
    dataBaseDirect: str = directoryObj.getDataBaseDirect()
    imgDirect: str = directoryObj.getOldDataDirect()
    groupDirec: str = f"{dataBaseDirect}GroupData.csv"
    itemDirec: str = f"{dataBaseDirect}ItemData.csv"
    
    GroupDF = pd.read_csv(groupDirec)
    ItemDF = pd.read_csv(itemDirec)
    
    rootGroup = Group(directoryObj = directoryObj)
    rootGroup.groupNum = 0
    
    rootGroup.loadGroupChildren()
    
    #get all image files 
    fileNameList: list[str] = getAllFiles(imgDirect)
        
    #do not load int files already in the database
    listLen = len(fileNameList)
    fileIndex = 0
    dataBaseFileList = ItemDF["fileName"].to_numpy()

    while(fileIndex < listLen):
        if fileNameList[fileIndex] in dataBaseFileList:
            fileNameList.pop(fileIndex)
            listLen -=1
        else:
            fileIndex += 1
            
    rootGroup.populateItems(fileNameList, imgDirect)
    #rootGroup.printGroupTree()
    
    return rootGroup
        
    

#helper func, makes sure that the returned group num is unique
def getGroupNum(GroupObj, GroupDf)-> int:
    groupNum = GroupObj.groupNum

    if(groupNum == -1):
        #get new num
        groupNum = GroupDf["groupNumber"].max()#will return nan if df empty
        #correct nan if groupDf is empty
        if(pd.isna(groupNum)):
            groupNum = 1
        else:
            groupNum +=1 
    
    return groupNum

#nearly identical to getGroupNum
def getItemNum(ItemObj, ItemDf)-> int:#very similar to getGroupNum
    itemNum = ItemObj.itemNum

    if(itemNum == -1):
        #get new num
        itemNum = ItemDf["itemNumber"].max()
        if(pd.isna(itemNum)):
            itemNum = 1
        else:
            itemNum +=1
    
    return itemNum


#writes the file to the new location
def writeNewFile(newFileName, oldFileName, oldFileDirect, newFileDirect)-> None:
    oldFullPath = oldFileDirect + oldFileName
    newFullPath = newFileDirect + newFileName
    
    if os.path.exists(oldFullPath):
        if os.path.exists(newFileDirect):
            if(oldFileDirect != newFileDirect):#if new location, write and delete old one
                PIL.Image.open(oldFullPath).save(newFullPath)
                os.remove(oldFullPath)
            elif(oldFileName != newFileName): #if file name hasn't changed, do nothing, otherwise re-name
                os.rename(oldFullPath, newFullPath)
        else:
            print(f"Failed to find folder {newFileDirect}")
    else:
        print(f"Failed to find file: {oldFileName}")

#writes a group to the group csv, all of its items to the items csv, and writes new files
def writeGroup(Group, GroupDf, ItemDf, parentGroupNum, oldFileDirect, newFileDirect)-> None:

    childGroupNum = getGroupNum(GroupObj=Group, GroupDf=GroupDf)
    
    #write/update the group to the DF
    #determine row of the group in the DF, if it exists, update it, otherwise add a new row
    groupBool = GroupDf["groupNumber"] == childGroupNum
    if(groupBool.any()):
        GroupDf.loc[groupBool] = [childGroupNum, parentGroupNum, " ".join(Group.subjects), " ".join(Group.creator), " ".join(Group.tags), Group.page]
    else:
        GroupDf.loc[len(GroupDf)] = [childGroupNum, parentGroupNum, " ".join(Group.subjects), " ".join(Group.creator), " ".join(Group.tags), Group.page]

    #write items to csv/write new file
    for item in Group.items:
        itemNum = getItemNum(ItemObj=item, ItemDf=ItemDf) #may want to rewrite later so that itemNum is iterated instead
        newFileName = str(itemNum) + item.fileType

        itemBool = ItemDf["itemNumber"] == itemNum
        if(itemBool.any()):
            ItemDf.loc[itemBool] = [itemNum, childGroupNum, newFileName]
        else:
            ItemDf.loc[len(ItemDf)] = [itemNum, childGroupNum, newFileName]
        writeNewFile(newFileName=newFileName, newFileDirect=newFileDirect, oldFileName=item.fileName, oldFileDirect=oldFileDirect)
    
    #delete items/let garbage collect
    Group.items = []

#writes the group before recursively traversing tree
def traverseTree(ParentGroup, GroupDf, ItemDf, parentGroupNum, oldFileDirect, newFileDirect)-> None:
    writeGroup(ParentGroup, GroupDf, ItemDf, parentGroupNum, oldFileDirect=oldFileDirect, newFileDirect=newFileDirect)
    #get group num
    parentGroupNum = getGroupNum(ParentGroup, GroupDf)
    for Child in ParentGroup.childGroups:
        traverseTree(ParentGroup=Child, GroupDf=GroupDf, ItemDf=ItemDf, parentGroupNum=parentGroupNum, oldFileDirect = oldFileDirect, newFileDirect = newFileDirect)
    
    ParentGroup.childGroups = []
    

def writeTreeBoot(rootGroup, databaseDirect, oldFileDirect, newFileDirect)-> None:

    ItemsDf = pd.read_csv(databaseDirect + "ItemData.csv").astype({"itemNumber" : int, "groupNumber" : int, "fileName" : str})
    GroupDf = pd.read_csv(databaseDirect + "GroupData.csv").astype({"groupNumber" : int, "parentNumber" : int, "subjects" : str, "creators": str, "tags" : str, "pg" : int})

    #the root group is not written to the database, so each of its children is 
    #considered its own tree 
    for groupTree in rootGroup.childGroups:
        #rootGroupNum = getGroupNum(GroupObj=groupTree, GroupDf=GroupDf)

        traverseTree(ParentGroup=groupTree, GroupDf=GroupDf, ItemDf=ItemsDf, 
                    parentGroupNum=0, oldFileDirect=oldFileDirect, newFileDirect=newFileDirect)

    rootGroup.childGroups = []

    #save database
    ItemsDf.to_csv(databaseDirect + "ItemData.csv", index=False)
    GroupDf.to_csv(databaseDirect + "GroupData.csv", index=False)
            

#return an array of all files in the directory
def getAllFiles(directory)-> list[str]:
    PathObj = Path(directory)
    validFileTypes = [".jpg", ".jpeg", ".png"]
    return [f.name for f in PathObj.iterdir() if (f.is_file() and (f.suffix.lower() in validFileTypes))]


#sets the database directory by prompting the user to select a directory, if the directory does not contain the csv files, it will ask if they want to create them
def setDataBaseFolder(DirectoriesObj: Directories)-> None:
    selectionMade: bool = False
    direct: str = ""
    
    while(not selectionMade):
        direct = filedialog.askdirectory(title="Select Database Folder")
        if(os.path.exists(direct + "/GroupData.csv") and os.path.exists(direct + "/ItemData.csv") and os.path.exists(direct + "/Labels.csv")):
            DirectoriesObj.setDataBaseDirect(direct)
            selectionMade = True
        else:
            selectionMade = messagebox.askyesno(title="Create DataBase files?", message="Database files not found, would you like to create them?")
            #prompt again if the user does not want to create the missing files
            if(not selectionMade):
                continue
    
            #if user chose to create the missing files, create them
            with open(direct + "/GroupData.csv", "w") as groupFile:
                groupFile.write("groupNumber,parentNumber,subjects,creators,tags,pg")
            with open(direct + "/ItemData.csv", "w") as itemFile:
                itemFile.write("itemNumber,groupNumber,fileName")
            with open(direct + "/Labels.csv", "w") as labelFile:
                labelFile.write("subjects,creators,tags")
    
            DirectoriesObj.setDataBaseDirect(direct)
            selectionMade = True

