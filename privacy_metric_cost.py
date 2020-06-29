import pathfinding_engine
import itertools
import numpy as np
from ahpy import *
from fractions import Fraction


class CostFinder:
    # take the sensitivites from each of the room, calculate overall sensitivity score
    # ordinal scale based on the number of resources (good, bad)
    # inheritance of class sensitiity unless subclass has a predefined sensitivity

    def __init__(self, criteria, options=list()):
        self.criteria = criteria
        self.options = options
        self.weights = None
        self.matrices = [np.ones((len(options), len(options)))] * len(criteria)
        self.crit_matrix = np.ones((len(criteria), len(criteria)))

    def setWeights(self):
        '''
        for opt in itertools.combinations(range(len(self.options)), 2):
            if opt[0] == opt[1]:
                pass
            for crit in range(len(self.criteria)):
                print("Compare {} to {} with the AHP fundamental scale:".format(self.options[opt[0]], self.options[opt[1]]))
                print("1 Equal importance, 3 Moderate Importance, 5 Strong importance, 7 Very Strong Importance, 9 Extreme Importance")
                comparison = input("How important is {} compared to {} in terms of {}? ".format(self.options[opt[0]], self.options[opt[1]],self.criteria[crit]))
                self.matrices[crit][opt[0]][opt[1]] = int(comparison)
                self.matrices[crit][opt[1]][opt[0]] = 1/int(comparison)
        comp_matrices = list()
         for i,crit in enumerate(self.criteria):
            comp_matrices.append(Compare(crit,self.matrices[i],self.options))
        '''
        for crit in itertools.combinations(range(len(self.criteria)), 2):
            if crit[0] == crit[1]:
                pass
            print(
                "1 Equal importance, 3 Moderate Importance, 5 Strong importance, 7 Very Strong Importance, 9 Extreme Importance")
            comparison = input(
                "How important is {} compared to {}? ".format(self.criteria[crit[0]], self.criteria[crit[1]]))
            self.crit_matrix[crit[0]][crit[1]] = Fraction(comparison)
            self.crit_matrix[crit[1]][crit[0]] = 1 / Fraction(comparison)

        self.weights = Compare('Criteria', self.crit_matrix, self.criteria).weights

        print(self.weights)