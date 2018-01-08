# -*- coding:utf-8 -*-


from __future__ import division

import logging
import pandas as pd
import numpy as np
import os
import sys

from fonction_publique.base import (
    focus_grille_xlsx_path,
    grilles_hdf_path,
    grilles_matching_hdf_path,
    grilles_txt_path,
    table_correspondance_corps_path,
    )

app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)

dtype_by_variable = {
    "categh": str,
    "code_etat_grade": int,
    "code_FP": int,
    "code_grade_NEG": str,
    "code_grade_NETNEH": str,
    "code_type_groupe": str,
    "date_effet_grille": str,
    "date_fin": str,
    "echelle": str,
    "echelon": str,
    "ib": float,
    "libelle_FP": str,
    "libelle_grade_NEG": str,
    "max_mois": float,
    "min_mois": float,
    "moy_mois": float,
    "type_grade": str,
    }


def read_correspondace_grade_corps():
    correspondance_grade_corps = pd.read_csv(
        table_correspondance_corps_path,
        usecols = [
            'CadredemploiNEG',
            'cadredemploiNETNEH',
            'CodeEmploiGrade_neg',
            ],
        dtype = {
            'CadredemploiNEG': str,
            'cadredemploiNETNEH': str,
            'CodeEmploiGrade_neg': str,
            },
        sep = ';',
        ).rename(columns = {
            'CadredemploiNEG': 'corps_NEG',
            'cadredemploiNETNEH': 'corps_NETNEH',
            'CodeEmploiGrade_neg': 'code_grade_NEG',
            })
    correspondance_grade_corps['code_grade_NEG'] = [s.lstrip("0") for s in correspondance_grade_corps['code_grade_NEG']]
    return correspondance_grade_corps


def read_exhaustive():
    """
    Read almost exhaustive data on grilles and adjust dtypes and homogeneize variables
    location: grilles_txt_path (neg_pour_ipp.txt)
    """
    exhaustive = pd.read_table(
        grilles_txt_path,
        dtype = dtype_by_variable,
        usecols = [
            'categh',
            'code_grade_NEG',
            'code_grade_NETNEH',
            'date_effet_grille',
            'echelle',
            'echelon',
            'ib',
            'libelle_grade_NEG',
            'libelle_FP',
            'max_mois',
            'min_mois',
            'moy_mois',
            ],
        )
    exhaustive['date_effet_grille'] = pd.to_datetime(
        exhaustive['date_effet_grille'],
        dayfirst = True,
        infer_datetime_format = True,
        )  # .dt.to_period('M')
    # Strip ending spaces in libelle_grade_NEG
    exhaustive['libelle_grade_NEG'] = exhaustive['libelle_grade_NEG'].str.rstrip(' ')
    return exhaustive


def read_focus():
    """
    Read focus sample data on grilles and adjust dtypes and homogeneize variables
    focus_grille_xlsx_path (corresp_neg_netneh_2018.xlsx): focus sample with additonal date_fin, etc columns
    """
    focus = pd.read_excel(
        focus_grille_xlsx_path,
        dtype = dtype_by_variable,
        )

    focus.rename(
        columns = {
            'Corps': 'corps',
            'date_effet_grille': 'date_debut_grade',
            'date_fin': 'date_fin_grade',
            'Filiere': 'filiere',
            },
        inplace = True,
        )

    focus.replace(
        {
            'code_grade_NETNEH': {
                'inconnu': np.nan,
                'Inconnu': np.nan,
                },
            },
        inplace = True,
        )

    for date_variable in ['date_debut_grade', 'date_fin_grade']:
        focus[date_variable] = pd.to_datetime(
            focus[date_variable],
            dayfirst = True,
            infer_datetime_format = True,
            errors = 'coerce'
            )

    # Strip zeros from some variable in focus
    focus['echelle'] = focus['echelle'].str.lstrip('0')
    focus['echelle'].replace({'nan': np.nan}, inplace = True)
    focus['code_grade_NEG'] = focus['code_grade_NEG'].str.lstrip('0')
    # Strip ending spaces in libelle_grade_NEG
    focus['libelle_grade_NEG'] = focus['libelle_grade_NEG'].str.replace("\(\*\)", "")
    focus['libelle_grade_NEG'] = focus['libelle_grade_NEG'].str.rstrip(' ')
    for problematic_mixed_string in ['corps', 'filiere', 'libelle_NETNEH']:
        focus[problematic_mixed_string] = focus[problematic_mixed_string].str.normalize('NFKD').str.encode(
            'ascii', errors='ignore').str.decode('utf-8').astype(str)
    assert not focus[['code_grade_NEG', 'libelle_grade_NEG', 'libelle_NETNEH', 'date_debut_grade']].duplicated().any()

    return focus


def check_grilles():
    """
    Check the coherence betwenn the following grilles:
        grilles_txt_path (neg_pour_ipp.txt): almost exhaustive grilles

    """
    exhaustive = read_exhaustive()
    focus = read_focus()
    common_variables = set(focus.columns).intersection(set(exhaustive.columns))
    print common_variables
    problematic_variables = list()
    for variable in common_variables:
        differences = set(focus[variable].unique()).difference(set(exhaustive[variable].unique()))
        if differences:
            problematic_variables.append(variable)
            print variable
            print differences
            print '\n'

    for variable in problematic_variables:
        print variable
        print focus[variable].unique()
        print exhaustive[variable].unique()
        print '\n'


def prepare_grille(grille):
        # Filter some invalid IB's
        grille = grille[~grille['ib'].isin([-1, 0])].copy()

        # Set special echelons to -5
        special_echelons = list(
            set(grille.echelon.unique()) - set([str(n).zfill(2) for n in range(1, 25)] + [str(n) for n in range(1, 25)])
            )
        grille.loc[grille['echelon'].isin(special_echelons), 'echelon'] = '-5'

        # Creating anne_grille as int. Missing integers are coded as -1
        grille['annee_effet_grille'] = (grille['date_effet_grille']
            .dt.year
            .fillna(-1)
            .astype('int32')
            )
        # Missing integers are coded as -1
        for col in [
                'echelon',
                'ib',
                'max_mois',
                'min_mois',
                'moy_mois'
                ]:
            grille[col] = grille[col].fillna(-1).astype('int32')

        for col in [
                'categh',
                'code_grade_NEG',
                'code_grade_NETNEH',
                'echelle',
                'libelle_grade_NEG',
                ]:
            grille[col] = grille[col].fillna(-1).astype(str)
        #
        return grille


def clean_grille(force_rebuild = False, hdf_path = grilles_hdf_path):
    """ Extract relevant data from neg_pour_ipp.txt and change to convenient dtype then save to HDFStore."""
    if force_rebuild is True:
        grille = read_exhaustive()
        grille = prepare_grille(grille)
        correspondace_grade_corps = read_correspondace_grade_corps()
        grille = grille.merge(correspondace_grade_corps, on = 'code_grade_NEG', how = 'left')
        grille.to_hdf(hdf_path, 'grilles', format = 'table', data_columns = True, mode = 'w')
        return True
    else:
        if os.path.exists(hdf_path):
            log.info('Using existing {}'.format(hdf_path))
            return True
        else:
            clean_grille(force_rebuild = True, hdf_path = hdf_path)


def build_clean_grille_for_matching(force_rebuild = False, hdf_path = grilles_matching_hdf_path):
    """ Extract relevant data from neg_pour_ipp.txt and change to convenient dtype then save to HDFStore."""
    if force_rebuild:
        log.info('Rebuilding matching grilles')
        exhaustive = read_exhaustive()
        focus = read_focus()
        grille = focus.merge(
            exhaustive[[
                'code_grade_NEG',
                # 'code_grade_NETNEH',
                'date_effet_grille',
                'echelon',
                'ib',
                'libelle_grade_NEG',
                'max_mois',
                'min_mois',
                'moy_mois',
                ]],
            on = ['code_grade_NEG', 'libelle_grade_NEG']
            )
        grille = prepare_grille(grille)
        correspondace_grade_corps = read_correspondace_grade_corps()
        grille = grille.merge(correspondace_grade_corps, on = 'code_grade_NEG', how = 'left')
        grille[[
            'num_meme_corps',        # int64
            'corps',                 # object  To translate from unicode
            'num_meme_filiere',      # int64
            'filiere',               # object  To translate from unicode
            'code_grade_NEG',        # object
            'code_FP',               # int64unidecode.unidecode
            'libelle_FP',            # object
            'code_etat_grade',       # int64
            'libelle_grade_NEG',     # object
            'categh',                # object
            'echelle',               # object
            'date_debut_grade',      # datetime64[ns]
            'date_fin_grade',        # datetime64[ns]
            'code_grade_NETNEH',     # object
            # 'type_grade',            # object VIDE
            'libelle_NETNEH',        # object  To translate from unicode
            'date_effet_grille',     # datetime64[ns]
            'echelon',               # int32
            'ib',                    # int32
            'max_mois',              # int32
            'min_mois',              # int32
            'moy_mois',              # int32
            'annee_effet_grille',    # int32
            ]].to_hdf(hdf_path, 'grilles', format = 'table', data_columns = True, mode = 'w')
        return True
    else:
        if os.path.exists(hdf_path):
            log.info('Using existing {}'.format(hdf_path))
            return True
        else:
            build_clean_grille_for_matching(force_rebuild = True, hdf_path = hdf_path)


def main():
    # read_focus()
    build_clean_grille_for_matching(force_rebuild = True)
    # check_grilles()


if __name__ == "__main__":
    sys.exit(main())
