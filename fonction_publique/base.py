# -*- coding:utf-8 -*-


from __future__ import division


import ConfigParser
import logging
import os
import re
import time

import pkg_resources

import pandas as pd

from fonction_publique.config import Config

parser = Config()

app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)

# Paths to legislation

project_path = os.path.join(
    pkg_resources.get_distribution('fonction_publique').location,
    'fonction_publique'
    )

asset_path = os.path.join(
    project_path,
    'assets',
    )

grilles_path = os.path.join(
    project_path,
    'assets',
    'grilles_fonction_publique',
    )

grilles_txt_path = os.path.join(
    grilles_path,
    "neg_pour_ipp.txt",
    )

focus_grille_xlsx_path = os.path.join(
    grilles_path,
    "corresp_neg_netneh_2018.xlsx",
    )

grilles_hdf_path = os.path.join(
    grilles_path,
    "grilles.h5",
    )

grilles_matching_hdf_path = os.path.join(
    grilles_path,
    "grilles_matching.h5",
    )

table_correspondance_corps_path = os.path.join(
    asset_path,
    'corresp_neg_netneh.csv'
    )

grilles = pd.read_hdf(
    os.path.join(grilles_hdf_path),
    )

# Directories paths:
raw_directory_path = parser.get('data', 'raw')
tmp_directory_path = parser.get('data', 'tmp')
clean_directory_path = parser.get('data', 'clean')
output_directory_path = parser.get('data', 'output')
try:
    simulation_directory_path = parser.get('data', 'simulation')
except ConfigParser.NoOptionError:
    log.info('Entry simulation in section data is absent. simulation_directory_path is not set')
    simulation_directory_path = None


# Options:
DEFAULT_CHUNKSIZE = 30000
DEBUG_CLEAN_CARRIERES = True
debug_chunk_size = 30000


# HDF5 files paths (temporary):
# Store des variables liées aux carrières nettoyées et stockées dans des tables du fichier donnees_de_carrieres.h5
def get_careers_hdf_path(clean_directory_path = None, file_path = None, debug = None):
    return create_file_path(
        directory = clean_directory_path,
        extension = 'carrieres',
        file_path = file_path,
        debug = debug,
        )


def get_tmp_hdf_path(file_path, debug = None):
    return create_file_path(
        directory = tmp_directory_path,
        extension = 'tmp',
        file_path = file_path,
        debug = debug,
        )


def get_output_hdf_path(file_path, debug = None):
    years = re.findall(r'\d+', file_path)
    assert int(years[0]) < int(years[1])
    assert debug is not None, 'debug should be True or False'
    output_hdf_path = os.path.join(
        output_directory_path,
        "debug",
        "{}_{}".format(years[0], years[1])
        ) if debug else os.path.join(
        output_directory_path,
        "{}_{}.h5".format(years[0], years[1]),
        )
    return output_hdf_path


# Helpers

def create_file_path(directory = None, extension = None, file_path = None, debug = None):
    assert directory is not None
    assert extension is not None
    assert (debug is False) or (debug is True), 'debug should be True or False'
    assert file_path is not None
    years = re.findall(r'\d+', file_path)
    filename = "{}_{}_{}.h5".format(
        years[0],
        years[1],
        extension,
        )
    if debug:
        return os.path.join(directory, "debug", filename)
    else:
        return os.path.join(directory, filename)


def get_variables(variables = None, stop = None, decennie = None):
    """Recupere certaines variables de la table des carrières matchées avec grilles"""
    if decennie == 1990:
        hdf5_file_path = os.path.join(output_directory_path, '{}_{}_carrieres.h5'.format(decennie, decennie + 6))
    else:
        hdf5_file_path = os.path.join(output_directory_path, '{}_{}_carrieres.h5'.format(decennie, decennie + 9))
    return pd.read_hdf(hdf5_file_path, 'output', columns = variables, stop = stop)


def get_careers(variable = None, variables = None, stop = None, data_path = None, debug = False, where = None):
    """Recupere certaines variables de la table des carrières bruts"""
    assert (data_path is not None)
    assert (variable is not None) or (variables is not None)
    assert not(
        (variable is not None) and (variables is not None)
        )
    if debug:
        actual_clean_directory_path = os.path.join(
            clean_directory_path,
            'debug',
            )
    else:
        actual_clean_directory_path = clean_directory_path

    careers_hdf_path = os.path.join(actual_clean_directory_path, data_path)

    if variable:
        log.info('Reading variable {} from file {}'.format(variable, careers_hdf_path))
        return pd.read_hdf(careers_hdf_path, variable, stop = stop, where = where)
    elif variables:
        with pd.HDFStore(careers_hdf_path) as store:
            return store.select_as_multiple(
                variables,
                columns = variables,
                where = where,
                selector = variables[0]
                )


def add_grilles_variable(data, grilles = grilles, first_year = 2011, last_year = 2015):  # FIXME deal with late policy implementation
    """Add grilles variables to observation according to their grade (code_grade_NETNEH == c_cir)
    """
    log.info('Add grilles variables')
    data_after_first_year = data.query('(annee >= @first_year)').copy()
    cas_uniques_with_echelon = list()
    for annee in range(first_year, last_year + 1):
        cas_uniques = (data_after_first_year
            .query('annee == @annee')[['c_cir', 'ib']]
            .drop_duplicates()
            .set_index(['c_cir', 'ib'])
            )
        for (c_cir, ib), row in cas_uniques.iterrows():
            date_effet_grille = grilles[
                (grilles['code_grade_NETNEH'] == c_cir) &
                (grilles['date_effet_grille'] <= pd.datetime(annee, 12, 31))
                ].date_effet_grille.max()
            grille_in_effect = grilles[
                (grilles['code_grade_NETNEH'] == c_cir) &
                (grilles['date_effet_grille'] == date_effet_grille)
                ].query('ib == @ib')
            if grille_in_effect.empty:
                echelon = -1
                min_mois = -1
                moy_mois = -1
                max_mois = -1
                date_effet_grille = -1
            else:
                grille_in_effect = grille_in_effect
                assert len(grille_in_effect) == 1
                echelon = grille_in_effect.echelon.values.astype(str)[0]
                min_mois = grille_in_effect.min_mois.values.astype(int)[0]
                moy_mois = grille_in_effect.moy_mois.values.astype(int)[0]
                max_mois = grille_in_effect.max_mois.values.astype(int)[0]
                date_effet_grille = grille_in_effect.date_effet_grille.values.astype(str)[0]
            cas_uniques_with_echelon.append(
                [annee, c_cir, ib, echelon, min_mois, moy_mois, max_mois, date_effet_grille]
                )
    cas_uniques = pd.DataFrame(
        cas_uniques_with_echelon,
        columns = ['annee', 'c_cir', 'ib', 'echelon', 'min_mois', 'moy_mois', 'max_mois', 'date_effet_grille'],
        )
    assert not cas_uniques[['c_cir', 'ib', 'annee']].duplicated().any()
    data = data.merge(cas_uniques, on = ['c_cir', 'ib', 'annee'], how = 'left')
    data['echelon'] = data['echelon'].fillna(-2).astype(int)
    return data


# Timer
def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        log.info('{} function took {:.3f} s'.format(f.func_name, (time2 - time1)))
        return ret
    return wrap
