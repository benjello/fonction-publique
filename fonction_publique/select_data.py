# -*- coding: utf-8 -*-





# Filters: individuals at least one time in the corps
from __future__ import division

import logging
import inspect
import os
import sys
import pkg_resources
import pandas as pd
import numpy as np
from fonction_publique.base import raw_directory_path, get_careers, parser


libelles_emploi_directory = parser.get('correspondances',
                                       'libelles_emploi_directory')
save_path = 'M:/CNRACL/output'


def select_grilles(corps):
    path_grilles = os.path.join(
        pkg_resources.get_distribution('fonction_publique').location,
        'fonction_publique',
        'assets',
        'grilles_fonction_publique',
        )
    grilles = pd.read_hdf(os.path.join(path_grilles, "grilles_old.h5"))
    if corps == 'AT':
        libNEG_corps = ['ADJOINT TECHNIQUE DE 2EME CLASSE',
                        'ADJOINT TECHNIQUE DE 1ERE CLASSE',
                        'ADJOINT TECHNIQUE PRINCIPAL DE 2EME CLASSE',
                        'ADJOINT TECHNIQUE PRINCIPAL DE 1ERE CLASSE'
                        ]
    elif corps == 'AA':
        libNEG_corps = ['ADJOINT ADMINISTRATIF DE 2EME CLASSE',
                        'ADJOINT ADMINISTRATIF DE 1ERE CLASSE',
                        'ADJOINT ADMINISTRATIF PRINCIPAL DE 2EME CLASSE',
                        'ADJOINT ADMINISTRATIF PRINCIPAL DE 1ERE CLASSE'
                        ]
    elif corps == 'AS':
        libNEG_corps = ['AIDE SOIGNANT CL NORMALE (E04)',
                        'AIDE SOIGNANT CL SUPERIEURE (E05)',
                        'AIDE SOIGNANT CL EXCEPT (E06)'
                        ]
    else:
        print("NEG for the corps are not specified in the select_grilles function")
        stop
    subset_grilles = grilles[grilles.libelle_grade_NEG.isin(libNEG_corps)]
    return (subset_grilles)


def select_ident(dataset):
    variable = 'c_neg'
    c_neg = get_careers(variable = variable, data_path = dataset)
    subset_by_corps = {}
    for corps in ['AT', 'AA', 'AS']:
        grilles = select_grilles(corps = corps)
        list_code = list(set(grilles.code_grade_NEG.astype(str)))
        list_code = ['0' + s for s in list_code]
        subset_ident = list(set(c_neg.ident[c_neg.c_neg.isin(list_code)]))
        subset_by_corps[corps] = subset_ident
    return subset_by_corps

def cleaning_data(dataset, subset_by_corps, corps, first_year, list_permanent_variables, list_quaterly_variables, list_yearly_variables):
    # Filter
    subset_ident = subset_by_corps[corps]
    # Load data by type
    where = "ident in {}".format(subset_ident)
  #  permanent_variables = list_permanent_variables
    permanent_variables = ['generation', 'sexe', 'an_aff']
    generation =  get_careers(variable = permanent_variables[0], data_path = dataset, where = where)
    sexe =  get_careers(variable = permanent_variables[1], data_path = dataset, where = where)
    an_aff =  get_careers(variable = permanent_variables[2], data_path = dataset, where = where)

#    data_i = get_careers(variables = ["generation", "sexe", "an_aff"], data_path = dataset, where = where).sort_values(['ident'])
#    data_i['ident'] = data_i.index
    data_i = generation.merge(sexe, how = "left", on = ['ident']).merge(an_aff, how = "left", on = ['ident']).sort_values(['ident'])
    del an_aff, generation, sexe

    where = "(ident in {}) & (annee >= {})".format(subset_ident, first_year)
#    quaterly_variables = list_quaterly_variables
    quaterly_variables =  ['ib', 'echelon', 'etat']
    ib  =  get_careers(variable = quaterly_variables[0], data_path = dataset, where = where)
    ib  =  ib.pivot_table(index= ['ident', 'annee'], columns='trimestre', values='ib').reset_index()
    ib.columns = ['ident', 'annee', 'ib1', 'ib2', 'ib3', 'ib4']
    ech =  get_careers(variable = quaterly_variables[1], data_path = dataset, where = where)
    ech.echelon =  pd.to_numeric(ech.echelon, errors='coerce')
    ech  =  ech.pivot_table(index= ['ident', 'annee'], columns='trimestre', values='echelon').reset_index()
    ech.columns = ['ident', 'annee', 'echelon1', 'echelon2', 'echelon3', 'echelon4']
    etats  =  get_careers(variable = quaterly_variables[2], data_path = dataset, where = where)
    etats.etat = pd.to_numeric(etats.etat, errors='coerce')
    etats  =  etats.pivot_table(index= ['ident', 'annee'], columns='trimestre', values='etat').reset_index()
    etats.columns = ['ident', 'annee', 'etat1', 'etat2', 'etat3', 'etat4']


    where = "(ident in {}) & (annee >= {})".format(subset_ident, first_year)
#    yearly_variables = list_yearly_variables
    yearly_variables =  ['c_neg', 'libemploi', 'statut']
    c_neg =  get_careers(variable = yearly_variables[0], data_path = dataset, where = where)
    libemploi =  get_careers(variable = yearly_variables[1], data_path = dataset, where = where)
    statut =  get_careers(variable = yearly_variables[2], data_path = dataset, where = where)

    # Merge time varying variables
    data = (libemploi
                .merge(c_neg, how = "left", on = ['ident', 'annee'])
                .merge(statut, how = "left", on = ['ident', 'annee'])
                .merge(ib, how = "left", on = ['ident', 'annee'])
                .merge(ech, how = "left", on = ['ident', 'annee'])
                .merge(etats, how = "left", on = ['ident', 'annee'])
                .sort_values(['ident', 'annee'])
            )
    # Merge two data
    data = data.merge(data_i, how = "left", on = ['ident'])
    # Drop duplicates
    a = len(set(data.ident))
    data = data.drop_duplicates(subset = ['ident', 'annee'], keep = False)
    b = len(set(data.ident))
    diff = a - b
    print("{}: {} individus dupliqués et supprimés".format(dataset, diff))

    return data


def main(first_year = None,
         list_corps = None,
         datasets = None,
         list_permanent_variables = None,
         list_quaterly_variables = None,
         list_yearly_variables = None
         ):
    data_merge_corps = {}
    for dataset in datasets:
        print("Processing data {}".format(dataset))
        for corps in list_corps:
            print("Processing corps {}".format(corps))
            # List of ident of the corps
            subset_by_corps = select_ident(dataset)
            # Load and clean data by corps
            data_cleaned = cleaning_data(dataset,
                                         subset_by_corps,
                                         corps = corps,
                                         first_year = first_year,
                                         list_permanent_variables = list_permanent_variables,
                                         list_quaterly_variables = list_quaterly_variables,
                                         list_yearly_variables = list_yearly_variables
                                         )
            if dataset == datasets[0]:
                data_merge_corps["data_corps_{}".format(corps)] = data_cleaned
            else:
                data_merge = data_merge_corps["data_corps_{}".format(corps)].append(data_cleaned)
                data_merge_corps["data_corps_{}".format(corps)] = data_merge

    for corps in list_corps:
        path = os.path.join(save_path,
                        "corps{}_{}.csv".format(corps, first_year)
                        )
        data_merge_corps["data_corps_{}".format(corps)].to_csv(path)

        print("Saving data corps{}_{}.csv".format(corps, first_year))

    return


if __name__ == '__main__':
#    logging.basicconfig(level = logging.info, stream = sys.stdout)
    main(first_year = 2011, list_corps =  ['AT'],#, 'AS'],
                  datasets = ['1980_1999_carrieres.h5',
                               '1976_1979_carrieres.h5',
                               '1970_1975_carrieres.h5',
                               '1960_1965_carrieres.h5',
                               '1966_1969_carrieres.h5'])
