"""This module is used to store the data of a frame using the graph data structure
this data structure is an undirectional weighted graph"""

from itertools import combinations
from frame_data_processing import frame
from frame_data_processing import molecule
from typing import Callable
import json

class Vertex:
    """This class represent the node that stores data of a molecule itself"""

    def __init__(self, node:molecule.molecule) -> None:
        """the node is a molecule, the molecule name will be used as the key to access the vertex
        adjacent is a dictionary that stores the keys of the adjacent molecule"""

        self.id = node.get_name()
        self.adjacent = {}
    
    def __str__(self):

        return f"molecule : {self.id} \n adjacents : {self.adjacent.keys()}"

    def add_neighbor(self, neighbor, weight = 0) -> None:
        """Weight is the coulomb matrix/ distance/ charge transfer coupling or transfer rate between the 2 vertex
        will decide later"""

        self.adjacent[neighbor] = weight # this weight might change later or will do calculation of weight first

    def get_connections(self):
        """getter method to get the neighbor keys"""

        return self.adjacent.keys()

    def get_id(self) -> str:
        """getter method to get the molecule's key"""

        return self.id

    def get_weight(self, neighbor:str) -> float:
        """getter method to get the weight connect to the selected neighbor
        currently doesn't handle key doesn't exist error"""

        return self.adjacent[neighbor]

class Graph:
    """The data structure of the undirectional weighted graph"""

    def __init__(self):

        self.vert_dict = {}
        self.num_vertex = 0
        
        #at the beginning there is no node and the vertex dictionary is empty

    def __iter__(self):
        """might not use method in this project"""

        return iter(self.vert_dict.values())

    def add_vertex(self, node:molecule.molecule):
        """method to add a new vertex to the graph"""

        self.num_vertex +=1
        
        new_vertex = Vertex(node)
        self.vert_dict[new_vertex.get_id()] = new_vertex

        return new_vertex #might not return this

    def get_vertex(self, key):
        """getter method to get the vertex base on the key"""
        
        if key in self.vert_dict:
            
            return self.vert_dict[key]

        else:

            return None

    def add_edge(self, frm:molecule.molecule, to:molecule.molecule, weight = 0):
        """method to add edge (connection) to two vertex"""

        if frm not in self.vert_dict:

            self.add_vertex(frm)

        if to not in self.vert_dict:

            self.add_vertex(to)

        self.vert_dict[frm].add_neighbor(self.vert_dict[to], weight)
        self.vert_dict[to].add_neighbor(self.vert_dict[frm], weight)

    def get_vertices(self):
        """getter method to get all the keys in the graph"""

        return self.vert_dict.keys()
