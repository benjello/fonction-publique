# -*- coding:utf-8 -*-


from __future__ import division

import logging
import os

import pandas as pd

from fonction_publique.base import (DEBUG_CLEAN_CARRIERES, clean_directory_path, debug_chunk_size,
    get_careers_hdf_path, get_output_hdf_path, get_tmp_hdf_path, grilles_matching_hdf_path, grilles_txt_path)
from fonction_publique.career_simulation_vectorized import _set_dates_effet
from fonction_publique.scripts.clean_grilles import build_clean_grille_for_matching

log = logging.getLogger(__name__)


def get_grilles(force_rebuild = False, date = None, date_effet_max = None, date_effet_min = None,
        subset = None, use_date_effet_index = False):
    build_clean_grille_for_matching(force_rebuild = force_rebuild)
    log.info('Reading grilles for matching from {}'.format(grilles_matching_hdf_path))
    grilles = pd.read_hdf(grilles_matching_hdf_path)
    grilles = grilles.loc[grilles.libelle_FP.isin(['FONCTION PUBLIQUE HOSPITALIERE', 'FONCTION PUBLIQUE TERRITORIALE'])]
    assert set(grilles.libelle_FP.unique()) == set(['FONCTION PUBLIQUE HOSPITALIERE', 'FONCTION PUBLIQUE TERRITORIALE'])
    if subset is not None:
        if 'date_effet_grille' not in subset:
            subset.append('date_effet_grille')
        grilles = grilles[subset].drop_duplicates()

    if date is not None:
        grilles = (
            grilles
            .set_index('date_effet_grille')
            .asof(date)
            )
    else:
        grilles = (
            grilles
            .set_index('date_effet_grille')
            .loc[date_effet_min:date_effet_max]
            )
    if use_date_effet_index:
        return grilles
    else:
        return grilles.reset_index()


def get_libelles(code_grade_neg = None, code_grade_netneh = None, force_rebuild = False):
    # assert (code_grade_neg is not None) or (code_grade_netneh is not None)
    assert code_grade_netneh is not None
    grilles = get_grilles(force_rebuild = False)
    if code_grade_netneh is not None:
        return grilles.loc[
            grilles.code_grade.str.contains(code_grade_netneh),
            ['code_grade', 'libelle_FP', 'libelle_grade_NEG']
            ].drop_duplicates()
    # elif code_grade_neg is not None:
    #     return grilles[grilles.code_grade_neg.contains(code_grade_neg))


def get_careers_for_which_we_have_law(start_year = 2009, file_path = None, debug = DEBUG_CLEAN_CARRIERES):
    """Get carrer data (id, annee, grade, ib) of ids which:
      - grade is present in legislation data at least for one year (freq of grade)
      - year > 2009
      - ib < 2016, != -1, != 0, != NaN
     Save to HDFStore
     Returns stored DataFrame
     """
    law = pd.read_hdf(grilles_matching_hdf_path, 'grilles')
    careers_hdf_path = get_careers_hdf_path(clean_directory_path = clean_directory_path,
        file_path = file_path, debug = debug)
    careers_hdf = pd.HDFStore(careers_hdf_path)
    # Keeping only valid grades
    grades_in_law = law.code_grade.unique()  # analysis:ignore
    if debug:
        valid_grades = careers_hdf.select(
            'c_netneh',
            where = 'c_netneh in grades_in_law',
            stop = debug_chunk_size,
            )
    else:
        valid_grades = careers_hdf.select(
            'c_netneh',
            where = 'c_netneh in grades_in_law',
            )
    valid_idents = valid_grades.ident.unique()  # analysis:ignore
    condition = "annee > {} & ident in valid_idents & ib < 1016".format(start_year)
    valid_ib = careers_hdf.select('ib', where = condition, auto_close = True)
    careers = valid_ib.merge(valid_grades, on = ['ident', 'annee'], how = 'outer')
    careers = careers[~careers['ib'].isin([-1, 0])]
    careers = careers[careers['ib'].notnull()]
    careers['ib'] = careers['ib'].astype('int')
    careers = careers[careers['c_netneh'].notnull()]
    careers['annee'] = careers['annee'].astype('str').map(lambda x: str(x)[:4])
    careers['annee'] = pd.to_datetime(careers['annee'])
    assert not careers.empty, 'careers is an empty DataFrame'
    tmp_hdf_path = get_tmp_hdf_path(file_path, debug = debug)
    assert os.path.exists(os.path.dirname(tmp_hdf_path)), 'Invalid path {}'.format(os.path.dirname(tmp_hdf_path))
    careers.to_hdf(
        tmp_hdf_path,
        'tmp_1',
        format = 'table',
        data_columns = True,
        )


def get_unique_career_states(file_path = None, debug = DEBUG_CLEAN_CARRIERES):
    """ identifier les etats de carrieres uniques, cad les triplets uniques codes grades NETNEH, annee, ib"""
    tmp_hdf_path = get_tmp_hdf_path(file_path, debug = debug)
    tmp_hdf = pd.HDFStore(tmp_hdf_path)
    careers = tmp_hdf.select('tmp_1')
    careers = careers[['annee', 'trimestre', 'c_netneh']]
    unique_career_states = careers.groupby(['annee', 'trimestre', 'c_netneh']).size().reset_index()[[
        'annee',
        'trimestre',
        'c_netneh',
        ]]
    unique_career_states['annee'] = [str(annee)[:4] for annee in unique_career_states['annee']]
    unique_career_states.to_hdf(tmp_hdf_path, 'tmp_2', format = 'table', data_columns = True)


def append_date_effet_to_unique_career_states(file_path = None, debug = DEBUG_CLEAN_CARRIERES):
    tmp_hdf_path = get_tmp_hdf_path(file_path, debug = debug)
    tmp_hdf = pd.HDFStore(tmp_hdf_path)
    law = pd.HDFStore(grilles_hdf_path)
    with tmp_hdf as store:
        unique_career_states = store.select('tmp_2').copy()
        dataframe = unique_career_states[['c_netneh', 'annee', 'trimestre']].copy()

        assert not dataframe.duplicated().any(), 'There are duplicated row in dataframe'
        dataframe['year'] = dataframe.annee
        dataframe['month'] = (dataframe.trimestre - 1) * 3 + 1
        dataframe['day'] = 1
        dataframe['observation_date'] = pd.to_datetime(dataframe[['year', 'month', 'day']])
        assert not dataframe.duplicated().any(), 'There are duplicated row in dataframe'
        dataframe.rename(
            columns = dict(observation_date = 'period', c_netneh = 'grade'),
            inplace = True,
            )
        dataframe = dataframe[['grade', 'annee', 'trimestre', 'period']].copy()
        assert not dataframe.duplicated().any(), 'There are duplicated row in dataframe'
        careers = store.select('tmp_1')
        assert not careers.duplicated().any(), 'There are duplicated row in careers'
        grilles = law.select('grilles')
        grilles = grilles.rename(columns = dict(code_grade_NETNEH = 'grade'))
        _set_dates_effet(
            dataframe,
            date_observation = 'period',
            start_variable_name = 'date_effet_grille',
            next_variable_name = None,
            grille = grilles,
            )
        assert not dataframe.duplicated().any(), 'There are duplicated row in unique_career_states (tmp_3)'
        dataframe.to_hdf(tmp_hdf_path,
            'tmp_3',
            format = 'table',
            data_columns = True)


def merge_date_effet_grille_with_careers(file_path = None, debug = DEBUG_CLEAN_CARRIERES):
    """ ajouter les dates d'effets de grilles aux carrieres """
    tmp_hdf_path = get_tmp_hdf_path(file_path, debug = debug)
    tmp_hdf = pd.HDFStore(tmp_hdf_path)
    unique_career_states = tmp_hdf.select('tmp_3')

    assert not unique_career_states.duplicated().any(), 'There are duplicated row in unique_career_states'
    careers = tmp_hdf.select('tmp_1')

    careers['annee'] = [str(annee)[:4] for annee in careers['annee']]
    careers['year'] = careers.annee.astype('int')
    careers['month'] = (careers.trimestre - 1) * 3 + 1
    careers['day'] = 1
    careers['period'] = pd.to_datetime(careers[['year', 'month', 'day']])
    careers = careers[['ident', 'ib', 'trimestre', 'c_netneh', 'period']].copy()
    careers.rename(columns = dict(c_netneh = 'grade'), inplace = True)
    assert not careers.duplicated().any(), 'There are duplicated row in careers'
    assert not unique_career_states.duplicated().any(), 'There are duplicated row in unique_career_states'
    careers = unique_career_states.merge(
        careers,
        on = ['period', 'grade', 'trimestre'],
        how = 'outer'
        )
    assert not careers.duplicated().any(), 'There are duplicated row in careers'
    careers.to_hdf(
        tmp_hdf_path,
        'tmp_4',
        format = 'table',
        data_columns = True,
        )


def merge_careers_with_legislation(file_path = None, debug = DEBUG_CLEAN_CARRIERES):
    """ ajouter les echelons aux carrieres """
    tmp_hdf_path = get_tmp_hdf_path(file_path, debug = debug)
    tmp_hdf = pd.HDFStore(tmp_hdf_path)
    law = pd.HDFStore(grilles_hdf_path)
    grilles = law.select('grilles')

    careers = tmp_hdf.select('tmp_4')
    assert not careers.duplicated().any(), 'There are duplicated row in careers'
    careers = careers[[
        'grade',
        'trimestre',
        'period',
        'date_effet_grille',
        'ident',
        'ib'
        ]].copy()
    careers.rename(columns = dict(grade = 'code_grade_NETNEH'), inplace = True)
    assert not careers.duplicated().any(), 'There are duplicated row in careers'
    grilles['date_effet_grille'] = [str(annee)[:10] for annee in grilles['date_effet_grille']]
    grilles['date_effet_grille'] = pd.to_datetime(grilles.date_effet_grille)
    careers = careers.merge(
        grilles,
        on = ['code_grade_NETNEH', 'date_effet_grille', 'ib'],
        how = 'outer'
        )
    assert not careers.duplicated().any(), 'There are duplicated row in careers (after merge)'
    careers.to_hdf(
        tmp_hdf_path,
        'tmp_5',
        format = 'table',
        data_columns = True,
        )


def merge_with_additional_variables(variables = None, file_path = None, debug = DEBUG_CLEAN_CARRIERES):
    assert variables is not None
    tmp_hdf_path = get_tmp_hdf_path(file_path, debug = debug)
    tmp_hdf = pd.HDFStore(tmp_hdf_path)
    clean_hdf_path = get_careers_hdf_path(clean_directory_path = clean_directory_path,
        file_path = file_path, debug = debug)
    clean_hdf = pd.HDFStore(clean_hdf_path)

    variables_dataframe = None
    for variable in variables:
        log.info('Getting additional variable {}'.format(variable))
        if 'annee' in clean_hdf.select(variable, stop = 1).columns:
            dataframe = clean_hdf.select(variable, where = 'annee > 2009')
        elif 'generation' in clean_hdf.select(variable, stop = 1).columns:
            dataframe = clean_hdf.select(variable, where = 'generation >= 1950 and generation <= 1959')
        else:
            dataframe = clean_hdf.select(variable)

        dataframe = dataframe[~dataframe['ident'].isnull()]
        dataframe['ident'] = dataframe['ident'].astype(int)

        if variables_dataframe is None:
            variables_dataframe = dataframe
        else:
            longitudinal_data_condition = (
                set(['annee', 'trimestre']) <= set(clean_hdf.select(variable, stop = 1).columns)
                ) and (
                variables_dataframe is None or set(['annee', 'trimestre']) <= set(variables_dataframe.columns)
                )
            merge_on = ['ident', 'annee', 'trimestre'] if longitudinal_data_condition else ['ident']
            variables_dataframe = variables_dataframe.merge(dataframe, on = merge_on, how = 'outer')
            #
        #
        del dataframe
        log.info('variables_dataframe columns are {}'.format(variables_dataframe.columns))
    #
    careers = tmp_hdf.select('tmp_5')
    careers = careers[~careers['ident'].isnull()]
    careers['ident'] = careers['ident'].astype(int)
    careers['trimestre'] = careers['trimestre'].astype(int)
    careers['annee'] = careers.period.dt.year
    careers = careers.merge(variables_dataframe, on = ['ident', 'annee', 'trimestre'], how = 'outer')
    careers = careers[~careers['echelon'].isnull()]
    output_hdf_path = get_output_hdf_path(file_path, debug = debug)
    assert os.path.exists(os.path.dirname(output_hdf_path)), '{} is not a valid path'.format(
        os.path.dirname(output_hdf_path))
    assert not careers.duplicated().any(), 'There are duplicated row in careers'
    fix_dtypes(careers)
    careers.to_hdf(output_hdf_path, 'output', format = 'table', data_columns = True)


def fix_dtypes(careers):  # dtype change might be due to merge and solved in recent version of pandas
    # code_grade_NETNEH            object
    # period               datetime64[ns]
    # date_effet_grille    datetime64[ns]
    # echelon = 'object'
    # code_grade = 'object'
    # etat = 'object'o
    dtype_by_variable = dict(
        trimestre = 'int',
        ident = 'int',
        ib = 'int',
        max_mois = 'int',
        min_mois = 'int',
        moy_mois = 'int',
        annee = 'int',
        )
    for variable, dtype in dtype_by_variable.iteritems():
        if careers[variable].dtype != dtype:
            careers[variable] = careers[variable].astype(dtype)


def main(source = None, force_rebuild = False, debug = DEBUG_CLEAN_CARRIERES):
    build_clean_grille_for_matching(force_rebuild = force_rebuild)
    if os.path.isfile(source):
        stata_files = [source]
    elif os.path.isdir(source):
        stata_files = os.listdir(source)
    for stata_file in stata_files:
        if not stata_file.endswith('.dta'):
            log.info('{} is not a valid stata file. Skipping.'.format(stata_file))
            continue
        log.info('Processing {}'.format(stata_file))
        get_careers_for_which_we_have_law(start_year = 2009, file_path = stata_file, debug = debug)
        get_unique_career_states(file_path = stata_file, debug = debug)
        append_date_effet_to_unique_career_states(file_path = stata_file, debug = debug)
        merge_date_effet_grille_with_careers(file_path = stata_file, debug = debug)
        merge_careers_with_legislation(file_path = stata_file, debug = debug)
        merge_with_additional_variables(variables = ['etat', 'generation'], file_path = stata_file, debug = debug)
        break
