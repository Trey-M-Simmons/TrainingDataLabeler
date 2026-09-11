# TrainingDataLabeler
# Run
Language: Python 3.12.3
External Libraries: Pandas 2.1.4
Files: DataLabeler.py, LabelerBackend.py

To run, Pandas 2.1.4 (or newer) must be installed/in your environment. Once that is done DataLabeler.py and LabelerBackend.py must be in the same directory. 
Then simply run DataLabeler.py using python3 DataLabeler.py. 

# Use Case
Aside from running large scale hardware, finding good LABELED data can be one of the most expensive and difficult parts of making modern large 
scale models. This is especially true for models that must be trained on images (Such generative and object identification) as many times images 
still must be manually labeled. The point of this program is to demonstrate a method that will increase the productivity of those labeling bulk 
training data. 

# The Method
The user will sort by placing **items** into corresponding **groups**. These groups will be organized into a hierarchical category structure. Ex:
                        
                         Vehicle                                         Animal                                                                                          
                            |                                              |
                            |                                              |
                           / \                                            / \
                          /   \                                          /   \
                      Truck    Car                                    Cat    Horse
                      
The user would begin by putting all of the items in either the vehicle or animal group. The user will then be able to "step down" into either the vehicle
or animal group and then restart the cycle of organizing until nothing but "leaf" groups remain. 

# Terminology
**item**
-Some kind of data that needs labeling, typically an image. However, in later versions there will be video and gif support.

**tags**
-Tags are what describe and label the items. Note: Tags are stored in the groups while running the program but stored with the individual items in the database.
    This was done in order to reduce the number of tag look ups during model training. 

**group**
-A group is a collection of items that have some or all common tags, a final "leaf" groups tags should accurately describe all tags.

*Note: This terminology is partially hidden from the user as to make a more user friendly experience, However they are frequently referenced in the source code.

# Architecture
I personally used a Control Model View design for this program. The Model portion was implemented as a tree of groups. Each group contains a list of items, tags, 
as well as references to its children and its parent. The Control and View portions were made using Tkinter.  

