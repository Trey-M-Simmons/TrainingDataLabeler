"""
Author: Trey Simmons
Created: 3/17/26
Date of Last Edit: 9/29/26
Edit: Added open/set the new/old image folders, and set the database folder tool bar options. Also added handling for window close protocol.

Description: This is the main file for the data labeling program. It contains the GUI and the main function that run the program. 
"""


import bisect
import tkinter as tk
from tkinter import dnd
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
#from turtle import pos
#from xxlimited import new
from PIL import Image, ImageTk
from sympy import root
import LabelerDataBase as DB
import LabelerBackend as LB
import pandas as pd
import os

def main():
    MainPage = tk.Tk()
    LabelsObj = None
    DataBaseObj = DB.LabelerDataBase()
    DirectoriesObj = LB.Directories()

    SORT(MainPage, LabelsObj, DirectoriesObj, DataBaseObj)




######################### SORTING SECTION ###########################
def SORT(MainPage, LabelsObj: LB.Labels, DirectoriesObj: LB.Directories, DataBaseObj: DB.LabelerDataBase)->None:
    
    #get directory from user
    directoryStr = filedialog.askdirectory(title="Select an Image or Video Folder")
    DirectoriesObj.setOldDataDirect(directoryStr)
    DirectoriesObj.setNewDataDirect(directoryStr)
    DataBaseObj.setDataBaseDirect()
    

    LabelsObj = LB.Labels(DataBaseObj)
    RootGroup = LB.Group(DB=DataBaseObj, directoryObj=DirectoriesObj)
    RootGroup.initializeGroupTree()
    
    
    MainPage.title("Data Labeler")
    MainPage.geometry("1500x1500")
    if(os.path.exists("./icon.png")):
        icon = ImageTk.PhotoImage(file="./icon.png")
        MainPage.iconphoto(True, icon)

    SortPage = sortPage(MainPage=MainPage, LabelsObj=LabelsObj, rootGroup=RootGroup, DirectoriesObj=DirectoriesObj, DataBaseObj=DataBaseObj)

    MainPage.mainloop()

#Main page that the user will see, the left side of the page will have the parent group/items while the right side will have 
# all of the children groups of the current parent. The user will then be able to drag and drop items from the parent group into the child groups, 
# as well as create new child groups and delete child groups. The user may choose to sort a child group, making that child the new parent group and 
# that child's children the new current child groups.
class sortPage:
    def __init__(self, MainPage, LabelsObj:LB.Labels, rootGroup, DirectoriesObj, DataBaseObj: DB.LabelerDataBase):

        self.LabelsObj = LabelsObj
        self.parentGroup = rootGroup
        self.RootGroup = rootGroup
        self.ParentGroupWidget : GroupWidget = None
        self.ChildGroupWidgets = []
        self.SelectedChildWidget : GroupWidget = None

        self.MainPage = MainPage

        #database and file directories
        self.DirectoriesObj = DirectoriesObj #May Need to Delete
        self.DataBaseObj = DataBaseObj

        #menu bar
        #here for now, will be moved later
        self.MenuBar = tk.Menu(MainPage)

        #file options
        self.FileMenu = tk.Menu(self.MenuBar, tearoff=0)
        self.FileMenu.add_command(label="Open Image Folder", command=self.setImageFolder) 
        self.FileMenu.add_command(label="Set Save Folder", command=self.setSaveFolder)
        self.FileMenu.add_command(label="Set Database Folder", command=self.setDataBaseFolder)
        self.MenuBar.add_cascade(label="File", menu=self.FileMenu)

        #database options
        self.CommitMenu = tk.Menu(self.MenuBar, tearoff=0)
        self.CommitMenu.add_command(label="Commit to Database", command=self.commitGroups)
        self.CommitMenu.add_command(label="Commit and Exit", command=self.commitExit)
        self.MenuBar.add_cascade(label="Commit", menu=self.CommitMenu)

        MainPage.config(menu=self.MenuBar)

        MainPage.columnconfigure(0, weight=1)
        MainPage.columnconfigure(1, weight=1)
        MainPage.rowconfigure(0, weight=1)

        #catch for user clicking close window
        MainPage.protocol("WM_DELETE_WINDOW", self.onClose)

        #create left/parent frame
        self.LeftFrame = tk.Frame(MainPage, width=900, height=500)  #outer most frame
        #self.LeftFrame.pack(side="left", fill="both", expand=True)
        self.LeftFrame.grid(row=0, column=0, sticky="NSEW")
        
        self.LeftFrame.columnconfigure(0, weight=1)
        self.LeftFrame.rowconfigure(0, weight=0)
        self.LeftFrame.rowconfigure(1, weight=1)
        
        self.SortGroupAbove = tk.Button(self.LeftFrame, text="Back")
        self.SortGroupAbove.grid(row=0, column=0, pady=33, padx=10)
        self.SortGroupAbove.bind("<Button-1>", self.sortParentGroup)

        #create right/child frame
        self.RightFrame = tk.Frame(MainPage, width=1200, height=500)
        #self.RightFrame.pack(side="right", fill="both", expand=True)
        self.RightFrame.grid(row=0, column=1, sticky="NSEW")

        self.RightFrame.columnconfigure(0, weight=1)
        self.RightFrame.rowconfigure(3, weight=1)

        self.NewGroupButton = tk.Button(self.RightFrame, text="Create New Group")
        self.NewGroupButton.grid(row=0, column=0)
        self.NewGroupButton.bind("<Button-1>", self.CreateChildGroup)

        self.DeleteGroupButton = tk.Button(self.RightFrame, text="Delete Selected Group")
        self.DeleteGroupButton.grid(row=1, column=0)
        self.DeleteGroupButton.bind("<Button-1>", self.deleteChildWidget)

        self.SortGroupButton = tk.Button(self.RightFrame, text="Sort Child Group")
        self.SortGroupButton.grid(row=2, column=0)
        self.SortGroupButton.bind("<Button-1>", self.sortChildGroup)

        self.RightScrollFrame = ScrollableFrame(self.RightFrame, width=1200, height=500)
        self.RightScrollFrame.grid(row=3, column=0, sticky="NSEW")
        
        #populate the left and right sides
        self.populateLeft()
        self.populateRight()

    ######## GUI Widget Setting Functions ########

    #populate the left side of the GUI with a GroupWidget of the parent group and its item widgets
    def populateLeft(self)->None:
        if(self.ParentGroupWidget == None):
            self.ParentGroupWidget = GroupWidget(ParentWidget=self.LeftFrame, Group=self.parentGroup, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900)
            self.ParentGroupWidget.grid(row=1, column=0, sticky="nsew")
        else:
            if(self.ParentGroupWidget.Group != self.parentGroup):#if the parent group has changed, delete old widgets
                self.ParentGroupWidget.deleteItemWidgets()
                self.ParentGroupWidget.Group = self.parentGroup

            self.ParentGroupWidget.setLabelText()
            self.ParentGroupWidget.setItemWidgets()
            
    #set the item widgets of the parent group widget
    def updateLeft(self)->None:
        if(self.ParentGroupWidget != None):
            self.ParentGroupWidget.renderItemWidgets()

    #populate the right side of the GUI with GroupWidgets of the current child groups 
    def populateRight(self)->None:
        for childWidget in self.ChildGroupWidgets:
            childWidget.destroy()
        
        self.ChildGroupWidgets = []
        
        #for child in self.parentGroup.childGroups:
        for childIndex in range(0, len(self.parentGroup.childGroups)):
            child = self.parentGroup.childGroups[childIndex]
            newChildWidget = GroupWidget(ParentWidget = self.RightScrollFrame.InnerFrame, Group = child, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
            #self.RightScrollFrame.InnerFrame.rowconfigure(childIndex, weight=1)
            newChildWidget.grid(row=childIndex, column=0, sticky="nsew")
            newChildWidget.bind("<Button-1>", self.selectChildWidget)
            self.ChildGroupWidgets.append(newChildWidget)

        #reset selected
        self.SelectedChildWidget = None

    #iterated through the child groups and child widgets, deleting or creating widgets as needed to match the child groups
    def updateRight(self)->None:
        groupIndex = 0
        while(groupIndex < len(self.parentGroup.childGroups)):

            #check if the current item has a corresponding widget
            foundWidgetIndex = 0
            foundWidgetFlag = False
            if(len(self.ChildGroupWidgets) != 0):#makes sure that there are widgets
                for widgetIndex in range(groupIndex, len(self.ChildGroupWidgets)):
                    if(self.parentGroup.childGroups[groupIndex] == self.ChildGroupWidgets[widgetIndex].Group):
                        foundWidgetFlag = True
                        foundWidgetIndex = widgetIndex
                        break
            
            #if the widget was found, delete widgets that no longer have a corresponding item
            if(foundWidgetFlag == True):
                #delete all widgets between the group index and the found widget index
                while(groupIndex < foundWidgetIndex):
                    self.ChildGroupWidgets[groupIndex].destroy()
                    self.ChildGroupWidgets.pop(groupIndex)
                    foundWidgetIndex -= 1
            else:#if the widget wasnt found, create and add it
                newChildWidget = GroupWidget(parentWidget =self.RightScrollFrame.InnerFrame, Group = self.parentGroup.childGroups[groupIndex], LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
                newChildWidget.bind("<Button-1>", self.selectChildWidget)
                self.ChildGroupWidgets.insert(groupIndex, newChildWidget)

            groupIndex += 1
        
        #the above alg wont delete widgets at the end of the list that do not have a corresponding item
        childGroupLen = len(self.parentGroup.childGroups)
        childWidgetLen = len(self.ChildGroupWidgets)
        if(childGroupLen < childWidgetLen):
            while(childGroupLen < childWidgetLen):
                self.ChildGroupWidgets.pop().destroy()
                childWidgetLen -=1
             
        #clean up work, re-grid the remaining widgets
        for index in range(0, childWidgetLen):
           #self.RightScrollFrame.InnerFrame.rowconfigure(index, weight=1)
           #self.RightScrollFrame.InnerFrame.columnconfigure(index, weight=1)
           self.ChildGroupWidgets[index].grid(row=index, column=0, sticky="nsew")

        #reset selected
        self.SelectedChildWidget = None

    ######### User Interaction Functions ########

    #selects a child widget and highlights it, while unhighlighting the previously selected child widget
    def selectChildWidget(self, event)->None:
        if(self.SelectedChildWidget != None):                
            self.SelectedChildWidget.configure(bg="lightblue")
        self.SelectedChildWidget = event.widget
        self.SelectedChildWidget.configure(bg="yellow")

    #delete the group of the selected child widget, and update the GUI
    def deleteChildWidget(self, event)->None:
        if(self.SelectedChildWidget != None):
            self.parentGroup.deleteChild(self.SelectedChildWidget.Group)
            self.updateLeft()
            self.updateRight()


    #allows user to "drop down" a tier in the tree and sort the selected child group
    def sortChildGroup(self, event)->None:
        if(self.SelectedChildWidget != None):
            self.parentGroup = self.SelectedChildWidget.Group
            self.parentGroup.loadGroupChildren()
            self.populateLeft()
            self.populateRight()

    #allows the user to go back up a tier in the tree and sort the current parent group
    def sortParentGroup(self, event)->None:
        if(self.parentGroup.parent != None):
            #sets the current parent group to the parent of the current parent
            #essentially going "up" one level in the tree
            self.parentGroup = self.parentGroup.parent
            self.populateLeft()
            self.populateRight()

    #create new child button
    def CreateChildGroup(self, event)->None:
        self.parentGroup.createChildGroup()
        self.populateRight()

    ########## Menu Bar Functions ########

    #save all of the changes to the database
    def commitGroups(self)-> None:
        #write to the db
        """
        LB.writeTreeBoot(rootGroup=self.RootGroup, 
                        databaseDirect=self.DirectoriesObj.getDataBaseDirect(),
                        oldFileDirect=self.DirectoriesObj.getOldDataDirect(),
                        newFileDirect=self.DirectoriesObj.getNewDataDirect())"""
        self.DataBaseObj.writeGroups(self.RootGroup)

        self.DataBaseObj.writeLabels(labelsObj=self.LabelsObj)
        
        #reset GUI to the root group, and reload the root groups children
        self.parentGroup = self.RootGroup
        self.RootGroup.childrenLoaded = False
        self.RootGroup.childGroups = []
        self.RootGroup.loadGroupChildren()
        self.populateLeft()
        self.populateRight()

    def commitExit(self)-> None:
        self.commitGroups()
        self.MainPage.destroy()

    ##### Set Directories #####
    def setImageFolder(self)->None:
        if(self.DirectoriesObj.getOldDataDirect() == None):
            #make sure user meant to change the image folder
            if(not messagebox.askyesno(title="Change Image Folder?", message="Are you sure?")):
                return

            #prompt user to save the current sorted data to the database
            if(messagebox.askyesno(title="Commit Sorted Data?", message="Would you like to commit sorted data before changing the image folder?")):
                self.commitGroups()

        #prompt and set the old directory
        self.DirectoriesObj.setOldDataDirect()

        #Create new root group and populate it
        self.RootGroup = LB.initializeGroupTree(directoryObj = self.DirectoriesObj, DB=self.DataBaseObj)
        self.parentGroup = self.RootGroup

        self.populateLeft()
        self.populateRight()
    
    def setSaveFolder(self)->None:
        self.DirectoriesObj.setNewDataDirect()

    def setDataBaseFolder(self)->None:
        if(messagebox.askyesno(title="Commit Sorted Data?", message="Would you like to commit sorted data before changing the database?")):
            self.commitGroups()

        self.DataBaseObj.setDataBaseDirect()

        #Create new root group and populate it
        self.RootGroup = LB.initializeGroupTree(directoryObj = self.DirectoriesObj, DB=self.DataBaseObj)
        self.parentGroup = self.RootGroup
        
        self.populateLeft()
        self.populateRight()

    ########### Protocols ###########
    #handle the window close protocol
    def onClose(self)-> None:
        if(messagebox.askyesno(title="Exit?", message="Are you sure you want to exit?")):
            if(messagebox.askyesno(title="Commit Sorted Data?", message="Would you like to commit sorted data before exiting?")):
                self.commitGroups()
            self.MainPage.destroy()




                



#widget class that displays a group and its children
class GroupWidget(tk.Frame):
    
    def __init__(self, ParentWidget, Group, LabelsObj, width=1200, height=1200, itemPack="top", maxItemHeight=800, maxItemWidth=800, maxItemWidgets = 10):
        super().__init__(ParentWidget, bg="lightblue", bd=2, relief="groove", width=width, height=height)
        self.packType = itemPack
        self.Group = Group
        self.maxItemHeight = maxItemHeight
        self.maxItemWidth = maxItemWidth
        self.ItemWidgetList = []
        self.maxItemWidgets = maxItemWidgets #max number of item widgets to be shown

        #the position of each each item widget in the scroll frame
        self.itemWidgetYPos: list[int] = [0]*len(self.Group.items)

        #scroll height for the itemWidgets (uses virtual scrolling)
        self.scrollHeight: int = 1
        self.itemRenderPending = False

        self.Labels = LabelsObj

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        #scroll frame that holds the item widgets
        self.ItemScrollFrame: ScrollableFrame = ScrollableFrame(self, width=width, height=height)
        #bind the callback, this allows us to add/subtract item widgets when the user scrolls
        self.ItemScrollFrame.setScrollCallBack(self.scheduleItemRender)

        def labelKindSelected(event)-> None:
            comboBox = event.widget
            labelType = comboBox.get()

            if(labelType == "subjects"):
                self.LabelsComboBox["values"] = self.Labels.subjectLabels
            elif(labelType == "creator"):
                self.LabelsComboBox["values"] = self.Labels.creatorLabels
            elif(labelType == "tags"):
                self.LabelsComboBox["values"] = self.Labels.tagLabels
            
            self.LabelsComboBox.set("Unknown")

        #combo boxes
        self.LabelKindComboBox = ttk.Combobox(self, values=["subjects", "creator", "tags"], state="readonly")
        self.LabelKindComboBox.set("Labels")
        
        self.LabelKindComboBox.bind("<<ComboboxSelected>>", labelKindSelected)

        self.LabelsComboBox = ttk.Combobox(self, values=self.Labels.subjectLabels)
        self.LabelsComboBox.set("Unknown")

        #this handles both selecting a label and if a new label is typed in
        def labelSelected(event)-> None:
            labelType = self.LabelKindComboBox.get()
            labelToAdd = self.LabelsComboBox.get()

            #address labels obj and then add to group
            if(labelType == "subjects"):
                self.Labels.putSubject(labelToAdd)
                self.Group.addSubjectLabel(labelToAdd)
            elif(labelType == "creator"):
                self.Labels.putCreator(labelToAdd)
                self.Group.addCreatorLabel(labelToAdd)
            elif(labelType == "tags"):
                self.Labels.putTag(labelToAdd)
                self.Group.addTagLabel(labelToAdd)
        
            self.setLabelText()#update label text
        
        self.AddLabelButton = tk.Button(self, text="Add Label")
        self.AddLabelButton.bind("<Button-1>", labelSelected)

            ## remove button
        def removeLabel(event)-> None:
            labelType = self.LabelKindComboBox.get()
            labelToAdd = self.LabelsComboBox.get()

            #address labels obj and then add to group
            if(labelType == "subjects"):
                self.Group.removeSubjectLabel(labelToAdd)
            elif(labelType == "creator"):
                self.Group.removeCreatorLabel(labelToAdd)
            elif(labelType == "tags"):
                self.Group.removeTagLabel(labelToAdd)
        
            self.setLabelText()#update label text

        self.RemoveLabelButton = tk.Button(self, text="Remove Label")
        self.RemoveLabelButton.bind("<Button-1>", removeLabel)

        #if this is the widget for the root group, do not display comboboxes/buttons
        if(self.Group.parent != None):
            self.LabelKindComboBox.grid(row=0, column=0)
            self.LabelsComboBox.grid(row=1, column=0)
            self.AddLabelButton.grid(row=2, column=0)
            self.RemoveLabelButton.grid(row=3, column=0)


        #label
        self.LabelsWidget = tk.Label(self, text='')
        self.setLabelText()
        self.LabelsWidget.grid(row=4, column=0)

        #grid scroll frame
        self.ItemScrollFrame.grid(row=5, column=0, sticky="nsew")

        #import items
        self.setItemWidgets()

    ######## Drag and Drop Call backs #########
    def dnd_accept(self, source, event):
        return self#this is recquired, typically is used to check if object being dropped is a valid one
        
    def dnd_enter(self, source, event):
        #self.configure(bg="lightgreen")#change later
        ""
        
    def dnd_leave(self, source, event):
        #self.configure(bg="lightblue")
        """"""

    def dnd_motion(self, source, event):
        """"""

    def dnd_commit(self, source, event):
        self.Group.addItem(source.item)
        self.setItemWidgetYPos()
        self.renderItemWidgets()

    ######## Update Widget Functions ########

    def deleteItemWidgets(self)-> None:
        #inefficient, need to rewrite later
        for itemWidget in self.ItemWidgetList:
            itemWidget.destroy()

        self.ItemWidgetList = []


    #iterated through the items and item widgets, deleting or creating widgets as needed to match the items
    def setItemWidgets(self)-> None:
        for _ in range(len(self.ItemWidgetList)):
            self.ItemWidgetList.pop(0).destroy()

        for x in range(self.maxItemWidgets):
            if(x > len(self.Group.items)):
                break
            newItemWidget = ItemWidget(self.ItemScrollFrame.InnerFrame, self, None)
            self.ItemWidgetList.append(newItemWidget)

        self.setItemWidgetYPos()
        self.renderItemWidgets()

    #set the item widget locations, also updates scrollheight and scroll frames inner frame/canvas
    def setItemWidgetYPos(self):
        itemLen: int = len(self.Group.items)
        posLen: int = len(self.itemWidgetYPos)

        currPos: int = 0

        if(itemLen != posLen ):
            if(itemLen > posLen):
                self.itemWidgetYPos.extend([0] * (itemLen - posLen))
            elif(itemLen < posLen):
                self.itemWidgetYPos = self.itemWidgetYPos[:itemLen]

        for itemIndex, item in enumerate(self.Group.items):
            self.itemWidgetYPos[itemIndex] = currPos
            currPos += item.getHeight() + 50

        #set Scroll Height
        self.scrollHeight = currPos

        #update the scroll frames inner frame/canvas height
        self.ItemScrollFrame.InnerFrame.configure(height=currPos)
        self.ItemScrollFrame.InnerCanvas.configure(scrollregion=(0, 0, 1, currPos))



    #updates the scroll region if necessary, what items are loaded into widgets, and widget placement in the scroll region
    def renderItemWidgets(self):
        self.itemRenderPending = False

        #get scroll pos
        topPerc, _ = self.ItemScrollFrame.InnerCanvas.yview()

        #position (in pixels) of the top/bottom of the visible viewport
        topWidgetPos: int = int(topPerc * self.scrollHeight)

        #items have variable heights, so topPerc/bottomPerc (fractions of pixel height) do not map
        #linearly to item indices - look up the index whose pixel position matches instead
        topIndex: int = max(0, bisect.bisect_right(self.itemWidgetYPos, topWidgetPos) - 1)

        #items still in view keep the widget they already have so their image isn't reloaded -
        endIndex: int = min(len(self.Group.items), topIndex + len(self.ItemWidgetList))
        neededIndices = list(range(topIndex, endIndex))

        #map each needed item index to a widget, reusing existing widgets where possible
        widgetForIndex: dict = {}#maps item index to the widget displaying it
        freeWidgets: list = []#widgets that are not currently mapped to any needed item index
        for widget in self.ItemWidgetList:
            matchedIndex = None
            if(widget.item is not None):
                for candidateIndex in neededIndices:
                    if(candidateIndex not in widgetForIndex and self.Group.items[candidateIndex] == widget.item):
                        matchedIndex = candidateIndex
                        break
            #if no match was found, this widget is free to be reused
            if(matchedIndex is None):
                freeWidgets.append(widget)
            else:
                widgetForIndex[matchedIndex] = widget

        #for needed items that do not have a widget yet, assign a free widget
        for itemIndex in neededIndices:
            if(itemIndex not in widgetForIndex):
                widget = freeWidgets.pop()
                widget.setItem(self.Group.items[itemIndex])
                widgetForIndex[itemIndex] = widget

        #any widgets left over are past the end of the item list, hide them
        for widget in freeWidgets:
            widget.place_forget()

        #place the widgets at their corresponding positions
        for itemIndex, widget in widgetForIndex.items():
            widget.place(x=0, y = self.itemWidgetYPos[itemIndex], relwidth=1)

        

    #throttles render calls to one per frame (~60fps) instead of firing on every scroll event
    def scheduleItemRender(self):
        if(not self.itemRenderPending):
            self.itemRenderPending = True
            self.after(16, self.renderItemWidgets)



    #creates/sets the str for the label widget
    def setLabelText(self)-> None:
        if(self.Group.parent != None):
            textStr:str = f'SUBJECTS: {" ".join(self.Group.subjects)} CREATORS: {" ".join(self.Group.creator)} TAGS: {" ".join(self.Group.tags)}'
            self.LabelsWidget["text"] = textStr
        else:
            self.LabelsWidget["text"] = "Root Group"

    #adjusts the minItemIndex to better fit the widget list
    #ex: if minItemIndex is 3, maxItemWidgets = 5, and the last index of the item list is 5, then set minItemIndex to 0
    #so that the entire widget list is shown
    def adjustMinItem(self)-> None:
        adjustment: int = (len(self.Group.items) -1) - (self.minItemIndex + self.maxItemWidgets -1)

        if(adjustment < 0):
            self.minItemIndex += adjustment
            if(self.minItemIndex < 0):
                self.minItemIndex = 0
        
        

#widget class that displays a single item
class ItemWidget(tk.Frame):
    def __init__(self, parent, groupWidget, item):

        super().__init__(parent, bg="lightblue", bd=2, relief="groove")
        self.groupWidget = groupWidget
        self.item = item

        self.WidgetLabel = tk.Label(self)
        self.WidgetLabel.pack(padx = 5, pady=5, fill="y", expand=True)

        self.text = tk.Label(self)
        self.text.pack(padx=20, pady=5)

        self.renderWidget()

    def setItem(self, setItem:LB.Item)->None:
        self.item = setItem
        self.renderWidget()

    def renderWidget(self)->None:
        if(self.item == None):
            return
        
        IMG = self.item.getIMG()
        if(IMG != None):
            self.WidgetLabel.config(image=IMG, text="", width=self.item.maxItemHeight)
            self.WidgetLabel.image = IMG
        
            self.text.config(text=self.item.fileName)

            #bind callbacks
            self.WidgetLabel.bind("<ButtonPress-1>", self.onDragStart)
            self.bind("<ButtonPress-1>", self.onDragStart)
        else:
            self.WidgetLabel.config(text=f"Unable to find image: {self.item.directory}{self.item.fileName}", width=self.item.maxItemHeight)



    ###### call backs for drag and drop features ######
    def onDragStart(self, event):
        dnd.dnd_start(source=self, event=event)
        
    def dnd_end(self, target, event):
        #if item was dropped into a groupWidget
        if(isinstance(target, GroupWidget)):
            if(self.groupWidget != target):
                self.groupWidget.Group.removeItem(self.item)
                self.groupWidget.setItemWidgetYPos()
                self.groupWidget.renderItemWidgets()
        elif(isinstance(target, ItemWidget)):
            #if the two items are not in the same group widget
            if(self.groupWidget != target.groupWidget):
                #remove the item from the old widget
                self.groupWidget.Group.removeItem(self.item)
                #re-populate widgets
                self.groupWidget.setItemWidgetYPos()
                self.groupWidget.renderItemWidgets()

    #Drop features
    def dnd_accept(self, source, event):
        return self#this is recquired, typically is used to check if object being dropped is a valid one
        
    def dnd_enter(self, source, event):
        self.configure(bg="lightgreen")#change later
        ""
        
    def dnd_leave(self, source, event):
        self.configure(bg="lightblue")
        ""

    def dnd_motion(self, source, event):
        ""

    def dnd_commit(self, source, event):
        self.configure(bg="lightblue")
        self.groupWidget.Group.addItemInFrontOf(self.item, source.item)#add item into the group
        #re-populate widgets
        self.groupWidget.setItemWidgetYPos()
        self.groupWidget.renderItemWidgets()


class ScrollableFrame(tk.Frame):
    def __init__(self, ParentWidget, width=800, height=1200):
        super().__init__(ParentWidget, bg="lightblue", bd=2, relief="groove", width=width, height=height)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        self.InnerCanvas = tk.Canvas(self)
        #self.InnerCanvas.pack(side="left", fill="both", expand=True)
        self.InnerCanvas.grid(row=0, column=0, sticky="nsew")

        self.ScrollBar = ttk.Scrollbar(self, orient="vertical", command=self.onScroll)
        self.ScrollBar.grid(row=0, column=1, sticky="ns")

        #function, does not redraw the window but makes other adjustments to properly update the window
        self.ScrollCallBack = None 

        self.InnerCanvas.configure(yscrollcommand=self.ScrollBar.set)
        self.InnerCanvas.bind("<Configure>", self.resizeInnerFrame)

        #all widgets will sit inside of this inner frame
        self.InnerFrame = tk.Frame(self.InnerCanvas)
        self.InnerFrame.bind("<Configure>", self.updateRegion)
        self.InnerFrame.columnconfigure(0, weight=1)#we are assuming the inner frame is populate with grid

        self.Window = self.InnerCanvas.create_window((0,0), window=self.InnerFrame, anchor="nw", width=self.winfo_width())

        self.InnerCanvas.bind("<Enter>", self.onEnter)
        self.InnerCanvas.bind("<Leave>", self.onLeave)


    #updates the window on scroll
    def updateRegion(self, event):
        self.InnerCanvas.configure(scrollregion=self.InnerCanvas.bbox("all"))
        #must use the canvas's own width, not the frame's (which also includes the scrollbar column),
        #otherwise the inner content is stretched under the scrollbar causing it to overlap
        self.InnerCanvas.itemconfigure(self.Window, width=self.InnerCanvas.winfo_width())

    #update on window resize
    def resizeInnerFrame(self, event):
        self.InnerCanvas.itemconfigure(self.Window, width=event.width)

    def setScrollCallBack(self, callBackFunc):
        self.ScrollCallBack = callBackFunc

    #updates the scrollbar and makes callback
    def onScroll(self, *args):
        #scrolls canvas
        self.InnerCanvas.yview(*args)

        if(self.ScrollCallBack != None):
            self.ScrollCallBack()

    #on user scroll wheel, for both linux and windows
    def onScrollWheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.onScroll("scroll", 1, "units")
        if event.num == 4 or event.delta > 0:
            self.onScroll("scroll", -1, "units")

    def onEnter(self, event):
        self.InnerCanvas.bind_all("<MouseWheel>", self.onScrollWheel)# Windows
        self.InnerCanvas.bind_all("<Button-4>", self.onScrollWheel)# Linux scroll up
        self.InnerCanvas.bind_all("<Button-5>", self.onScrollWheel)# Linux scroll down

    def onLeave(self, event):
        self.InnerCanvas.unbind_all("<MouseWheel>")
        self.InnerCanvas.unbind_all("<Button-4>")
        self.InnerCanvas.unbind_all("<Button-5>")



if __name__ == "__main__":
    main()