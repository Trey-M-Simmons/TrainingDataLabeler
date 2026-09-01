# TrainingDataLabeler
# Run
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
The user would begin by putting all of the items in either vehicle or animal group. The user will then be able to "step down" into either the vehicle
or animal group and then restart the cycle of organizing until nothing but "leaf" groups remain. 

# Terminology


# Architecture

