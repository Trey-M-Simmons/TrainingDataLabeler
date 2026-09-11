"""
Author: Trey Simmons
Created: 3/17/26
Date of Last Edit: 9/11/26
Description: This is the main file for the data labeling program. It contains the GUI and the main function that run the program. 
"""


import tkinter as tk
from tkinter import dnd
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
import LabelerBackend as LB
import pandas as pd
import os

def main():
    MainPage = tk.Tk()
    LabelsDF = pd.read_csv("./DataBase/Labels.csv")
    LabelsObj = Labels(LabelsDF)

    SORT(MainPage, LabelsObj)


######################### SORTING SECTION ###########################
def SORT(MainPage, LabelsObj)->None:
    #get directory from user
    directoryStr = filedialog.askdirectory(title="Select an Image or Video Folder")
    Directories = LB.Directories()
    Directories.setOldDataDirect(directoryStr)
    Directories.setNewDataDirect(directoryStr)

    LB.setDataBaseFolder(Directories)

    RootGroup = LB.initializeGroupTree(directoryObj = Directories)
    
    SortPage = sortPage(MainPage=MainPage, LabelsObj=LabelsObj, rootGroup=RootGroup, DirectoriesObj=Directories)
    MainPage.title("Data Labeler")
    MainPage.geometry("1500x1500")
    MainPage.mainloop()

#Main page that the user will see, the left side of the page will have the parent group/items while the right side will have 
# all of the children groups of the current parent. The user will then be able to drag and drop items from the parent group into the child groups, 
# as well as create new child groups and delete child groups. The user may choose to sort a child group, making that child the new parent group and 
# that child's children the new current child groups.
class sortPage:
    def __init__(self, MainPage, LabelsObj, rootGroup, DirectoriesObj):

        self.LabelsObj = LabelsObj
        self.parentGroup = rootGroup
        self.RootGroup = rootGroup
        self.ParentGroupWidget : GroupWidget = None
        self.ChildGroupWidgets = []
        self.SelectedChildWidget : GroupWidget = None

        #database and file directories
        self.DirectoriesObj = DirectoriesObj
        self.oldDirectory = "./Testimgs/"
        self.newDirectory = self.oldDirectory
        self.csvDirectory = "./DataBase/"


        #menu bar
        #here for now, will be moved later
        self.MenuBar = tk.Menu(MainPage)

        self.FileMenu = tk.Menu(self.MenuBar, tearoff=0)
        self.FileMenu.add_command(label="Open Image Folder", command=self.setImageFolder)

        self.MenuBar.add_cascade(label="File", menu=self.FileMenu)


        self.SortMenu = tk.Menu(self.MenuBar, tearoff=0)
        self.SortMenu.add_command(label="Commit to Database", command=self.commitGroups)

        self.MenuBar.add_cascade(label="Commmit", menu=self.SortMenu)

        MainPage.config(menu=self.MenuBar)

        MainPage.columnconfigure(0, weight=1)
        MainPage.columnconfigure(1, weight=1)
        MainPage.rowconfigure(0, weight=1)



        #create left/parent frame
        self.LeftFrame = tk.Frame(MainPage, width=800, height=500)  #outer most frame
        #self.LeftFrame.pack(side="left", fill="both", expand=True)
        self.LeftFrame.grid(row=0, column=0, sticky="NSEW")
        
        self.LeftFrame.columnconfigure(0, weight=1)
        
        self.SortGroupAbove = tk.Button(self.LeftFrame, text="Back")
        self.SortGroupAbove.pack(pady=26)
        self.SortGroupAbove.bind("<Button-1>", self.sortParentGroup)

        #allows the widgets inside of self.LeftScrollFrame.InnerFrame to be vertically scrolled
        self.LeftScrollFrame = ScrollableFrame(self.LeftFrame, width=1200, height=500)
        self.LeftScrollFrame.pack(side="left", fill="both", expand=True)
        

        #create right/child frame
        self.RightFrame = tk.Frame(MainPage, width=1200, height=500)
        #self.RightFrame.pack(side="right", fill="both", expand=True)
        self.RightFrame.grid(row=0, column=1, sticky="NSEW")

        self.NewGroupButton = tk.Button(self.RightFrame, text="Create New Group")
        self.NewGroupButton.pack()
        self.NewGroupButton.bind("<Button-1>", self.CreateChildGroup)

        self.DeleteGroupButton = tk.Button(self.RightFrame, text="Delete Selected Group")
        self.DeleteGroupButton.pack()
        self.DeleteGroupButton.bind("<Button-1>", self.deleteChildWidget)

        self.SortGroupButton = tk.Button(self.RightFrame, text="Sort Child Group")
        self.SortGroupButton.pack()
        self.SortGroupButton.bind("<Button-1>", self.sortChildGroup)

        self.RightScrollFrame = ScrollableFrame(self.RightFrame, width=1200, height=500)
        self.RightScrollFrame.pack(side="right", fill="both", expand=True)
        
        #populate the left and right sides
        self.populateLeft()
        self.populateRight()

    ######## GUI Widget Setting Functions ########

    #populate the left side of the GUI with a GroupWidget of the parent group and its item widgets
    def populateLeft(self)->None:
        if(self.ParentGroupWidget == None):
            self.ParentGroupWidget = GroupWidget(self.LeftScrollFrame.InnerFrame, self.parentGroup, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900)
            self.ParentGroupWidget.pack(fill="y")
        else:
            if(self.ParentGroupWidget.Group != self.parentGroup):#if the parent group has changed, delete old widgets
                self.ParentGroupWidget.deleteItemWidgets()
                self.ParentGroupWidget.Group = self.parentGroup

            self.ParentGroupWidget.setLabelText()
            self.ParentGroupWidget.setItemWidgets()
            
    #set the item widgets of the parent group widget
    def updateLeft(self)->None:
        if(self.ParentGroupWidget != None):
            self.ParentGroupWidget.setItemWidgets()

    #populate the right side of the GUI with GroupWidgets of the current child groups 
    def populateRight(self)->None:
        for childWidget in self.ChildGroupWidgets:
            childWidget.destroy()
        
        self.ChildGroupWidgets = []
        
        #for child in self.parentGroup.childGroups:
        for childIndex in range(0, len(self.parentGroup.childGroups)):
            child = self.parentGroup.childGroups[childIndex]
            newChildWidget = GroupWidget(self.RightScrollFrame.InnerFrame, child, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
            #newChildWidget.pack(fill="y")
            newChildWidget.grid(row=childIndex, column=0)
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
                newChildWidget = GroupWidget(self.RightScrollFrame.InnerFrame, self.parentGroup.childGroups[groupIndex], LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
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
           self.ChildGroupWidgets[index].grid(row=index, column=0)

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
        LB.writeTreeBoot(rootGroup=self.RootGroup, 
                        databaseDirect=self.DirectoriesObj.getDataBaseDirect(),
                        oldFileDirect=self.DirectoriesObj.getOldDataDirect(),
                        newFileDirect=self.DirectoriesObj.getNewDataDirect())
        
        #reset GUI to the root group, and reload the root groups children
        self.parentGroup = self.RootGroup
        self.RootGroup.childrenLoaded = False
        self.RootGroup.loadGroupChildren()
        self.populateLeft()
        self.populateRight()

    ##### Set Directories #####
    def setImageFolder(self)->None:
        #prompt user to save the current sorted data to the database
        if(messagebox.askyesno(title="Would you like to save sorted data to the database?", message="Would you like to set a save location for the sorted files?")):
            self.commitGroups()

        #prompt and set the old directory
        self.DirectoriesObj.setOldDataDirect(filedialog.askdirectory(title="Select an Image or Video Folder"))

        #Create new root group and populate it
        self.RootGroup = LB.initializeGroupTree(directoryObj = self.DirectoriesObj)
        self.parentGroup = self.RootGroup

        self.populateLeft()
        self.populateRight()
    
    def setSaveFolder(self)->None:
        self.DirectoriesObj.setNewDataDirect(filedialog.askdirectory(title="Select Save Location"))

    def setDataBaseFolder(self)->None:
        LB.setDataBaseFolder(self.DirectoriesObj)




                



#widget class that displays a group and its children
class GroupWidget(tk.Frame):
    
    def __init__(self, ParentWidget, Group, LabelsObj, width=800, height=1200, itemPack="top", maxItemHeight=800, maxItemWidth=800, maxItemWidgets = 30):
        super().__init__(ParentWidget, bg="lightblue", bd=2, relief="groove", width=width, height=height)
        self.packType = itemPack
        self.Group = Group
        self.maxItemHeight = maxItemHeight
        self.maxItemWidth = maxItemWidth
        self.ItemWidgetList = []
        self.maxItemWigets = maxItemWidgets #max number of item widgets to be shown

        self.Labels = LabelsObj

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
        ""

    def dnd_motion(self, source, event):
        """"""

    def dnd_commit(self, source, event):
        self.Group.addItem(source.item)
        self.setItemWidgets()

    ######## Update Widget Functions ########

    def deleteItemWidgets(self)-> None:
        #inefficient, need to rewrite later
        for itemWidget in self.ItemWidgetList:
            itemWidget.destroy()

        self.ItemWidgetList = []

    

    #iterated through the items and item widgets, deleting or creating widgets as needed to match the items
    #Very similar to updateRight() in SORTPAGE
    #CHANGE SYSTEM LATER IN ORDER TO CLEAN UP .configure jitteryness
    def setItemWidgets(self)-> None:
        itemIndex = 0
        while(itemIndex < self.maxItemWigets - 1):
            if(itemIndex >= len(self.Group.items)):
                break

            #check if the current item has a corresponding widget
            foundWidgetIndex = 0
            foundWidgetFlag = False
            if(len(self.ItemWidgetList) != 0):#makes sure that there are widgets
                for widgetIndex in range(itemIndex, len(self.ItemWidgetList)):
                    if(self.Group.items[itemIndex] == self.ItemWidgetList[widgetIndex].item):
                        foundWidgetFlag = True
                        foundWidgetIndex = widgetIndex
                        break
            
            #if the widget was found, delete widgets that no longer have a corresponding item
            if(foundWidgetFlag == True):
                #delete all widgets between the item index and the found widget index
                for deleteIndex in range(itemIndex, foundWidgetIndex):
                    self.ItemWidgetList[deleteIndex].destroy()
                    self.ItemWidgetList.pop(deleteIndex)
            else:#if the widget wasnt found, create and add it
                newItemWidget = ItemWidget(self, self.Group.items[itemIndex], maxItemWidth=self.maxItemWidth, maxItemHeight=self.maxItemHeight)
                self.ItemWidgetList.insert(itemIndex, newItemWidget)
                #newItemWidget.grid(row=itemIndex + 1, column=0)

            itemIndex += 1
        
        #clean up work, re-grid the remaining widgets
        for index in range(0, len(self.ItemWidgetList)):
            self.ItemWidgetList[index].grid(row=index + 6, column=0)
            #note: the +6 is so that the item widgets are not in the same row as the buttons/labels

    #creates/sets the str for the label widget
    def setLabelText(self)-> None:
        if(self.Group.parent != None):
            textStr = "SUBJECTS: "
            for subjLabel in self.Group.subjects:
                textStr += subjLabel + " "

            textStr += "CREATORS: "
            for creatLabel in self.Group.creator:
                textStr += creatLabel + " "
            
            textStr += "TAGS: "
            for tag in self.Group.tags:
                textStr += tag + " "

            self.LabelsWidget["text"] = textStr
        else:
            self.LabelsWidget["text"] = "Root Group"

#widget class that displays a single item
class ItemWidget(tk.Frame):
    def __init__(self, parent, item, maxItemHeight=400, maxItemWidth=300):

        super().__init__(parent, bg="lightblue", bd=2, relief="groove")
        self.groupWidget = parent
        self.item = item

        self.WidgetLabel = None

        if os.path.exists(item.directory + item.fileName):
            PIL_IMG = Image.open(item.directory + item.fileName)
            #resize
            PIL_IMG.thumbnail((maxItemWidth, maxItemHeight), Image.Resampling.LANCZOS)

            tk_IMG = ImageTk.PhotoImage(PIL_IMG)
            self.WidgetLabel = tk.Label(self, image=tk_IMG, text="DUED", width=maxItemWidth)
            self.WidgetLabel.image = tk_IMG
            self.WidgetLabel.pack(padx = 5, pady=5, fill="y", expand=True)

            self.text = tk.Label(self, text=item.fileName)
            self.text.pack(padx=20, pady=5)
        else:
            self.WidgetLabel = tk.Label(self, text="Unable to find image", width=maxItemWidth)

        self.WidgetLabel.bind("<ButtonPress-1>", self.onDragStart)
        self.bind("<ButtonPress-1>", self.onDragStart)




    ###### call backs for drag and drop features ######
    def onDragStart(self, event):
        dnd.dnd_start(source=self, event=event)

        
    def dnd_end(self, target, event):
        #if item was dropped into a groupWidget
        if(isinstance(target, GroupWidget)):
            if(self.groupWidget != target):
                self.groupWidget.Group.removeItem(self.item)
        elif(isinstance(target, ItemWidget)):
            #if the two items are not in the same group widget
            if(self.groupWidget != target.groupWidget):
                #remove the item from the old widget
                self.groupWidget.Group.removeItem(self.item)
        self.groupWidget.setItemWidgets()#re-populate widgets

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
        self.groupWidget.Group.addItemInFrontOf(self.item, source.item)
        self.groupWidget.setItemWidgets()


class ScrollableFrame(tk.Frame):
    def __init__(self, ParentWidget, width=800, height=1200, itemPack="top", maxItemHeight=800, maxItemWidth=800):
        super().__init__(ParentWidget, bg="lightblue", bd=2, relief="groove", width=width, height=height)
        
        self.InnerCanvas = tk.Canvas(self)
        self.InnerCanvas.pack(side="left", fill="both", expand=True)

        self.ScrollBar = ttk.Scrollbar(self, orient="vertical", command=self.InnerCanvas.yview)
        self.ScrollBar.pack(side="right", fill="y")

        self.InnerCanvas.configure(yscrollcommand=self.ScrollBar.set)

        #all widgets will sit inside of this inner frame
        self.InnerFrame = tk.Frame(self.InnerCanvas)
        self.InnerFrame.bind("<Configure>", self.updateRegion)

        self.Window = self.InnerCanvas.create_window((0,0), window=self.InnerFrame, anchor="nw", width=self.winfo_width())


    def updateRegion(self, event):
        self.InnerCanvas.configure(scrollregion=self.InnerCanvas.bbox("all"))
        self.InnerCanvas.itemconfigure(self.Window, width=self.winfo_width())


#keeps track of various page state data such as labels
class Labels():
    def __init__(self, Df):
        #all of the label options for each label
        #note: the most recently used option should be at the top of the list
        self.subjectLabels = []
        self.creatorLabels = []
        self.tagLabels = []

        self.LabelsCSV = Df

        self.getLabels()

    #pull the labels from the df
    def getLabels(self)->None:
        self.subjectLabels = self.LabelsCSV["subjects"].dropna().to_list()
        self.creatorLabels = self.LabelsCSV["creators"].dropna().to_list()
        self.tagLabels = self.LabelsCSV["tags"].dropna().to_list()

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

if __name__ == "__main__":
    main()