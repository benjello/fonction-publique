# -*- coding: utf-8 -*-
"""
Created on Tue Nov 08 13:26:31 2016

@author: s.rabate

grade_matching_adequacy.py
Testing the quality of the matching between libelles and grade using the years for which we have
both the official grade and the libelles (2011-2014)

"""


from __future__ import division

import logging
import os
import pprint
import sys

import numpy as np
import pandas as pd
from slugify import slugify
from fuzzywuzzy import process

from fonction_publique.base import get_careers, parser, timing
from fonction_publique.merge_careers_and_legislation import get_grilles


pd.options.display.max_colwidth = 0
pd.options.display.max_rows = 999

log = logging.getLogger(__name__)


DEBUG = False
VERSANTS = ['T', 'H']

correspondance_data_frame_path = parser.get('correspondances', 'h5')
corps_correspondance_data_frame_path = parser.get('correspondances', 'corps_h5')
libelles_emploi_tmp_directory = parser.get('correspondances', 'libelles_emploi_tmp_directory')
if not os.path.exists(os.path.dirname(libelles_emploi_tmp_directory)):
    os.makedirs(libelles_emploi_tmp_directory)


def get_true_correspondance(which = None, debug=False):
    """
    Creation du dataframe de la même forme que correspondance avec les grades
    réellement observés
    """
    list_dec = [1970,1980]
    for decennie in list_dec:
        libemploi = get_careers(variable = 'libemploi', decennie = decennie, debug = debug)
        libemploi = libemploi[libemploi.annee>=2011]
        c_netneh = get_careers(variable = 'c_netneh', decennie = decennie, debug = debug)
        c_netneh = c_netneh[c_netneh.annee>=2011]
        statut = get_careers(variable = 'statut', decennie = decennie, debug = debug)
        statut = statut[statut.annee>=2011]
        libemploi = get_careers(variable = 'libemploi', decennie = decennie, debug = debug)
        libemploi = libemploi[libemploi.annee>=2011]
        correspondance_obs = (libemploi.merge(
        statut.query("statut in ['T', 'H']"),
        how = 'inner',
        ))
        correspondance_obs = (correspondance_obs.merge(
        c_netneh.query("c_netneh != '' "),
        how = 'inner',
        ))

        correspondance_obs['libemploi_slugified'] = correspondance_obs.libemploi.apply(slugify, separator = "_")
        # Dropping: libemploi without netneh
        correspondance_obs = correspondance_obs.drop(["ident","libemploi"], 1)
        if decennie == list_dec[0]:
            true_correspondance = correspondance_obs
        else:
            true_correspondance = pd.concat([true_correspondance,correspondance_obs])

    true_correspondance = true_correspondance.drop_duplicates()
    true_correspondance = true_correspondance.sort(['libemploi_slugified'])


    return (true_correspondance)


def load_matched_correspondance(which = None):
    """
    Charge le data frame avec les libellés matchés dans le script grade_matching.py

    Returns
    -------
    data_frame : table de correspondance (chargée, ou nouvelle générée)
    """
    assert which in ['grade', 'corps'], "Seuls les tables des grades et des corps existent"

    data_frame_path = (
        correspondance_data_frame_path
        if which == 'grade'
        else corps_correspondance_data_frame_path
        )
    correspondance_non_available = (
        data_frame_path is None or
        data_frame_path == 'None' or  # None is parsed as string in config.ini
        not os.path.exists(data_frame_path)
        )
    if correspondance_non_available:
        log.info("Il n'existe pas de fichier de correspondances pour le {} à compléter".format(which))
        if which == 'grade':
            data_frame = pd.DataFrame(columns = ['versant', 'grade', 'date_effet', 'annee', 'libelle'])
        if which == 'corps':
            data_frame = pd.DataFrame(columns = ['versant', 'corps', 'libelle'])  # TODO: Add annee
        data_frame.annee = data_frame.annee.astype(int)
        return data_frame
    else:
        log.info("Laa table de correspondance {} est utilisé comme point de départ".format(
            data_frame_path))
        data_frame = pd.read_hdf(correspondance_data_frame_path, 'correspondance')
        return data_frame


def get_grilles_cleaned(annee=None):
    '''
    Correction des doublons dans la grille initiale
    '''
    grilles = get_grilles(
        date_effet_max = "{}-12-31".format(annee),
        subset = ['libelle_FP', 'libelle_grade_NEG'],
        )
    # Analyse des doublons
    grilles.loc[grilles.libelle_grade_NEG=='INFIRMIER DE CLASSE NORMALE (*)','libelle_grade_NEG']= 'INFIRMIER DE CLASSE NORMALE(*)'
    grilles.loc[grilles.libelle_grade_NEG=='INFIRMIER DE CLASSE SUPERIEURE (*)','libelle_grade_NEG']= 'INFIRMIER DE CLASSE SUPERIEURE(*)'
    return grilles


@timing
def load_libelles_emploi_data(decennie = None, debug = False, force_recreate = False):
    assert decennie is not None

    libemploi_h5 = os.path.join(libelles_emploi_tmp_directory, 'libemploi_{}.h5'.format(decennie))
    if os.path.exists(libemploi_h5) and not force_recreate:
        libemplois = pd.read_hdf(libemploi_h5, 'libemploi')
        log.info("Libellés emploi read from {}".format(libemploi_h5))
    else:
        libemploi = get_careers(variable = 'libemploi', decennie = decennie, debug = debug)
        statut = get_careers(variable = 'statut', decennie = decennie, debug = debug)
        libemploi = (libemploi.merge(
            statut.query("statut in ['T', 'H']"),
            how = 'inner',
            ))
        libemploi['libemploi_slugified'] = libemploi.libemploi.apply(slugify, separator = "_")
        libemploi.rename(columns = dict(statut = 'versant'), inplace = True)
        libemplois = libemploi.groupby([u'annee', u'versant'])['libemploi_slugified'].value_counts()
        log.info("Generating and saving libellés emploi to {}".format(libemploi_h5))
        libemplois.to_hdf(libemploi_h5, 'libemploi')
    return libemplois


def print_stats(libemplois = None, annee = None, versant = None):
    correspondance_data_frame = get_correspondance_data_frame(which = 'grade')[
        ['versant', 'annee', 'date_effet', 'libelle']
        ].rename(
            columns = dict(annee = 'annee_stop', libelle = 'libemploi_slugified')
            ).copy()
    correspondance_data_frame['annee_start'] = pd.to_datetime(
        correspondance_data_frame.date_effet
        ).dt.year
    del correspondance_data_frame['date_effet']
    libemplois.name = 'count'
    merged_libemplois = (libemplois
        .reset_index()
        .query("libemploi_slugified != ''")  # On ne garde pas les libellés vides
        .merge(correspondance_data_frame)
        )
    libelles_emploi_deja_renseignes = (merged_libemplois
        .query('annee_start <= annee <= annee_stop')
        .drop(['annee_start', 'annee_stop'], axis = 1)
        .drop_duplicates()
        )
    selectionnes = libelles_emploi_deja_renseignes.groupby(['annee', 'versant']).agg({
        'count': 'sum',
        'libemploi_slugified': 'count',
        }).rename(columns = dict(count = 'selectionnes_ponderes', libemploi_slugified = 'selectionnes'))

    total = libemplois.reset_index().groupby(['annee', 'versant']).agg({
        'count': 'sum',
        'libemploi_slugified': 'count',
        }).rename(columns = dict(count = 'total_ponderes', libemploi_slugified = 'total'))

    result = total.merge(selectionnes, left_index = True, right_index = True, how = 'outer').fillna(0)

    result.selectionnes_ponderes = result.selectionnes_ponderes.astype(int)
    result.selectionnes = result.selectionnes.astype(int)
    result['pct_pondere'] = 100 * result.selectionnes_ponderes / result.total_ponderes
    result['pct'] = 100 * result.selectionnes / result.total
    print(result.sort_index(ascending = False))

    #     print("""
    # Pondéré:
    # {0} / {1} = {2:.2f} % des libellés emplois non vides ({3} vides soit {4:.2f} %) sont attribués
    # """.format(
    #         selectionnes_weighted_count,
    #         total_weighted_count,
    #         100 * selectionnes_weighted_count / total_weighted_count,
    #         vides_count,
    #         100 * vides_count / total_weighted_count,
    #         ))
    #     print("""
    # Non pondéré:\n{0} / {1} = {2:.2f} % des libellés emplois  sont attribués
    # """.format(
    #         selectionnes_count,
    #         total_count,
    #         100 * selectionnes_count / total_count,
    #         ))


def get_libelle_to_classify(libemplois = None):
    '''
    Fonction d'initialisation des libellés à classer, à partir de la

    Parameters
    ----------
    libemplois : Liste de l'ensemble des libellés

    Returns
    -------
    Liste ordonnée (selon le nombre d'occurence) des libellés restant à classer pour une année donnée
    '''
    assert libemplois is not None
    libelles_emploi_deja_renseignes_dataframe = get_correspondance_data_frame(which = 'grade')
    annees = libemplois.index.get_level_values('annee').sort_values(ascending = False)
    for annee in annees:
        result = dict()
        for versant in VERSANTS:
            libelles_emploi_deja_renseignes = (libelles_emploi_deja_renseignes_dataframe
                .loc[pd.to_datetime(
                    libelles_emploi_deja_renseignes_dataframe.date_effet
                    ).dt.year <= annee]
                .query("(annee >= @annee) &  (versant == @versant)")
                ).libelle.tolist()
            #
            result[versant] = (libemplois
                .loc[annee, versant]
                .loc[~libemplois.loc[annee, versant].index.isin(libelles_emploi_deja_renseignes)]
                ).head(1)
            #
        #
        if result['T'].empty and result['H'].empty:
            continue

        libelle = None
        frequence = 0
        for versant_itere, serie in result.iteritems():
            assert len(serie) == 1
            if serie.values[0] > frequence:
                versant = versant_itere
                libelle = serie.index[0]
                frequence = max(frequence, serie.max())

        print_stats(
            libemplois = libemplois,
            annee = annee,
            versant = versant
            )

        return versant, annee, libelle

    return None


def store_corps(libelles_emploi = None, grade_triplet = None):
    # TODO: fix grade_triplet = ('corps', versant, corps)
    data_frame = get_correspondance_data_frame(which = 'corps')
    for libelle in libelles_emploi:
        versant = grade_triplet[1]
        corps = grade_triplet[2]
        data_frame = data_frame.append(pd.DataFrame(  # Add annee
            data = [[versant, corps, libelle]],
            columns = ['versant', 'corps', 'libelle']
            ))
    log.info('Writing corps_correspondance_data_frame to {}'.format(corps_correspondance_data_frame_path))
    data_frame.to_hdf(corps_correspondance_data_frame_path, 'correspondance', format = 'table', data_columns = True)


def select_and_store(libelle_emploi = None, annee = None, versant = None, libemplois = None):
    grade_triplet = select_grade_neg(
        libelle_saisi = libelle_emploi,
        annee = annee,
        versant = versant,
        )

    if grade_triplet is None:
        return 'break'
    if grade_triplet == "next":
        return 'continue'

    if grade_triplet[0] == 'corps':
        store_corps(
            libelles_emploi = [libelle_emploi],
            grade_triplet = grade_triplet,
            )
        return 'continue'

    store_libelles_emploi(
        libelles_emploi = [libelle_emploi],
        annee = annee,
        grade_triplet = grade_triplet,
        libemplois = libemplois,
        )

    while True:
        libelles_emploi_selectionnes, next_grade = select_libelles_emploi(
            grade_triplet = grade_triplet,
            libemplois = libemplois,
            annee = annee,
            versant = versant,
            )

        if libelles_emploi_selectionnes:
            store_libelles_emploi(
                libelles_emploi = libelles_emploi_selectionnes,
                annee = annee,
                grade_triplet = grade_triplet,
                libemplois = libemplois,
                )
        if next_grade:
            return 'continue'


def main(decennie = None):
    assert decennie is not None
    libemplois = load_libelles_emploi_data(decennie = decennie)
#    grilles = get_grilles(subset = ['libelle_FP', 'libelle_grade_NEG'])
#    libelles_grade_NEG = sorted(grilles.libelle_grade_NEG.unique().tolist())
#    print("Il y a {} libellés emploi différents".format(len(libemplois)))
#    print("Il y a {} libellés grade NEG différents".format(len(libelles_grade_NEG)))

    while True:
        versant, annee, libelle_emploi = get_libelle_to_classify(
            libemplois = libemplois,
            )
        if libelle_emploi == "":
            log.info("On ignore les libelle_emploi vides")
            continue
        print("""
annee: {}
versant: {}
libelle emploi: {}
""".format(annee, versant, libelle_emploi))

        result = select_and_store(
            libelle_emploi = libelle_emploi,
            annee = annee,
            versant = versant,
            libemplois = libemplois,
            )
        if result == 'continue':
            continue
        elif result == 'break':
            break

        while True:
            selection = raw_input("""
o: passage à l'année suivante. q : quitter
selection: """)
            if selection == "o":
                break
            if selection == "q":
                return
            else:
                continue


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    main(decennie = 1970)
