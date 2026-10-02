from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
import pandas as pd
import os
import PIL
import copy
from PIL import Image, ImageTk
#import LabelerDataBase as LDB
import sqlite3

####### keeps track of the directories ########
class Directories:
    def __init__(self):
        #new directory is where the files will be saved after commiting 
        self._newDataDirectory: str = None
        #old directory is where the files are prior to commiting
        self._oldDataDirectory: str = None
        
        self._dataBaseDirectory: str = None
    
    #### get methods ####
    def getNewDataDirect(self)-> str:
        return copy.deepcopy(self._newDataDirectory)
    
    def getOldDataDirect(self)-> str:
        return copy.deepcopy(self._oldDataDirectory)
    
    def getDataBaseDirect(self)-> str:
        return copy.deepcopy(self._dataBaseDirectory)
    
    #### set methods ####
    #helper func to the rest of the set methods, ensures the directory exists and has a trailing slash
    def _setDirect(direct: str)-> str:
        if(os.path.isdir(direct)):
            if(direct[-1] == "/"):
                return direct
            else:
                return f"{direct}/"
        else:
             raise FileNotFoundError(f"{direct} is NOT a valid directory!")
    
    def setNewDataDirect(self, direct: str = None):
        if(direct == None):
            direct = filedialog.askdirectory(title="Select Where to Save New Data")
        self._newDataDirectory = Directories._setDirect(direct)
    
    def setOldDataDirect(self, direct: str = None):
        if(direct == None):
            direct = filedialog.askdirectory(title="Select an Image Folder")
        self._oldDataDirectory = Directories._setDirect(direct)
    
    def setDataBaseDirect(self, direct: str = None):
        if(direct == None):
            selectionMade: bool = False

            while(not selectionMade):
                direct = filedialog.askdirectory(title="Select Database Folder")
                #if user clicked the "x", do nothing and exit the func
                if(direct == ""):
                    messagebox.showinfo(title="No Folder Selected", message="Database folder has Not been changed!")
                    return
                    
                groupDirect = direct + "/GroupData.csv"
                itemDirect = direct + "/ItemData.csv"
                labelsDirect = direct + "/Labels.csv"
                if(os.path.exists(groupDirect) and os.path.exists(itemDirect) and os.path.exists(labelsDirect)):
                    selectionMade = True
                else:
                    selectionMade = messagebox.askyesno(title="Create DataBase files?", message="Database files not found, would you like to create them?")
                    #prompt again if the user does not want to create the missing files
                    if(not selectionMade):
                        continue
                
                    #if user chose to create the missing files, create them
                    if(not os.path.exists(groupDirect)):
                        with open(groupDirect, "w") as groupFile:                            
                            groupFile.write("groupNumber,parentNumber,subjects,creators,tags,pg")
                    if(not os.path.exists(itemDirect)):
                        with open(itemDirect, "w") as itemFile:
                            itemFile.write("itemNumber,groupNumber,fileName")
                    if(not os.path.exists(labelsDirect)):
                        with open(labelsDirect, "w") as labelFile:
                            labelFile.write("subjects,creators,tags")
                
                    selectionMade = True

        self._dataBaseDirectory = Directories._setDirect(direct)

#keeps track of various page state data such as labels
class Labels():
    def __init__(self, DataBaseObj = None):
        #all of the label options for each label
        #note: the most recently used option should be at the top of the list
        self.subjectLabels = []
        self.creatorLabels = []
        self.tagLabels = []

        self.LabelsCSV = None #DELETE

        #if a database was given load the labels from it
        if(DataBaseObj != None):
            DataBaseObj.loadLabels(self)



    ##### Put Label Functions #####
    
    #if a label is already in the list, move it to the top, otherwise it is added to the top
    #helper func to the below put functions
    def putLabelOnTop(self, LabelList, addlabel)->None:
        if(addlabel in LabelList):
            LabelList.remove(addlabel)
        LabelList.append(addlabel)
    
    def putSubject(self, label)->None:
        self.putLabelOnTop(LabelList=self.subjectLabels, addlabel=label)
    
    def putCreator(self, label)->None:
        self.putLabelOnTop(LabelList=self.creatorLabels, addlabel=label)

    def putTag(self, label)->None:
        self.putLabelOnTop(LabelList=self.tagLabels, addlabel=label)

    ##### Remove Label Functions #####
    #not finished yet

#an item is some image or video that needs to be labeled and is contained inside of a group
class Item:
    def __init__(self, fileName = "unknown.unknown", directory = ".", itemNum: int = -1, maxItemWidth: int = 400, maxItemHeight: int = 300):
        self.fileName = fileName
        self.fileType = Path(fileName).suffix
        self.directory = directory
        self.itemNum = itemNum
        self.IMG = None

        self.maxItemWidth = maxItemWidth
        self.maxItemHeight = maxItemHeight

        self.itemWidth: int = None
        self.itemHeight: int = None


    def getIMG(self):
        #if the item has not been rendered yet then do so
        if((self.IMG == None) and (os.path.exists(self.directory + self.fileName))):
            self.IMG = Image.open(self.directory + self.fileName)
            #resize
            self.IMG.thumbnail((self.maxItemWidth, self.maxItemHeight), Image.Resampling.LANCZOS) 
            self.IMG = ImageTk.PhotoImage(self.IMG)

        return self.IMG

    def getHeight(self):
        return self.maxItemHeight

#A group is a node of a tree where each group holds a list of items and a list of child groups
class Group:
    def __init__(self, DB, items = None, subjects = [], creator = [], collection = -1, tags = [], page = 0, parent = None, groupNum = -1, directoryObj: Directories= None):
        
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
        #data base object
        self.DB = DB
        
        
    
    ###### Child Group methods ######
    #all new child groups will be initialized with the current groups labeling
    def createChildGroup(self)-> None:
        newGroup = Group(DB=self.DB, items=[], subjects=copy.deepcopy(self.subjects), creator=copy.deepcopy(self.creator), collection=self.collection, tags=copy.deepcopy(self.tags), page=self.page, parent=self)
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
    #loads all of the children from the database into memory
    def loadGroupChildren(self)-> None:
        #if the current group is new, then it will not have children in the database
        if(self.groupNum == -1 or self.childrenLoaded == True):
            return

        #load group children and their items from the database
        self.childGroups = self.DB.getChildrenOf(self)
        self.childrenLoaded = True

    #used to load the database back into a group tree
    #loads files not already in the database into the rootGroup
    #should only be called on the root group
    def initializeGroupTree(self):
        imgDirect: str = self.directs.getOldDataDirect()
        
        self.groupNum = 0
        self.loadGroupChildren()
        
        #get all image files 
        fileNameList: list[str] = getAllFiles(imgDirect)

        self.populateItems(fileNameList, imgDirect)
            
#return an array of all files in the directory
def getAllFiles(directory)-> list[str]:
    PathObj = Path(directory)
    validFileTypes = [".jpg", ".jpeg", ".png"]
    return [f.name for f in PathObj.iterdir() if (f.is_file() and (f.suffix.lower() in validFileTypes))]