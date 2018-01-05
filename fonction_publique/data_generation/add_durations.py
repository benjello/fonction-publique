# -*- coding: utf-8 -*-
import logging
import os
import pandas as pd


from fonction_publique.base import grilles, output_directory_path
from fonction_publique.data_generation.utils import (
    add_change_grade_variable, get_career_transitions, get_grilles_including_bef_ATT, reshape_wide_to_long,
    )


log = logging.getLogger(__name__)


def add_rank_change_var(
        data = None,
        grilles = get_grilles_including_bef_ATT(grilles = grilles),
        first_year = 2004,
        start_year = None
        ):
    """Add indicator of grade change between 2003 and start_year
    """
    log.info('add indicator of grade change between 2003 and 2011')
    if data is None:
        data = pd.read_csv(
            os.path.join(output_directory_path, 'filter', 'data_ATT_{}_filtered.csv'.format(start_year)),
            index_col = 0,
            ).query('annee >= annee_min_to_consider')
        
    data = data.query('annee >= annee_min_to_consider')   
    data_change_grade = []  # Redefined at the end of the loop
    annees = list(reversed(range(first_year, (start_year+1) )))
    data_a_utiliser_pour_annee_precedente = None
    for annee in annees:
        log.info("processing year {}".format(annee))
        if annee == start_year:
            data_unique_transition = get_career_transitions(data, annee, unique = True)
            log.debug(data_unique_transition)
            data_with_change_grade_variable = add_change_grade_variable(
                data_unique_transition, annee, grilles = grilles
                ).reset_index().merge(
                    get_career_transitions(data, annee, unique = False)[['ident', 'annee', 'ib_bef', 'c_cir']],
                    on = ['annee', 'ib_bef', 'c_cir'],
                    how = 'right'
                    )
        else:
            data_unique_transition = get_career_transitions(
                data = data_a_utiliser_pour_annee_precedente,
                annee = annee,
                unique = True
                )
            data_with_change_grade_variable = add_change_grade_variable(
                data_unique_transition, annee, grilles = grilles
                ).reset_index().merge(
                    get_career_transitions(data_a_utiliser_pour_annee_precedente, annee, unique = False)[[
                        'ident', 'annee', 'ib_bef', 'c_cir'
                        ]],
                    on = ['annee', 'ib_bef', 'c_cir'],
                    how = 'right'
                    )
        data_change = data_with_change_grade_variable.query('change_grade == True')
        data_entre = data.query('(annee_min_to_consider == @annee) & (annee == @annee)')[['annee', 'ident']]
        data_entre['change_grade'] = [True] * len(data_entre)
        data_entre['ambiguite'] = [False] * len(data_entre)
        data_entre['nombre_de_grades_possibles'] = [1] * len(data_entre)
        data_change_grade.append(data_change.append(data_entre))

        log.debug('data_with_change_grade_variable: {}'.format(data_with_change_grade_variable.info(verbose = True)))

        if annee != first_year:
            data_a_utiliser_pour_annee_precedente = (data_with_change_grade_variable
                .query('change_grade == False')[['ident', 'c_cir_bef_predit']]
                .rename(columns = {'c_cir_bef_predit': 'c_cir'})
                .merge(
                    data[['ident', 'ib', 'annee']].query('annee == {} | annee == {}'.format(annee - 1, annee - 2)),
                    on = ['ident']
                    )
                )
            del data_with_change_grade_variable, data_change, data_entre
        else:
            data_with_var_grade_change = (pd.concat(data_change_grade)
                .drop_duplicates()
                .append(data_with_change_grade_variable.query('change_grade == False'))
                .drop_duplicates()
                )
            del data_with_var_grade_change['c_cir']
            data_with_var_grade_change['annee'] = data_with_var_grade_change['annee'] - 1
            data_with_var_grade_change = data_with_var_grade_change.rename(
                columns = {'c_cir_bef_predit': 'c_cir', 'ib_bef': 'ib'}
                )
            data_with_var_grade_change = data_with_var_grade_change.sort_values(['ident', 'date_effet_grille'])
            data_with_var_grade_change = data_with_var_grade_change.drop_duplicates(
                data_with_var_grade_change.columns.difference(
                    ['date_effet_grille', 'max_mois', 'min_mois', 'echelon']
                    ),
                keep = "last"
                )
            data_no_ambig = data_with_var_grade_change.query(
                '(ambiguite == False) & (change_grade == False)'
                ).reset_index()[[
                    'ident', 'annee'
                    ]].drop_duplicates()
            data_no_ambig['first_year_no_ambig'] = data_no_ambig.groupby('ident')['annee'].transform(min)
            data_no_ambig = data_no_ambig[['ident', 'first_year_no_ambig']].drop_duplicates()
            data_with_var_grade_change_ident_no_ambig = data_with_var_grade_change.query(
                'ident in @data_no_ambig.ident.unique()'
                ).merge(
                    data_no_ambig,
                    left_on = ['ident', 'annee'],
                    right_on = ['ident', 'first_year_no_ambig'],
                    how = 'inner',
                    )
            del data_with_var_grade_change_ident_no_ambig['first_year_no_ambig']
            results = data_with_var_grade_change.query(
                'ident not in @data_with_var_grade_change_ident_no_ambig.ident.unique()'
                ).append(data_with_var_grade_change_ident_no_ambig).append(
                    data.query('annee > 2010').copy()[[
                        u'ident', u'libemploi', u'annee', u'c_cir', u'statut', u'ib', u'etat',
                        u'echelon', u'min_mois', u'moy_mois',
                        u'max_mois', u'date_effet_grille'
                        ]]
                    )
            return results.merge(
                data[[
                    'ident', u'generation', u'sexe', u'an_aff', u'c_cir_start', u'annee_exit',
                    u'annee_min_to_consider'
                    ]], on = 'ident'
                ).drop_duplicates()


def add_censoring_var(data, first_year = 2003):
    data['right_censored'] = (data['annee_exit'] == 9999)
    data['left_censored'] = [False] * len(data)
    id_left_censored = data.query(
        '((annee == annee_min_to_consider) | (annee == @first_year)) & (change_grade == False)'
        ).ident.unique()
    data.loc[data['ident'].isin(id_left_censored), 'left_censored'] = True
    return data


def add_grade_bef_var(data):
    data_temp = data.copy()
    data_temp['grade_bef'] = None
    data_temp.loc[(data_temp['change_grade']  == True ), 'grade_bef'] = data_temp['c_cir']
    data_temp = data_temp[['ident', 'grade_bef']].dropna().drop_duplicates('ident', keep = 'first')
    data = data.merge(data_temp, on = 'ident', how = 'left')
    return data


def add_grade_next_var(data):  # FIXME
    data_temp = data.copy()
    data_temp['grade_next'] = None
    data_temp.loc[(data['annee'] == data['annee_exit']), 'grade_next'] = data_temp['c_cir']
    data_temp = data_temp[['ident', 'grade_next']].dropna()
    data = data.merge(data_temp, on = ['ident'], how = 'left')

    data['next_grade_situation'] = ['no_exit'] * len(data)
    data.loc[
        (data['grade_next'].isin(['TTH2', 'TTH3', 'TTH4'])) & (data['annee'] == data['annee_exit'] - 1),
        'next_grade_situation'
        ] = 'exit_next'
    data.loc[
        (data['next_grade_situation'] != 'exit_next') & (data['annee'] == data['annee_exit'] - 1),
        'next_grade_situation'
        ] = 'exit_oth'
    data.loc[data['annee'] >= data['annee_exit'], 'next_grade_situation'] = None
    return data


def add_year_of_entry_var(data):
    data['annee_entry'] = None
    data.loc[(data['change_grade'] == True) & (data['left_censored'] == False), 'annee_entry'] = data['annee'] + 1
    data['annee_entry_min'] = data.groupby('ident')['annee_entry'].transform(min)
    data['annee_entry_max'] = data.groupby('ident')['annee_entry'].transform(max)
    for col in ['annee_entry_min', 'annee_entry_max']:
        data[col] = data[col].fillna(-1).astype(int)
    del data['annee_entry']
    return data


def add_duration_var(data, start_year):
    data['duration_max_in_grade'] = None
    data['duration_min_in_grade'] = None
    data.loc[(data['annee_entry_min'] != -1) & (data['annee'] >= start_year), 'duration_max_in_grade'] = data[
        'annee'
        ] - data['annee_entry_min'] + 1
    data.loc[data['annee_entry_max'] != -1, 'duration_min_in_grade'] = data[
        'annee'
        ] - data['annee_entry_max'] + 1
    for col in ['duration_max_in_grade', 'duration_min_in_grade']:
        data[col] = data[col].fillna(-1).astype(int)
    return data


def add_entry_in_echelon_var(data, data_quarterly = None, reshape = False, start_year = None):
    """ /!\ : arbitrary use of 'annee_entry_max' """
    # FIXME deal with grille change
    if data_quarterly is None:
        data_quarterly = reshape_wide_to_long()
    if reshape is True and data_quarterly is not None:
        data_quarterly =  reshape_wide_to_long(data_quarterly)
    data_temp = data.query('annee <= @start_year')[['ident', 'annee_entry_min']].drop_duplicates().copy()
    data_quarterly = data_quarterly.merge(
        data_temp,
        on = 'ident',
        how = 'inner'
        )[['ident', 'annee', 'quarter', 'echelon', 'ib', 'annee_entry_min']].query(
            '(annee >= annee_entry_min) & (annee <= @start_year)').copy()

    dict_periods = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
    data_quarterly['period'] = pd.to_datetime(
        data_quarterly['annee'].map(str) + '-' + data_quarterly['quarter'].map(dict_periods).map(str)
        ).dt.strftime('%Y-%m-%d')
    echelon_2011 = data_quarterly.query('(annee == 2011) & (quarter == 4)').copy().filter(
        ['ident', 'ib', 'echelon'], axis = 1
        ).drop_duplicates().rename(columns = {"ib": "ib_start", "echelon": "echelon_start"})
    data_quarterly = data_quarterly.merge(echelon_2011, on = 'ident', how = 'left').query(
        'ib == ib_start'
        )
    data_quarterly = data_quarterly.query('ib == ib_start')[['ident', 'period']]
    data_quarterly['quarter_entry_echelon'] = data_quarterly.groupby('ident')['period'].transform(min)
    data_quarterly = data_quarterly[['ident', 'quarter_entry_echelon']].drop_duplicates()
    
    
    
    return data.merge(data_quarterly, on = 'ident', how = 'left')


def add_initial_anciennete_in_echelon(data, start_year = None):
    data['first_quarter_obs'] = pd.datetime(start_year, 12, 31)
    data['quarter_entry_echelon'] = pd.to_datetime(data['quarter_entry_echelon'])

    def diff_month(d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    data['anciennete_echelon'] = (
        diff_month(pd.DatetimeIndex(data['first_quarter_obs']), pd.DatetimeIndex(data['quarter_entry_echelon']))
        )
    del data['first_quarter_obs']
    return data


def main_duration(data = None, start_year = None):
    data1 = add_rank_change_var(data, start_year = start_year)
    data2 = add_censoring_var(data1)
    log.info('add left and right censoring indicator')
    data3 = add_grade_bef_var(data2)
    log.info('add previous grade')
    data4 = add_grade_next_var(data3)
    log.info('add next grade / next grade situation variables')
    data5 = add_year_of_entry_var(data4)
    log.info('add year of entry variables')
    data6 = add_duration_var(data5, start_year)
    log.info('add duration in grade variables')
    data7 = add_entry_in_echelon_var(data6,  data_quarterly = data, reshape = True, start_year = start_year)
    log.info('add quarter of entry in {} echelon variable'.format(start_year))
    data8 = add_initial_anciennete_in_echelon(data7, start_year = start_year)
    log.info('add initial anciennete in {} echelon'.format(start_year))
    return data8


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    main_duration(
        data = pd.read_csv(
            os.path.join(output_directory_path, 'filter', 'data_ATT_2011_filtered.csv'),
            index_col = 0,
            ).query('annee >= annee_min_to_consider'),
        start_year = 2011
        )
