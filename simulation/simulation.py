"""
This module is the simulation of electron transfer
this simulation object take a gro file and a config file as input
The config file should contain the parameters that will be used in the simulation,
including the stopping condition, model to use and cut off distance for molecular pair
"""
from math import log
import pickle
import os
from typing import Callable
from electron_coupling import marcus_equation

import tensorflow as tf

from simulation import constructors, algorithm
from simulation import DBT1
from simulation.molecule_graph import Molecule_graph as Graph
from simulation.molecule_graph import Molecule_vertex
from itertools import combinations

import random
import numpy as np
from simulation.molecule_relation import Relation

class Simulation:
    """This class define how the simulation should be run from a single frame"""

    prediction_model = tf.keras.models.load_model('model/ANN1', compile=False)
    
    def __init__(self, gro_file:str) -> None:
        """gro_file - the file path of the gromac file"""
        
        self.__file__ = gro_file
        self.graph, self.box_width, self.timestamp = extract_metadata(gro_file)
        self.total_jump = 10000
        self.initial_box = np.array([0,0,0])
        self.current_box = np.array([0,0,0])
        self.time = 0
        
        self.electron_coupling_list, self.electron_coupling_key = make_cache_prediction(self.graph, self.prediction_model)
        print(self.box_width)

    def predicted_electron_coupling(self, key1, key2):

        index = self.electron_coupling_key[(key1, key2)]
        return self.electron_coupling_list[index]

    def single_jump(self, key):
        """
        this method do a single jump from a selected key
        """

        current_key = key
        new_key, jumping_time = jump(self.graph, current_key, self.predicted_electron_coupling)
        translation = self.graph.get_vertex(current_key).get_weight(new_key).translation

        initial_molecule = self.graph.get_vertex(current_key).molecule
        final_molecule = self.graph.get_vertex(new_key).molecule

        x0, y0, z0 = initial_molecule.center_coordinate(self.box_width, (0, 0, 0))
        x1, y1, z1 = final_molecule.center_coordinate(self.box_width, translation)
        
        Vector = (x1-x0, y1-y0, z1-z0)
        
        print(f'{new_key=}, {jumping_time=}, {Vector=}')

        return new_key, jumping_time, Vector
    
    def run(self):
        """this method run the simulation for electron jumps in the periodic space"""
        
        #start by choosing a random molecule - vertex

        initial_key = random.choice([ i for i in self.graph.get_vertices()])
        
        print('simulation starting from molecule {}'.format(self.graph.get_vertex(initial_key).id))

        current_key = initial_key

        for _ in range(self.total_jump):
                
            new_key, jumping_time = jump(self.graph, current_key, self.predicted_electron_coupling)
            
            self.time += jumping_time

            translation = self.graph.get_vertex(current_key).get_weight(new_key).translation

            self.current_box += translation

            current_key = new_key

        print(f'final box = {self.current_box}')
        
        initial_molecule = self.graph.get_vertex(initial_key).molecule
        final_molecule = self.graph.get_vertex(current_key).molecule

        Coord1 = initial_molecule.N_S1_S2_coordinates(self.box_width, tuple(self.initial_box))
        Coord2 = final_molecule.N_S1_S2_coordinates(self.box_width, tuple(self.current_box))

        distance = DBT1.DBT1_distance(*Coord1, *Coord2)

        print(f'distance travelled = {distance}')
        print(f'time taken = {self.time}')

def make_cache_prediction(graph:Graph, prediction_model):
    """This function make the cache for the model prediction"""
    
    list_of_coulomb_matrix = []
    keys = {}
    index = 0 #index use to access the predicted value
    for vertex in graph.vert_dict.values():
        
        for key, relation in vertex.adjacent.items():
            
            if (vertex.id, key) not in keys.keys():
                list_of_coulomb_matrix.append(relation.coulomb_matrix)
                keys[(vertex.id, key)] = index
                keys[(key, vertex.id)] = index
                index += 1

    array_of_coulomb_matrix = np.array(list_of_coulomb_matrix)
    predictions = prediction_model.predict(array_of_coulomb_matrix)
    
    return predictions.flatten(), keys

def jump(graph:Graph, key, func:Callable):
    """This function perform a jump and return the next vertex"""

    #find all possible neighbour
    _vertex = graph.get_vertex(key)
    neigbours = _vertex.get_connections()
    print(neigbours)
    #calculate total rate
    rates = []
    options = []
    for neighbour_key in neigbours:
        
        electron_coupling = func(_vertex.id, neighbour_key)
        reorganization_energy = 0.180
        temperature = 300
        Eij = 0
        
        options.append(neighbour_key)
        rates.append(marcus_equation.transfer_rate(electron_coupling, reorganization_energy, temperature, Eij))

    new_key, jumping_rate = random_weight_selector(options, rates)
    
    print('{:e}'.format(jumping_rate))
    random_number = -log(random.uniform(1,0))

    #print(f'{random_number=}')
    jumping_time = random_number/jumping_rate
    #this part is reserved for the calculation of the jumping time

    #for now we only care about the box tracking
    print(new_key)

    return new_key, jumping_time

def random_weight_selector(keys:list[str], _weights:list[float]):
    """A wrapper to random choice of new key"""

    list_of_tuple = [i for i in zip(keys, _weights)]
    choice = random.choices(list_of_tuple, weights=tuple(_weights), k = 1)
    return choice[0]

def extract_metadata(file_path:str)->tuple[Graph,float, float]:
    """This method build the graph for the simulation, (for internal use only, not to be called in runtime)"""
    
    file_name = file_path.split('/')[-1]
    cache_path = f'./cache/{file_name}'
    if os.path.isfile(cache_path):

        with open(cache_path, 'rb') as f:

            graph, boundary_data, timestamp = pickle.load(f)
    else:
        graph = Graph()
        file_data = constructors._Gro_file_parser(file_path, graph.molecule_length)
        molecules = file_data['list_of_molecules']
        boundary_data = file_data['boundary']
        timestamp = file_data['timestamp']

        for index,molecule in enumerate(molecules):
            molecules[index] = algorithm.complete_molecule(molecule, boundary_data)

        for m1, m2 in combinations(molecules, 2):

            relation = algorithm.molecular_pair_relation(m1, m2, 1.2, boundary_data)
            if (relation is not None):

                graph.add_edge(m1,m2,relation)
        
        with open(cache_path, 'wb') as f:
            
            object_to_save = (graph, boundary_data, timestamp)
            pickle.dump(object_to_save, f)

    return graph, boundary_data, timestamp
