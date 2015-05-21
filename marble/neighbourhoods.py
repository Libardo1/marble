# -*- coding: utf-8 -*-
"""neighbourhoods.py

Scripts to extract the areal units where the different classes are
over-represented, and cluster the areal units that have common boundaries.
"""
from __future__ import division
import math
import shapely
import networkx as nx

import marble as mb
from common import (regroup_per_class,
                   return_categories,
                   compute_totals)



__author__ = """\t""".join(["Rémi Louf <remi.louf@sciti.es>"])

__all__ = ["overrepresented_units",
           "neighbourhoods",
           "clustering"]



#
# Helper functions
#
def _adjacency(areal_units):
    """ Compute the adjacency matrix of areal units

    Two areal units are said adjacent if their repective boundaries touch one
    another (see shapely's `touch` function for more information).

    Parameter
    ---------

    areal_units: dictionary
        Dictionnary of areal unit ids with shapely polygon object representing
        the unit's geometry as values.

    Returns
    -------

    adjacency: dictionary
    """

    ## Compute adjacency list
    adjacency = {a:[] for a in areal_units}
    for a0,a1 in itertools.permutations(areal_units, 2):
        if blocks[a1].touches(areal_units[a0]):
            adjacency[a0].append(a1)

    return adjacency


def _single_clustering(Nu, Nc):
    """Compute clustering index
    
    Parameters
    ----------
    Nu: int
        Number of units
    Nc: int
        Number of clusters
        
    Returns
    -------
    clust: float
        0 if units are not clustered (checkerboard)
        1 if units form a single cluster
    """
    clust = 1 - ( ((Nc/Nu) - (1/Nu)) /
                  (1 - (1/Nu)) ) 

    return clust




#
# Callable functions
#
def overrepresented_units(distribution, classes=None):
    """ Find the areal units in which each class is over-represented
   
    We say that a class `\alpha` is overrepresented in that tract `t` if the
    representation `r_\alpha(t)` is such that

    .. math::
        r_\alpha(t) > 1 + 2.57 \sigma_\alpha(t)

    Parameters
    ----------

    distribution: nested dictionaries
        Number of people per class, per areal unit as given in the raw data
        (ungrouped). The dictionary must have the following formatting:
        > {areal_id: {class_id: number}}

    classes: dictionary of lists
        When the original categories need to be aggregated into different
        classes. 
        > {class: [categories belonging to this class]}
        This can be arbitrarily imposed, or computed with uncover_classes
        function of this package.

    Returns
    -------

    units: dictionary of lists
        Dictionnary of classes, with the list of areal units where this class is
        overrepresented with 99% confidence.
        > {class:[list of areal units]}
    """
    # Regroup into classes if specified. Otherwise return categories indicated
    # in the data
    if not classes:
       classes = return_categories(distribution) 


    ## Compute the representation of the different classes in all areal units
    rep = mb.representation(distribution, classes)

    ## Find the tracts where classes are overrepresented
    areal_units = {cl:[au for au in rep
                          if rep[au][cl][0] > 1 + 2.57*math.sqrt(rep[au][cl][1])] 
                    for cl in classes}

    return areal_units



def neighbourhoods(distribution, areal_units, classes=None):
    """ Return the neighbourhoods where different classes gather

    Parameter
    ---------

    distribution: nested dictionaries
        Number of people per class, per areal unit as given in the raw data
        (ungrouped). The dictionary must have the following formatting:
        > {areal_id: {class_id: number}}

    areal_units: dictionnary
        Dictionnary of areal unit ids with shapely polygon object representing
        the unit's geometry as values.

    classes: dictionary of lists
        When the original categories need to be aggregated into different
        classes. 
        > {class: [categories belonging to this class]}
        This can be arbitrarily imposed, or computed with uncover_classes
        function of this package.

    Returns
    -------

    neighbourhoods: dictionary
        Dictionary of classes names with list of neighbourhoods (that are
        each represented by a list of areal unit)
        > {'class': [ [areal units in cluster i], ...]}
    """

    # Regroup into classes if specified. Otherwise return categories indicated
    # in the data
    if not classes:
       classes = return_categories(distribution) 

    ## Find the areal units where classes are overrepresented
    or_units = overrepresented_units(distribution, classes)
    
    ## Compute the adjacency list
    adjacency = _adjacency(areal_units)

    ## Extract neighbourhooods as connected components
    G = nx.from_dict_of_lists(adjacency) # Graph from adjacency
    neighbourhoods = {cl: [list(subgraph) for subgraph in
                            nx.connected_component_subgraphs(G.subgraph(or_units[cl]))]
                        for cl in classes}

    return neighbourhoods



def clustering(distribution, areal_units, classes=None):
    """ Return the clustering coefficient for the different classes
    
    [Add the definition of clustering here]

    Parameter
    ---------

    distribution: nested dictionaries
        Number of people per class, per areal unit as given in the raw data
        (ungrouped). The dictionary must have the following formatting:
        > {areal_id: {class_id: number}}

    areal_units: dictionnary
        Dictionnary of areal unit ids with shapely polygon object representing
        the unit's geometry as values.

    classes: dictionary of lists
        When the original categories need to be aggregated into different
        classes. 
        > {class: [categories belonging to this class]}
        This can be arbitrarily imposed, or computed with uncover_classes
        function of this package.

    Returns
    -------

    clustering: dictionary
        Dictionary of classes names with clustering values.
    """
    
    ## Get the number of neighbourhoods
    neigh = neighbourhoods(distribution, areal_units, classes)
    num_neigh = {cl: len(neighbourhoods[cl]) for cl in classes}
    num_units = {cl: len([a for neigh in neighbourhoods[cl] for a in neigh])
                    for cl in classes}

    ## Compute clustering values
    clustering = {}
    for cl in classes:
        if len(num_units[cl]) == 0:
            clustering[cl] = float('nan')
        elif len(num_units[cl]) == 1:
            clustering[cl] = 1
        else:
            clustering[cl] = _single_clustering(num_units[cl],
                                                num_neigh[cl])

            clust = num_neighbourhoods[cl] / len(over_bg[cl])
            clustering[cl] = 1 - ((clust-(1/len(over_bg[cl]))) / 
                                    (1-(1/len(over_bg[cl]))))

    return clustering
