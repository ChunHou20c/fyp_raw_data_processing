"""This module is used to store the data of a frame using the graph data structure
this data structure is an undirectional weighted graph"""

from typing import Optional
from frame_data_processing import molecule
from frame_data_processing import translation_tracker

class relation:
    """this class object track down the relation between the two vertex
    1) distance
    2) coulomb matrix/ transfer rate
    3) translation**  """

    def __init__(self, distance:float = 0, translation:translation_tracker.translation = translation_tracker.translation()) -> None:
        """translation is basically x y z coordinate with additional method to produce conjugate translation object"""

        self.distance = distance
        self.translation = translation

def relation_conjugate(rel:relation)-> relation:
    """this method return the conjugate of the relation"""

    return relation(rel.distance, translation_tracker.conjugate(rel.translation))
        
class Vertex:
    """This class represent the node that stores data of a molecule itself"""
    
    hint = 'vertex'

    def __init__(self, node:molecule.molecule) -> None:
        """the node is a molecule, the molecule name will be used as the key to access the vertex
        adjacent is a dictionary that stores the keys of the adjacent molecule"""

        self.id = node.get_name()
        self.adjacent = {}
        self.molecule = node
    
    def __str__(self):

        return f"molecule : {self.id} adjacents : {self.adjacent}"

    def add_neighbor(self, neighbor:str, relation:relation = relation()) -> None:
        """Weight is the coulomb matrix/ distance/ charge transfer coupling or transfer rate between the 2 vertex
        will decide later"""

        self.adjacent[neighbor] = relation # this weight might change later or will do calculation of weight first

    def get_connections(self):
        """getter method to get the neighbor keys"""

        return self.adjacent.keys()

    def get_id(self) -> str:
        """getter method to get the molecule's key"""

        return self.id

    def get_relation(self, neighbor:str) -> float:
        """getter method to get the weight connect to the selected neighbor
        currently doesn't handle key doesn't exist error"""

        return self.adjacent[neighbor]

#class border(Vertex):
#    """Same as vertex but with hint border and separated dictionary for neighbors from different side
#        this class will not check whether the molecule is actually at border, so check have to be done before constructing"""
#    
#    hint = 'border'
#
#    def __init__(self, node: molecule.molecule, flags:tuple[bool, bool, bool]) -> None:
#        """flag is the x y z cut by border flag, will check for neighbor base on the flag"""
#        super().__init__(node)
#
#        pass
#
#

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

    def get_vertex(self, key)-> Optional[Vertex]:
        """getter method to get the vertex base on the key"""
        
        if key in self.vert_dict:
            
            return self.vert_dict[key]

        else:

            return None

    def add_edge(self, frm:molecule.molecule, to:molecule.molecule, relation:relation = relation()):
        """method to add edge (connection) to two vertex"""

        if frm.get_name() not in self.vert_dict.keys():
            self.add_vertex(frm)

        if to.get_name() not in self.vert_dict.keys():
            self.add_vertex(to)

        self.vert_dict[frm.get_name()].add_neighbor(self.vert_dict[to.get_name()].get_id(), relation)
        self.vert_dict[to.get_name()].add_neighbor(self.vert_dict[frm.get_name()].get_id(), relation_conjugate(relation))

    def get_vertices(self):
        """getter method to get all the keys in the graph"""

        return self.vert_dict.keys()
