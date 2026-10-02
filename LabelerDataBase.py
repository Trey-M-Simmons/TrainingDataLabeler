import os
import sqlite3
import LabelerBackend as LB
from tkinter import filedialog
from tkinter import messagebox
import PIL


class LabelerDataBase:
    def __init__(self):
        self.sortedDBDirect = None
        self.sortedFolderDirect = None
        self.sortedDirect = None #top level folder of the directory


    def getDataBaseDirect(self)-> str:
        return self.sortedDirect


    def setDataBaseDirect(self, direct: str = None):
        if(direct == None):
            selectionMade: bool = False
            #allow the user to select a database folder
            while(not selectionMade):
                direct = filedialog.askdirectory(title="Select Database Folder")
                #if user clicked the "x", do nothing and exit the func
                if(direct == ""):
                    messagebox.showinfo(title="No Folder Selected", message="Database folder has Not been changed!")
                    return
                        
                if(self.checkDBExistence(direct)):#if it doesnt exist, prompt to create it
                    selectionMade = True

                    self.sortedDirect = direct + "/SortedData/"
                    self.sortedDBDirect = self.sortedDirect + "labeler.db"
                    self.sortedFolderDirect = self.sortedDirect + "LabledImages/"
                else:
                    selectionMade = messagebox.askyesno(title="Create DataBase files?", message="Database files not found, would you like to create them?")
                    #prompt again if the user does not want to create the missing files
                    if(not selectionMade):
                        continue

                    self.sortedDirect = direct + "/SortedData/"
                    self.sortedDBDirect = self.sortedDirect + "labeler.db"
                    self.sortedFolderDirect = self.sortedDirect + "LabledImages/"

                    self.createDatabase()
                    
                    selectionMade = True
                    return
        else:
            if(direct[-1] != "/"):
                direct = f"{direct}/"
            else:
                direct = direct
            
            self.sortedDirect = direct + "SortedData/"
            self.sortedDBDirect = self.sortedDirect + "labeler.db"
            self.sortedFolderDirect = self.sortedDirect + "LabledImages/"

            if(self.checkDBExistence(direct)):
                return
            
            self.createDatabase()


    #checks if the db file and image folder exists, return true only if all are true
    def checkDBExistence(self, direct: str) -> bool:
        direct += "/SortedData"
        if(not os.path.isdir(direct)):
            return False
        if(not os.path.isdir(direct + "/LabledImages/")):
            return False
        if(not os.path.exists(direct + "/labeler.db")):
            return False
        return True


    def createGroupTable(self)->None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS groups (
                            groupNum INTEGER PRIMARY KEY AUTOINCREMENT,
                            parentNum INTEGER NOT NULL, 
                            subjects TEXT, 
                            creators TEXT,
                            tags TEXT, 
                            pg INTEGER
                        )''')
            conn.commit()

    def createItemTable(self)->None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                            itemNum INTEGER PRIMARY KEY AUTOINCREMENT,
                            groupNum INTEGER NOT NULL,
                            fileName TEXT NOT NULL
                        )''')
            conn.commit()

    def createLabelTable(self)->None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS labels (
                            subjects TEXT UNIQUE,
                            creators TEXT UNIQUE,
                            tags TEXT UNIQUE
                        )''')
            conn.commit()

    def createDatabase(self)->None:
        #make folders
        os.makedirs(self.sortedFolderDirect, exist_ok=True) 
        #create tables
        self.createGroupTable()
        self.createItemTable()
        self.createLabelTable()

    def writeItemFile(self, itemObj)->None:
        newFileName = f"{itemObj.itemNum}{itemObj.fileType}"

        oldFullPath = itemObj.directory + itemObj.fileName
        newFullPath = self.sortedFolderDirect + newFileName
        
        if os.path.exists(oldFullPath):
            if os.path.exists(self.sortedFolderDirect):
                if(itemObj.directory != self.sortedFolderDirect):#if new location, write and delete old one
                    PIL.Image.open(oldFullPath).save(newFullPath)
                    os.remove(oldFullPath)
                elif(itemObj.fileName != newFileName): #if file name hasn't changed, do nothing, otherwise re-name
                    os.rename(oldFullPath, newFullPath)
            else:
                print(f"Failed to find folder {self.sortedFolderDirect}")
        else:
            print(f"Failed to find file: {oldFullPath}")

    def writeItems(self, groupObj)->None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            #get the current maximum item number for the group
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(itemNum) FROM items')
            currItemNum = cursor.fetchone()[0]
            if currItemNum is None:
                currItemNum = 0

            for item in groupObj.items:
                #if the item is new and not in the database yet, insert, otherwise update
                if(item.itemNum == -1):
                    currItemNum += 1
                    item.itemNum = currItemNum
                    
                    cursor.execute('''INSERT INTO items (itemNum, groupNum, fileName)
                                    VALUES (?, ?, ?)''',
                                    (item.itemNum,
                                    groupObj.groupNum,
                                    str(item.itemNum) + item.fileType))
                else:
                    cursor.execute('''UPDATE items SET groupNum = ?, fileName = ? 
                                    WHERE itemNum = ?''',
                                    (groupObj.groupNum,
                                    item.fileName,
                                    str(item.itemNum) + item.fileType))

                #write the item file to the sorted folder
                self.writeItemFile(item)
            conn.commit()


    def writeSingleGroup(self, groupObj, parentNum)->None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO groups (groupNum, parentNum, subjects, creators, tags, pg)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (groupObj.groupNum,
                            parentNum,
                            " ".join(groupObj.subjects),
                            " ".join(groupObj.creator),
                            " ".join(groupObj.tags),
                            groupObj.page))
            conn.commit()

        self.writeItems(groupObj=groupObj)

    #recursively sets the group numbers for the parent group and its child groups, that do not already have them
    def traverseTree(self, ParentGroup, currGroupNum)-> int:

        #write parent to DB, in the future, check for change flag before writing
        #self.writeSingleGroup(groupObj=ParentGroup, parentNum=ParentGroup.parentNum, )
        parentNum = ParentGroup.groupNum

        for Child in ParentGroup.childGroups:
            #assign the current group number to the parent group
            if(Child.groupNum == -1):
                currGroupNum += 1
                Child.groupNum = currGroupNum

            #write parent to DB, in the future, check for change flag before writing
            self.writeSingleGroup(groupObj=Child, parentNum=parentNum)

            currGroupNum = self.traverseTree(ParentGroup=Child, currGroupNum=currGroupNum)
            
        return currGroupNum


    def writeGroups(self, rootGroup)->None:

        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT MAX(groupNum) FROM groups''')
            maxGroupNum = cursor.fetchone()[0]
            if maxGroupNum is None:
                maxGroupNum = 0
        
        self.traverseTree(ParentGroup=rootGroup, currGroupNum=maxGroupNum)
        
        rootGroup.childGroups = []

    def writeLabels(self, labelsObj)-> None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()

            for subject in labelsObj.subjectLabels:
                cursor.execute("INSERT INTO labels (subjects) VALUES (?) ON CONFLICT(subjects) DO NOTHING", (subject,))
            for creator in labelsObj.creatorLabels:
                cursor.execute("INSERT INTO labels (creators) VALUES (?) ON CONFLICT(creators) DO NOTHING", (creator,))
            for tag in labelsObj.tagLabels:
                cursor.execute("INSERT INTO labels (tags) VALUES (?) ON CONFLICT(tags) DO NOTHING", (tag,))
            conn.commit()

    def setItems(self, groupObj)-> None:
        groupObj.items = self.getItemsOf(groupObj.groupNum)

    def getItemsOf(self, groupNum)-> list:
        items = []

        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT itemNum, fileName FROM items WHERE groupNum = ?", (groupNum,))

            for itemRow in cursor:
                itemNum = itemRow[0]
                groupNum = groupNum
                fileName = itemRow[1]

                items.append(LB.Item(fileName=fileName, directory=self.sortedFolderDirect, itemNum=itemNum))

        return items

    #loads all of the direct children of a group from the database into memory
    def getChildrenOf(self, parentGroup)-> None:
        childGroups = []
        parentGroupNum = parentGroup.groupNum

        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups WHERE parentNum = ?", (parentGroupNum,))

            for groupRow in cursor:
                groupNum = groupRow[0]
                parentNum = groupRow[1]
                subjects = [] if groupRow[2] is None else groupRow[2].split(" ")
                creators = [] if groupRow[3] is None else groupRow[3].split(" ")
                tags = [] if groupRow[4] is None else groupRow[4].split(" ")
                pg = groupRow[5]

                group = LB.Group(DB=self, items=None, subjects=subjects, creator=creators, collection=-1, tags=tags, page=pg, parent=parentGroup, groupNum=groupNum)
                self.setItems(group)
                childGroups.append(group)

        return childGroups

    def loadLabels(self, LabelsObj)-> None:
        with sqlite3.connect(self.sortedDBDirect) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT subjects FROM labels")
            for subject in cursor:
                LabelsObj.subjectLabels.append(subject[1])
        
            cursor.execute("SELECT creators FROM labels") 
            for creator in cursor:
                LabelsObj.creatorLabels.append(creator[1])
        
            cursor.execute("SELECT tags FROM labels")
            for tag in cursor:
                LabelsObj.tagLabels.append(tag[1])


