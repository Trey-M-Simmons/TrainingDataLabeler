
import tkinter as tk
from tkinter import dnd
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import LabelerBackend as LB
import pandas as pd
import os






def main():
    MainPage = tk.Tk()
    LabelsDF = pd.read_csv("F:/bac files/ImageLabeler/DataBase/Labels.csv")
    LabelsObj = Labels(LabelsDF)

    SORT(MainPage, LabelsObj)




########## SORTING SECTION ##############
def SORT(MainPage, LabelsObj):

    directoryStr = "F:/bac files/ImageLabeler/Testimgs"
    #directoryStr =
    RootGroup = LB.Group()
    RootGroup.populateItems(LB.getAllFiles(directory=directoryStr), directoryStr + "/")

    SortPage = sortPage(MainPage=MainPage, LabelsObj=LabelsObj, rootGroup=RootGroup)

    MainPage.geometry("1000x1000")
    MainPage.mainloop()

class sortPage:
    def __init__(self, MainPage, LabelsObj, rootGroup):

        self.LabelsObj = LabelsObj
        self.parentGroup = rootGroup
        self.RootGroup = rootGroup
        self.ParentGroupWidget : GroupWidget = None
        self.ChildGroupWidgets = []
        self.SelectedChildWidget :GroupWidget = None

        #database and file directories
        self.oldDirectory = "F:/bac files/ImageLabeler/Testimgs/"
        self.newDirectory = self.oldDirectory
        self.csvDirectory = "F:/bac files/ImageLabeler/DataBase/"


        #menu bar
        #here for now, will be moved later
        self.MenuBar = tk.Menu(MainPage)

        self.FileMenu = tk.Menu(self.MenuBar, tearoff=0)
        self.FileMenu.add_command(label="Open File", command=self.setImageFolder)

        self.MenuBar.add_cascade(label="File", menu=self.FileMenu)


        self.SortMenu = tk.Menu(self.MenuBar, tearoff=0)
        self.SortMenu.add_command(label="Commit and Exit", command=self.commitGroups)

        self.MenuBar.add_cascade(label="Exit", menu=self.SortMenu)

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


    def populateLeft(self):
        if(self.ParentGroupWidget == None):
            self.ParentGroupWidget = GroupWidget(self.LeftScrollFrame.InnerFrame, self.parentGroup, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900)
            self.ParentGroupWidget.pack(fill="y")
        else:
            if(self.ParentGroupWidget.Group != self.parentGroup):#if the parent group has changed, delete old widgets
                self.ParentGroupWidget.deleteItemWidgets()
                self.ParentGroupWidget.Group = self.parentGroup

            self.ParentGroupWidget.setLabelText()
            self.ParentGroupWidget.setItemWidgets()
            

    def updateLeft(self):
        if(self.ParentGroupWidget != None):
            self.ParentGroupWidget.setItemWidgets()

    def populateRight(self):
        for childWidget in self.ChildGroupWidgets:
            childWidget.destroy()
        
        self.ChildGroupWidgets = []
        
        for child in self.parentGroup.childGroups:
            newChildWidget = GroupWidget(self.RightScrollFrame.InnerFrame, child, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
            newChildWidget.pack(fill="y")
            newChildWidget.bind("<Button-1>", self.selectChildWidget)
            self.ChildGroupWidgets.append(newChildWidget)

        #reset selected
        self.SelectedChildWidget = None

    def updateRight(self):
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
                for deleteIndex in range(groupIndex, foundWidgetIndex):
                    self.ChildGroupWidgets[deleteIndex].destroy()
                    self.ChildGroupWidgets.pop(deleteIndex)
            else:#if the widget wasnt found, create and add it
                newChildWidget = GroupWidget(self.RightScrollFrame.InnerFrame, self.parentGroup.childGroups[groupIndex], LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
                newChildWidget.bind("<Button-1>", self.selectChildWidget)
                self.ChildGroupWidgets.insert(groupIndex, newChildWidget)

            groupIndex += 1
        
        #clean up work, re-grid the remaining widgets
        for index in range(0, len(self.ChildGroupWidgets)):
           self.ChildGroupWidgets[index].grid(row=index, column=0)

        #reset selected
        self.SelectedChildWidget = None

        """
        ##### OLD
        for childWidget in self.ChildGroupWidgets:
            childWidget.destroy()
        
        self.ChildGroupWidgets = []
        
        for child in self.parentGroup.childGroups:
            newChildWidget = GroupWidget(self.RightScrollFrame.InnerFrame, child, LabelsObj=self.LabelsObj, maxItemHeight=900, maxItemWidth=900, itemPack="top")
            newChildWidget.pack(fill="y")
            newChildWidget.bind("<Button-1>", self.selectChildWidget)
            self.ChildGroupWidgets.append(newChildWidget)"""


    def selectChildWidget(self, event):
        if(self.SelectedChildWidget != None):                
            self.SelectedChildWidget.configure(bg="lightblue")
        self.SelectedChildWidget = event.widget
        self.SelectedChildWidget.configure(bg="yellow")
    
    def deleteChildWidget(self, event):
        if(self.SelectedChildWidget != None):
            print(len(self.SelectedChildWidget.Group.subjects))
            self.parentGroup.deleteChild(self.SelectedChildWidget.Group)
            self.updateLeft()
            self.updateRight()


    #allows user to "drop down" a tier in the tree and sort the selected child group
    def sortChildGroup(self, event):
        if(self.SelectedChildWidget != None):
            self.parentGroup = self.SelectedChildWidget.Group
            self.populateLeft()
            self.populateRight()

    def sortParentGroup(self, event):
        if(self.parentGroup.parent != None):
            #sets the current parent group to the parent of the current parent
            #essentially going "up" one level in the tree
            self.parentGroup = self.parentGroup.parent
            self.populateLeft()
            self.populateRight()

    #create new child button
    def CreateChildGroup(self, event):
        self.parentGroup.createChildGroup()
        self.populateRight()

    def commitGroups(self):
        print("committed!")
        LB.writeTreeBoot(rootGroup=self.RootGroup, databaseDirect=self.csvDirectory, oldFileDirect=self.oldDirectory, newFileDirect=self.newDirectory)
        self.populateLeft()
        self.populateRight()
        #self.parentGroup = None

    def setDirectory(self, directory, title):
        return filedialog.askdirectory(title=title)

    def setImageFolder(self):
        self.oldDirectory = filedialog.askdirectory(title="Select an Image or Video Folder")
        print(self.oldDirectory)
        #self.ParentGroupWidget.deleteItemWidgets()#if this isnt called there will still be old item widgets in the frame
        #Create new root group and populate it
        self.RootGroup = LB.Group()
        print(len(self.RootGroup.items))#when you create a new group it adds the new items to the old ones? CHECK FOR BUG NOW
        self.RootGroup.populateItems(LB.getAllFiles(directory=self.oldDirectory), self.oldDirectory + "/")
        self.parentGroup = self.RootGroup
        print(len(self.parentGroup.items))#when you create a new group it adds the new items to the old ones?
        self.populateLeft()
        self.populateRight()
    
    def setSaveFolder(self):
        self.newDirectory = filedialog.askdirectory(title="Select Save Location")

    def setDataBaseFolder(self):
        self.csvDirectory = filedialog.askdirectory(title="Select Database Folder")




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

        def labelKindSelected(event):
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
        #self.LabelKindComboBox.pack(side="top")
        
        self.LabelKindComboBox.bind("<<ComboboxSelected>>", labelKindSelected)

        self.LabelsComboBox = ttk.Combobox(self, values=self.Labels.subjectLabels)
        self.LabelsComboBox.set("Unknown")
        #self.LabelsComboBox.pack(side='top')

        #button
            ##add button
        #this handles both selecting a label and if a new label is typed in
        def labelSelected(event):
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
        #self.AddLabelButton.pack(side="top")
        self.AddLabelButton.bind("<Button-1>", labelSelected)

            ## remove button
        def removeLabel(event):
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
        #self.RemoveLabelButton.pack(side="top")
        self.RemoveLabelButton.bind("<Button-1>", removeLabel)

        #if this is the widget for the root group, do not display comboboxes/buttons
        if(self.Group.parent != None):
            """self.LabelKindComboBox.pack(side="top")
            self.LabelsComboBox.pack(side="top")
            self.AddLabelButton.pack(side="top")
            self.RemoveLabelButton.pack(side="top")"""

            self.LabelKindComboBox.grid(row=0, column=0)
            self.LabelsComboBox.grid(row=1, column=0)
            self.AddLabelButton.grid(row=2, column=0)
            self.RemoveLabelButton.grid(row=3, column=0)


        #label
        self.LabelsWidget = tk.Label(self, text='')
        self.setLabelText()
        #self.LabelsWidget.pack(side="top")
        self.LabelsWidget.grid(row=4, column=0)

        #import items
        self.setItemWidgets()

    #call backs for drag and drop features
    def dnd_accept(self, source, event):
        return self#this is recquired, typically is used to check if object being dropped is a valid one
        
    def dnd_enter(self, source, event):
        #self.configure(bg="lightgreen")#change later
        ""
        
    def dnd_leave(self, source, event):
        #self.configure(bg="lightblue")
        ""

    def dnd_motion(self, source, event):
        #print("being dragged")
        """"""

    def dnd_commit(self, source, event):
        self.Group.addItem(source.item)
        self.setItemWidgets()


    def deleteItemWidgets(self):
        #inefficient, need to rewrite later
        for itemWidget in self.ItemWidgetList:
            itemWidget.destroy()

        self.ItemWidgetList = []

    #CHANGE SYSTEM LATER IN ORDER TO CLEAN UP .configure jitteryness
    def setItemWidgets(self):
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
            #note: the +5 is so that the item widgets are not in the same row as the buttons/labels


    
    #creates/sets the str for the label widget
    def setLabelText(self):
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
            print("unable to find image " + item.fileName)

        self.WidgetLabel.bind("<ButtonPress-1>", self.onDragStart)
        self.bind("<ButtonPress-1>", self.onDragStart)




    #call backs for drag and drop features
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
        #print("being dragged")
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

    def getLabels(self):
        self.subjectLabels = self.LabelsCSV["subjects"].dropna().to_list()
        self.creatorLabels = self.LabelsCSV["creators"].dropna().to_list()
        self.tagLabels = self.LabelsCSV["tags"].dropna().to_list()
    
    #if a label is already in the list, move it to the top, otherwise it is added to the top
    def putLabelOnTop(self, LabelList, addlabel):
        if(addlabel in LabelList):
            LabelList.remove(addlabel)
        LabelList.append(addlabel)
    
    def putSubject(self, label):
        self.putLabelOnTop(LabelList=self.subjectLabels, addlabel=label)
    
    def putCreator(self, label):
        self.putLabelOnTop(LabelList=self.creatorLabels, addlabel=label)

    def putTag(self, label):
        self.putLabelOnTop(LabelList=self.tagLabels, addlabel=label)

    #add remove labels later


        


if __name__ == "__main__":
    main()