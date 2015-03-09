# -*- coding: utf-8 -*-
"""exposure.py

Functions needed to compute the exposure matrix (including concentration) and
the standard deviation for the null model
"""
from __future__ import division
import itertools

import marble as mb
from common import (regroup_per_class,
                   return_categories,
                   compute_totals)



__all__ = ["exposure"]




#
# Helper functions
#

## To compute the exposure
def pair_exposure(r, N_unit, N_tot, alpha, beta):
    E = (1/N_tot)*sum([N_unit[au]*r[au][alpha]*r[au][beta] for au in r])
    return E



## To compute the variance of the exposure
def unit_variance(N_tot, N_t, N_alpha, N_beta):
    "Compute the variance of E_{\alpha \beta}(t)" 
    var = (1/(N_alpha*N_beta)) * ((N_tot/N_t)-1)**2 \
            + (1/N_alpha) * ((N_tot/N_t)-1) \
            + (1/N_beta) * ((N_tot/N_t)-1)

    return var


def units_covariance(N_alpha, N_beta):
    "Compute the covariance of E_{\alpha \beta}(s) and E_{\alpha \beta}(t)"
    return (1-(1/N_alpha)) + (1-(1/N_beta)) -1 


def pair_variance(r, N_unit, N_class, N_tot, alpha, beta):
    var = (1/N_tot**2) * ( sum([(N_unit[au]**2)*unit_variance(N_tot, 
                                                              N_unit[au],
                                                              N_class[alpha], 
                                                              N_class[beta]) 
                                for au in r]) 
        + 2*sum([N_unit[au0]*N_unit[au1]*units_covariance(N_class[alpha],
                                                          N_class[beta])
                for au0, au1 in itertools.combination_with_replacement(r, 2)]) )
           
    return var 



#
# Callable functions
#
def exposure(distribution, classes=None):
    """ Compute the exposure between classes
    
    The exposure between two categories `\alpha` and `\beta` is defined as

    ..math::
        E_{\alpha \beta} = \frac{1}{N} \sum_{t=1}^{T} n(t) r_\alpha(t)
        r_\beta(t)

    where `r_\alpha(t)` is the representation of the class `\alpha` in the areal
    unit `t`, `n(t)` the total population of `t`, and `N` the total population
    in the considered system.

    The exposure of a class to itself `E_{\alpha \alpha}` measures the
    **isolation** of this class.

    The variance is computed on the null model which corresponds to the
    unsegregated configuration, that is when the spatial repartition of people
    of different income classes is no different from that that would be obtained
    if they scattered at random across the city.

    Parameters
    ----------

    distribution: nested dictionaries
        Number of people per class, per areal unit as given in the raw data
        (ungrouped). The dictionary must have the following formatting:
        > {areal_id: {class_id: number}}

    Returns
    -------

    exposure: nested dictionaries
        Matrix of exposures between categories.
        > {class_id0: {class_id1: (exposure_01, variance null model)}} 
    """
    # Regroup into classes if specified. Otherwise return categories indicated
    # in the data
    if classes:
        distribution = mb.regroup_per_class(distribution, classes)
    else:
       classes = mb.return_categories(distribution) 

    # Compute the total numbers per class and per individual
    N_unit, N_class, N_tot = mb.compute_totals(distribution) 

    # Compute representation for all areal unit
    representation = mb.representation(distribution, classes)

    # Compute the exposure matrix
    exposure = {alpha: {beta: (pair_exposure(representation, N_unit, N_tot, alpha, beta),
                               pair_variance(representation, N_class, N_unit, N_tot, alpha, beta)) }
                for alpha, beta in itertools.combination_with_replacement(classes,2)} 

    return exposure 
