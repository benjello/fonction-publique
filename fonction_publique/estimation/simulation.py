# -*- coding: utf-8 -*-


import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd
from pandas.api.types import is_any_int_dtype


from fonction_publique.base import (grilles, output_directory_path, simulation_directory_path)
from fonction_publique.career_simulation_vectorized import AgentFpt


log = logging.getLogger(__name__)


processed_grades = ['TTM1', 'TTM2', 'TTH1', 'TTH2', 'TTH3', 'TTH4']
processed_grades_by_code = {24: 'TTM1', 551: 'TTM2', 793: 'TTH1', 794: 'TTH2', 795: 'TTH3', 796: 'TTH4'}

# Règles possibles pour regle_echelon_by_grade_de_depart:
# - conservation_echelon: l'individu conserve son échelon en changeant de grade
# - conservation_ib: l'individu conserve son ib ou rejoint celui immédaitement supérieur en changeant de grade

regle_echelon_by_grade_de_depart = {
    'TTH1': {
        'TTH2': 'conservation_echelon',
        'others': 'conservation_ib',
        },
    'TTH2': {
        'TTH3': 'conservation_echelon',
        'others': 'conservation_ib',
        },
    'TTH3': {
        'TTH4': 'conservation_ib',
        'others': 'conservation_ib',
        },
    'TTH4': {
        'others': 'conservation_ib',
        },
    }

# Règles possibles pour regle_anciennete_dans_echelon_by_grade_de_depart:
# - conservation: l'individu conserve son anciennete dans l'échelon en changeant de grade
# - reinitialisation: l'individu voit son anciennete réinitilisée à son changement de grade

regle_anciennete_dans_echelon_by_grade_de_depart = {
    'TTH1': {
        'TTH2': 'conservation',
        'others': 'reinitialisation',
        },
    'TTH2': {
        'TTH3': 'conservation',
        'others': 'reinitialisation',
        },
    'TTH3': {
        'TTH4': 'conservation',
        'others': 'reinitialisation',
        },
    'TTH4': {
        'others': 'reinitialisation',
        },
    }


# FIXME: ugly
grilles = grilles.query("code_grade_NETNEH != 'TTM2' or echelon != -5")


def complete_echelon_speciaux(grilles_to_be_completed):
    grilles.query('(code_grade_NETNEH in @processed_grades) & (echelon ==-5)')
    new_echelon_speciaux_by_grade = {
        'TTH4': 8,
        'TTM2': 0
        }
    for grade, echelon in new_echelon_speciaux_by_grade.iteritems():
        grilles_to_be_completed.loc[
            (grilles_to_be_completed.code_grade_NETNEH == grade) &
            (grilles_to_be_completed.echelon == -5),
            'echelon'
            ] = echelon
    return grilles_to_be_completed


def get_data_counterfactual_echelon_trajectory(data = None):
    if data is None:
        data_counterfactual_echelon_trajectory = pd.read_csv(
            os.path.join(
                output_directory_path,
                'simulation_counterfactual_echelon',
                'results_annuels.csv'
                )
            )
        del data_counterfactual_echelon_trajectory['Unnamed: 0']
    return data_counterfactual_echelon_trajectory


def predict_next_period_grade_when_exit_oth(data):
    log.info('Predict next period grade when exit to other corps')
    data.loc[
        (data['next_situation'] == 'exit_oth') |
        (
            (data['grade'] == 'TTH4') &
            (data['next_situation'] == 'exit_next')
            ),
        'next_grade'
        ] = "TTM1"
    if sum(data['next_situation'] == 'exit_oth') > 0:  # FIXME: find a better organisation for three possible options
        data.loc[(data.grade  == 'TTH4') & (data.next_grade == 'TTM1') & (data.echelon > 5), 'next_grade'] = "TTM2"
        data.loc[(data.grade  == 'TTH3') & (data.next_grade == 'TTM1') & (data.echelon > 10), 'next_grade'] = "TTM2"
    data['next_annee'] = data['annee'] + 1
    data['next_anciennete_dans_echelon'] = 5
    return data


def predict_echelon_next_period_when_no_exit(data, grilles):
    log.debug('Predict echelon next period when no exit')
    log.debug("1. Number of idents = {} and number of lines is {}".format(
        len(data.ident.unique()), len(data.ident)))
    data_no_exit = data.query("next_situation == 'no_exit'").copy()
    log.debug("2. Number of idents = {} and number of lines is {}".format(
        len(data_no_exit.ident.unique()), len(data_no_exit.ident)))
    data_no_exit['period'] = pd.to_datetime(data_no_exit['annee'].astype(str) + "-12-31")
    predicted_year = data_no_exit['annee'].max() + 1
    log.info('Echelon prediction when no exit for year {}'.format(predicted_year))
    # FIXME the latter should be more provided by the model
    # Replace by the following
    data_no_exit['code_grade_NETNEH'] = data_no_exit['grade']
  #  data_no_exit.drop(['grade', 'next_annee', 'next_grade', 'next_anciennete_dans_echelon'], axis = 1, inplace = True)
    #    data_input = get_data(rebuild = False)[[
    #        'ident', 'period', 'grade', 'echelon'
    #        ]]
    #    data_input['period'] = pd.to_datetime(data_input['period'])
    #    data_input = data_input.query('echelon != 55555').copy()
    assert len(data_no_exit['annee'].unique()) == 1
    annee = data_no_exit['annee'].unique()[0]
    agents_grilles = (grilles
        .loc[grilles['code_grade_NETNEH'].isin(processed_grades)]
        .copy()
        )  # FIXME take out of the function
    agents_grilles['code_grade_NEG'] = agents_grilles['code_grade_NEG'].astype(int)
    log.debug("3. Number of idents = {} and number of lines is {}".format(
        len(data_no_exit.ident.unique()), len(data_no_exit.ident)))
    filtered_grilles = (agents_grilles
        .query('annee_effet_grille > @annee')[['code_grade_NETNEH', 'code_grade_NEG']]
        .drop_duplicates()
        )
    assert (filtered_grilles.code_grade_NETNEH.value_counts() == 1).all()
    data_no_exit = data_no_exit.merge(
        filtered_grilles,
        on = 'code_grade_NETNEH',
        how = 'left',
        )
    log.debug("4. Number of idents = {} and number of lines is {}".format(
        len(data_no_exit.ident.unique()), len(data_no_exit.ident)))
    data_no_exit['grade'] = data_no_exit['code_grade_NEG']
    del data_no_exit['code_grade_NEG']
    # agents_grilles = agents_grilles.loc[agents_grilles['code_grade_NEG'].isin([793, 794, 795, 796])].copy()
    # grilles['echelon'] = grilles['echelon'].replace(['ES'], -2).astype(int)
    log.debug("5. Number of idents = {} and number of lines is {}".format(
        len(data_no_exit.ident.unique()), len(data_no_exit.ident)))


    data_no_exit['anciennete_dans_echelon'] = data_no_exit['anciennete_dans_echelon'].astype(int)
    assert is_any_int_dtype(data_no_exit['anciennete_dans_echelon']), "anciennete_dans_echelon is not an int"
#    assert data_no_exit['anciennete_dans_echelon'].tolist() in range(1000)

    data_no_exit.loc[
        (data_no_exit['anciennete_dans_echelon'] < 2),
        'anciennete_dans_echelon'
        ] = 2  # FIXME very ugly to deal with anciennete_echelon edges !
            
            
    agents = AgentFpt(data_no_exit, end_date = pd.Timestamp(predicted_year + 1, 1, 1))  # < end_date
    agents.set_grille(agents_grilles)
    agents.compute_result()
    resultats = agents.result
    assert len(data_no_exit) == len(resultats.ident.unique())
    resultats["max_quarter"] = resultats.groupby(['ident'])['quarter'].transform(max)
    # FIXME ugly way to deal with missing last quarter for some individuals
    resultats_annuel = resultats.loc[
        resultats.quarter == resultats.max_quarter
        ].copy()
    assert len(data_no_exit) == len(resultats_annuel.ident.unique())
    assert resultats_annuel.groupby('ident')['quarter'].count().unique() == 1, resultats_annuel.groupby('ident')['quarter'].count().unique()

    resultats_annuel['next_annee'] = pd.to_datetime(resultats_annuel['quarter']).dt.year  # Au 31 décembre de l'année précédente
    assert (resultats_annuel['next_annee'] == predicted_year).all()
    resultats_annuel.rename(columns = {
        'echelon': 'next_echelon',
        'anciennete_dans_echelon_bis': 'next_anciennete_dans_echelon',
        },
        inplace = True,
        )

    data_no_exit = data_no_exit.merge(
        resultats_annuel[['ident', 'next_annee', 'next_echelon', 'next_anciennete_dans_echelon']],
        on = ['ident'],
        how = 'left',
        )
    
    del data_no_exit['period']
    del data_no_exit['code_grade_NETNEH']

    return data_no_exit


def predict_echelon_next_period_when_exit(data, grilles):
    """
    Prediction de l'échelon et de l'ancienneté dans l'échelon à la prochaine période pour les individus qui changent de grade. 
    """    
    log.debug('Predict echelon next period when exit')
    data_exit = data.query("next_situation != 'no_exit'").copy()
    
    # 1. Définition des règles à appliquer pour chaque grade d'arrivée et de départ. 
    grades_de_depart = data_exit.grade.unique()
    data_exit['regle_echelon'] = None
    data_exit['regle_anciennete_dans_echelon'] = None

    for grade in grades_de_depart:
        grades_d_arrivee = data_exit.query('grade == @grade')['next_grade'].unique()
        for next_grade in grades_d_arrivee:
            regle_echelon_by_grade_d_arrive = regle_echelon_by_grade_de_depart[grade]
            regle_echelon = (
                regle_echelon_by_grade_d_arrive[next_grade]
                if next_grade in regle_echelon_by_grade_d_arrive.keys()
                else regle_echelon_by_grade_d_arrive['others']
                )
            regle_anciennete_dans_echelon_by_grade_d_arrive = regle_anciennete_dans_echelon_by_grade_de_depart[grade]
            regle_anciennete_dans_echelon = (
                regle_anciennete_dans_echelon_by_grade_d_arrive[next_grade]
                if next_grade in regle_anciennete_dans_echelon_by_grade_d_arrive.keys()
                else regle_anciennete_dans_echelon_by_grade_d_arrive['others']
                )
            data_exit.loc[
                (data_exit.grade == grade) & (data_exit.next_grade == next_grade),
                ['regle_echelon', 'regle_anciennete_dans_echelon']
                ] = [regle_echelon, regle_anciennete_dans_echelon]
    
    # 2. Merge avec les grilles en effet pour trouver les ib et échelon correspondant
    
    grilles_in_effect = (grilles
        .query("date_effet_grille <= 2012")
        .groupby(['code_grade_NETNEH'])
        .agg({'date_effet_grille': np.max})
        .reset_index()
        )
    grilles = grilles.merge(
        grilles_in_effect,
        on = ['code_grade_NETNEH', 'date_effet_grille'],
        how = 'inner'
        )
    data_exit_merged = data_exit.merge(
        grilles[['code_grade_NETNEH', 'echelon', 'ib']],
        left_on = 'next_grade',
        right_on = 'code_grade_NETNEH',
        how = 'inner',
        suffixes = ('_data', '_grilles')
        )
    data_exit_merged.rename(columns = {
        'echelon_grilles': 'next_echelon',
        'echelon_data': 'echelon',
        },
        inplace = True,
        )


    # 3. Application des règles de détermination l'échelon
    data_exit_echelon_pour_echelon = data_exit_merged.query(
        "(regle_echelon == 'conservation_echelon') & (echelon == next_echelon)")
    
    
    data_exit_ib_pour_ib = data_exit_merged.query("(regle_echelon == 'conservation_ib')")  # FIXME To generalize
    data_exit_ib_pour_ib = (data_exit_ib_pour_ib
        .query('ib_grilles >= ib_data')
        .groupby(['ident']).agg({'ib_grilles': np.min})
        .reset_index()
        )
    data_exit_with_ib_pour_ib = data_exit.merge(data_exit_ib_pour_ib, on = 'ident', how= 'inner')
    assert (data_exit_with_ib_pour_ib.ib_grilles >= data_exit_with_ib_pour_ib.ib).all()

    data_exit_with_ib_pour_ib = data_exit_with_ib_pour_ib.merge(
        grilles[['code_grade_NETNEH', 'ib', 'echelon']].rename(columns = {'ib': 'next_ib', 'echelon': 'next_echelon'}),
        left_on = ['next_grade', 'ib_grilles'],
        right_on = ['code_grade_NETNEH', 'next_ib'],
        how = 'left',
        )

    del data_exit_with_ib_pour_ib['code_grade_NETNEH']
    del data_exit_with_ib_pour_ib['ib_grilles']

    data_exit_with_echelon_pour_echelon = data_exit_echelon_pour_echelon.query('echelon == next_echelon').copy().rename(
        columns = {"ib_data": "ib", "ib_grilles": "next_ib"})
    data_exit_with_echelon_pour_echelon_right_col = data_exit_with_echelon_pour_echelon[
        data_exit_with_ib_pour_ib.columns]

    data_exit = data_exit_with_echelon_pour_echelon_right_col.append(data_exit_with_ib_pour_ib)
    data_exit['next_annee'] = data_exit.annee + 1

    # 4. Application des règles d'anciennete dans l'échelon
    selection = (data_exit.regle_anciennete_dans_echelon == 'conservation')
    data_exit.loc[selection, 'next_anciennete_dans_echelon'] = data_exit.loc[selection, 'anciennete_dans_echelon'] +  12
    selection = (data_exit.regle_anciennete_dans_echelon == 'reinitialisation')
    data_exit.loc[selection, 'next_anciennete_dans_echelon'] = 6
    assert data_exit['anciennete_dans_echelon'].notnull().all(), 'Some anciennete_dans_echelon are NA'
    assert data_exit['next_anciennete_dans_echelon'].notnull().all(), 'Some next anciennete_dans_echelon are NA'
    
    del data_exit['regle_anciennete_dans_echelon']
    del data_exit['regle_echelon']
    del data_exit['next_ib'] # Ugly: recalculer dans get_ib pour tous => TODO: remonter get ib dans predict_no_exit
    
    return data_exit


def get_ib(data, grilles):
    annees = data.annee.unique()
    assert len(annees) == 1
    annee = annees[0]
    # grilles['echelon'] = grilles['echelon'].replace(['ES'], 55555).astype(int)  # FIXME or drop me
    grilles_grouped = (grilles
        .query('annee_effet_grille <= @annee')
        .groupby(['code_grade_NETNEH', 'echelon'])
        .agg({'date_effet_grille': np.max})
        .reset_index()
        )
    grilles_to_use = grilles_grouped.merge(
        grilles,
        on = ['code_grade_NETNEH', 'echelon', 'date_effet_grille'],
        how = 'inner'
        )
    grilles_to_use['code_grade_NETNEH'] = grilles_to_use['code_grade_NETNEH'].astype(str)
    assert not (grilles_to_use
        .query('code_grade_NETNEH in @processed_grades')
        .duplicated(subset = ['code_grade_NETNEH', 'echelon'])
        .any()
        ), \
        grilles_to_use.query('code_grade_NETNEH in @processed_grades').loc[grilles_to_use
            .query('code_grade_NETNEH in @processed_grades')
            .duplicated(subset = ['code_grade_NETNEH', 'echelon'], keep = False)
            ]

    data['grade'] = data['grade'].astype(str)
    assert not data.duplicated(subset = ['ident']).any()
    data_merged = data.merge(
        grilles_to_use[['code_grade_NETNEH', 'echelon', 'ib']],
        left_on = ['grade', 'echelon'],
        right_on = ['code_grade_NETNEH', 'echelon'],
        how = 'left',
        )[
            ['ident', 'annee', 'grade', 'echelon', 'ib', 'situation', 'anciennete_dans_echelon']
            ]

    assert data_merged.ib.notnull().all(), data_merged.loc[
        data_merged.ib.isnull(), ['grade', 'echelon']
        ].drop_duplicates()

    return data_merged


def predict_next_grade(data):
    # 1. Predict next period grade when no exit
    selection = (data['next_situation'] == 'no_exit')
    data.loc[selection, 'next_grade'] = data.loc[selection, 'grade'].copy()

    # 2. Predict next period grade when exit to next grade
    data.loc[(data['next_situation'] == 'exit_next'), 'next_grade'] = [
        'TTH' + str(int(s[-1:]) + 1) for s in data.query("next_situation == 'exit_next'")['grade']
        ]
    data['next_grade'] = data['next_grade'].replace(['TTH5'], 'TTM1')

    # 3. Predict next period grade when exit to other corps
    log.info('Predict next period grade when exit to other corps')
    data.loc[
        (data['next_situation'] == 'exit_oth') | (
            (data['grade'] == 'TTH4') &
            (data['next_situation'] == 'exit_next')
            ),
        'next_grade'
        ] = "TTM1"
    if sum(data['next_situation'] == 'exit_oth') > 0:  # FIXME: find a better organisation for three possible options
        data.loc[(data.grade  == 'TTH4') & (data.next_grade == 'TTM1') & (data.echelon > 5), 'next_grade'] = "TTM2"
        data.loc[(data.grade  == 'TTH3') & (data.next_grade == 'TTM1') & (data.echelon > 10), 'next_grade'] = "TTM2"
    # data['next_annee'] = data['annee'] + 1
    # data['next_anciennete_dans_echelon'] = 5
    assert data.next_grade.notnull().all(), "Column net_grade contains NaN"


def predict_next_period(data = None, grilles = None):
    """
    data is the resut of the first simulation du grade for the nex year
    Take data and compute the echelon and IB for next year
    """
    assert data is not None
    assert grilles is not None
    del data['Unnamed: 0']
    grilles = complete_echelon_speciaux(grilles.copy())
    data = data.query('echelon != 55555').copy()


    predict_next_grade(data)  # data is changed inplace

    data_with_next_echelon_when_no_exit = predict_echelon_next_period_when_no_exit(
        data, grilles)

    data_with_next_echelon_when_exit = predict_echelon_next_period_when_exit(
        data, grilles
        )
    assert  set(data_with_next_echelon_when_no_exit.columns) == set(data_with_next_echelon_when_exit.columns),  \
        "Les deux df n'ont pas les meme colonnes" 
    results = data_with_next_echelon_when_no_exit.append(data_with_next_echelon_when_exit)
    assert len(results.query(
        "(next_situation != 'no_exit') & (next_grade not in ['TTH4', 'TTM1', 'TTM2']) & (echelon != next_echelon)")
        ) == 0
    assert 'next_anciennete_dans_echelon' in results.columns
    results = results[['ident', 'next_annee', 'next_grade', 'next_echelon', 'next_situation', 'next_anciennete_dans_echelon']].copy()
    results['next_annee'] = results['next_annee'].astype(int)
    results['ident'] = results['ident'].astype(int)
    results['next_grade'] = results['next_grade'].astype(str)
    results = results.rename(columns = {col: col.replace('next_', '') for col in results.columns})
    assert len(list(set(results.ident.unique()) - set(data.ident.unique()))) == 0
    results = get_ib(results, grilles)
    results['grade'] = results['grade'].astype(str)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', default = '2011_data_simul_withR_MNL_1.csv', help = 'input file (csv)')
    parser.add_argument('-o', '--output-file', default = 'results_2011_m1.csv', help = 'output file (csv)')
    parser.add_argument('-v', '--verbose', action = 'store_true', default = True, help = "increase output verbosity")
    parser.add_argument('-d', '--debug', action = 'store_true', default = False, help = "increase output verbosity (debug mode)")


    args = parser.parse_args()
    if args.verbose:
        level = logging.INFO
    elif args.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(level = level, stream = sys.stdout)
    input_file_path = os.path.join(simulation_directory_path, 'results',
        args.input_file
        )
    log.info('Using unput data from {}'.format(input_file_path))
    data = pd.read_csv(input_file_path)
    input_idents = data.ident.unique().tolist()
    log.info("Number of unique idents in input file: {}".format(len(input_idents)))
    results = predict_next_period(data = data, grilles = grilles)
    directory_path = os.path.join(simulation_directory_path, 'results')

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    output_file_path = os.path.join(directory_path, args.output_file)
    if os.path.exists(output_file_path):
        log.info("Found existing output file {}. Removing.".format(output_file_path))
        os.remove(output_file_path)

    log.info("Saving results to {}".format(output_file_path))
    output_idents = results.ident.unique().tolist()
    missing_id = data.loc[data.ident.isin(set(input_idents) - set(output_idents))]
    missing_id.to_csv(os.path.join(directory_path, 'missing_id.csv'))

    missing_ib = results.loc[results.ib.isnull()]
    missing_ib.to_csv(os.path.join(directory_path, 'missing_ib.csv'))

    ids = results.ident
    clones = results[ids.isin(ids[ids.duplicated()])]

    log.info("Number of unique idents in output file: {}".format(len(output_idents)))
    log.info("Number of unique doubles in output file: {}".format(len(clones.ident.unique().tolist())))



    results  = results.drop_duplicates(subset = "ident")

    results.to_csv(output_file_path)


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    sys.exit(main())
    # logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    # for model in ['_m1']:  #, '_m2', '_m3']:
    #     data = pd.read_csv(os.path.join(
    #         output_directory_path,
    #         '..',
    #         'simulation',
    #         'data_simul_2011{}.csv'.format(model)
    #         ))
    #     predict_next_period(
    #         data = data,
    #         results_filename = 'results_2011{}.csv'.format(model),
    #         grilles = grilles,
    #         )
