#!/usr/bin/env python
# -*- coding:utf-8 -*-


from __future__ import division

from datetime import datetime
import logging
import os
import pprint
import sys

import numpy as np
import pandas as pd
from slugify import slugify
from fuzzywuzzy import process

from fonction_publique.base import get_careers, parser
from fonction_publique.merge_careers_and_legislation import get_grilles

pd.options.display.max_colwidth = 0
pd.options.display.max_rows = 999

log = logging.getLogger(__name__)


DEBUG = False
VERSANTS = ['T', 'H']

correspondance_data_frame_path = parser.get('correspondances', 'h5')
corps_correspondance_data_frame_path = parser.get('correspondances', 'corps_h5')
libelles_emploi_directory = parser.get('correspondances', 'libelles_emploi_directory')


def get_correspondance_data_frame(which = None, netneh = False):
    """
    Charge la table avec les libellés déjà classés.

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
            if netneh:
                data_frame = pd.DataFrame(
                    columns = ['versant', 'grade', 'date_debut_grade', 'date_fin_grade', 'libelle'])
            else:
                data_frame = pd.DataFrame(columns = ['versant', 'grade', 'date_effet', 'annee', 'libelle'])
                data_frame.annee = data_frame.annee.astype(int)
        if which == 'corps':
            data_frame = pd.DataFrame(columns = ['versant', 'corps', 'libelle'])  # TODO: Add annee
            data_frame.annee = data_frame.annee.astype(int)
        return data_frame
    else:
        log.info("La table de correspondance {} est utilisé comme point de départ".format(
            data_frame_path))
        data_frame = pd.read_hdf(correspondance_data_frame_path, 'correspondance')
        return data_frame


def get_grilles_cleaned(annee = None, versant = None, force_rebuild = False, subset = None):
    '''
    Correction des doublons dans la grille initiale
    TODO remove when cleaning
    '''

    if subset is None:
        subset = [
            'code_grade_NEG',
            'libelle_FP',
            'libelle_grade_NEG',
            ]
    if annee is not None:
        grilles = get_grilles(
            date_effet_max = "{}-12-31".format(annee),
            subset = subset,
            force_rebuild = force_rebuild,
            )
    else:
        grilles = get_grilles(
            subset = subset,
            force_rebuild = force_rebuild
            )
    grilles.loc[
        grilles.libelle_grade_NEG == 'INFIRMIER DE CLASSE NORMALE (*)', 'libelle_grade_NEG'
        ] = 'INFIRMIER DE CLASSE NORMALE(*)'
    grilles.loc[
        grilles.libelle_grade_NEG == 'INFIRMIER DE CLASSE SUPERIEURE (*)', 'libelle_grade_NEG'
        ] = 'INFIRMIER DE CLASSE SUPERIEURE(*)'
    if versant is None:
        return grilles
    elif versant == 'H':
        return grilles.query("libelle_FP == 'FONCTION PUBLIQUE HOSPITALIERE'").copy()
    elif versant == 'T':
        return grilles.query("libelle_FP == 'FONCTION PUBLIQUE TERRITORIALE'").copy()
    else:
        raise ValueError("versant should be 'H', 'T'' or None")


def load_libelles_emploi_data(decennie = None, debug = False, force_recreate = False):
    assert decennie is not None
    libemploi_h5 = os.path.join(libelles_emploi_directory, 'libemploi_{}.h5'.format(decennie))
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
    libemplois = libemplois.loc[2006:2014, ]
    return libemplois


def query_grade_neg(query = None, choices = None, score_cutoff = 95):
    u'''
    A partir de libelés NETNEH observés, va chercher les 50 libellés les plus proches dans
    la liste des libellés officiels des grades. En l'absence de résultats, on abaisse le seuil.

    Parameters
    ----------
    query : libéllé à classer
    choices : liste possible des libellés de grade "officiels"
    score_cutoff : score limite

    Returns
    -------
    Liste de grades correspondants avec les scores de matching associés.
    '''
    assert query is not None
    assert choices is not None
    slugified_choices = [slugify(choice, separator = '_') if (choice is not np.nan) else '' for choice in choices]
    slugified_query = slugify(query, separator = '_')
    results = process.extractBests(slugified_query, slugified_choices, score_cutoff = score_cutoff, limit = 50)
    if results:
        choice_by_slug = dict(zip(slugified_choices, choices))
        data_frame = pd.DataFrame.from_records(results, columns = ['slug_grade_neg', 'score'])
        data_frame['libelle_grade_neg'] = data_frame.slug_grade_neg.map(choice_by_slug)
        return data_frame
    else:
        return query_grade_neg(query, choices = choices, score_cutoff = score_cutoff - 5)


def query_libelles_emploi(query = None, choices = None, last_min_score = 100):
    '''
    A partir du grade attribué à un libellé saisi à la main, cherche parmi les autres
    libellés saisis à la main des correspondances pour le grade choisi.

    Parameters
    ----------
    query : libellé de grade officiel à rapprocher des libellés saisis
    choices : list, liste possible des libellés saisis
    last_min_score : int, default 100, score

    Returns
    -------
    DataFrame de libellés correspondants avec les score de matching associés.
    '''
    assert query is not None
    assert choices is not None

    slugified_query = slugify(query, separator = '_')
    min_score = 100
    score_cutoff = last_min_score

    empty = True
    extracted_results = process.extractBests(slugified_query, choices, limit = 50)
    while ((min_score > last_min_score) | empty):
        score_cutoff = score_cutoff - 5
        if score_cutoff < 0:
            log.info("Aucun libellé emploi ne correspondant à {}.".format(query))
            break
            # return None
        results = [result for result in extracted_results if result[1] >= score_cutoff]
        if results:
            min_score = min([result[1] for result in results])
            empty = False
        else:
            empty = True
            continue

    log.info("Recherche de libellés emploi correspondant à {}:\n slug: {}\n score >= {}".format(
        query, slugified_query, score_cutoff))
    return pd.DataFrame.from_records(results, columns = ['libelle_emploi', 'score'])


def select_grade_neg(libelle_saisi = None, annee = None, versant = None):  # Rename select_grade_or_corps
    '''
    Fonction de sélection par l'utilisateur du grade adéquat parmi les choix possibles.
    On charge les grades officiels de l'année courante, puis
    générés par la fonction query_grade_neg. L'utilisateur saisi un unique grade correspondant.
    Si aucun grade ne correspond au libellé considéré, l'utilisateur peut soit abaisser le
    seuil, soit rentrer un grade à la main, soit décider de ne pas classer le grade.

    Parameters
    ----------
    libelle_saisi : str, Libellé à classer
    annee : int, année courante
    versant : 'H' or 'T', versant de la fonction publique

    Returns
    -------
    grade_neg : tuple, (versant, grade, date d'effet) du grade correspondant
                ou ('corps', versant, corps) pour le libellé considéré.
    '''
    assert libelle_saisi is not None
    assert annee is not None
    assert versant in VERSANTS, "versant {} is not in {}".format(versant, VERSANTS)

    score_cutoff = 95

    grilles = get_grilles_cleaned(annee, versant = versant)

    unique_grilles = grilles.groupby(['libelle_grade_NEG', 'code_grade_NEG']).count()
    unique_grilles = unique_grilles.reset_index()
    libelles_grade_NEG = grilles['libelle_grade_NEG'].unique()

    while True:
        grades_neg = query_grade_neg(query = libelle_saisi, choices = libelles_grade_NEG, score_cutoff = score_cutoff)
        print("\nGrade NEG possibles pour {} (score_cutoff = {}):\n{}".format(libelle_saisi, score_cutoff, grades_neg))
        selection = raw_input("""
Present: entrer un NOMBRE
Non present: plus de choix (n), rentrer a la main (m)
Autre: classer comme corps (c), quitter(q)
selection: """)
        if selection == "q":
            return "quit"
        elif selection == "n":
            score_cutoff -= 5
            continue
        elif selection == "m":
            grade_neg = hand_select_grade(
                libelle_a_saisir = libelle_saisi, choices = libelles_grade_NEG, annee = annee)
            if grade_neg:
                break
            else:
                continue

        elif selection == "c":
            corps = select_corps(libelle_saisi = libelle_saisi, annee = annee, versant = versant)
            break
        elif selection.isdigit() and int(selection) in grades_neg.index:
            grade_neg = grades_neg.loc[int(selection), "libelle_grade_neg"]
            break
        else:
            print('Plage de valeurs incorrecte')
            continue

    if selection == "c":
        return ("corps", versant, corps)  # TODO improve
    else:
        date_effet_grille = grilles.loc[
            grilles.libelle_grade_NEG == grade_neg
            ].date_effet_grille.min().strftime('%Y-%m-%d')
        libelle_FP = grilles.loc[grilles.libelle_grade_NEG == grade_neg].libelle_FP.unique().squeeze().tolist()
        # libelle_FP is 'FONCTION PUBLIQUE TERRITORIALE' or 'FONCTION PUBLIQUE HOSPITALIERE' or the list containing both
        if versant == 'H':
            assert libelle_FP == 'FONCTION PUBLIQUE HOSPITALIERE' or 'FONCTION PUBLIQUE HOSPITALIERE' in libelle_FP
        elif versant == 'T':
            assert libelle_FP == 'FONCTION PUBLIQUE TERRITORIALE' or 'FONCTION PUBLIQUE TERRITORIALE' in libelle_FP

    print("""Le grade NEG suivant a été sélectionné:
 - versant: {}
 - libellé du grade: {}
 - date d'effet la plus ancienne: {}""".format(
        versant,
        grade_neg,
        date_effet_grille,
        ))
    return (versant, grade_neg, date_effet_grille)


def hand_select_grade(libelle_a_saisir = None, choices = None, annee = None):
    '''
    Fonction de sélection par l'utilisateur du grade adéquat pour le libellé donné.
    L'utilisateur saisi à la main un grade, et on cherche dans la liste officielle
    le grade qui s'en rapproche le plus pour confirmation.

    Paremeter
    ---------
    libelle_a_saisir : libellé à classer
    choices : libellé
    annee : année courante

    Returns
    -------
    grade_neg : libellé du grade officiel
    '''
    assert libelle_a_saisir is not None
    assert annee is not None
    score_cutoff = 95

    while True:
        print("Saisir un libellé à la main pour {}:".format(libelle_a_saisir))
        libelle_saisi = raw_input("""
SAISIR UN LIBELLE, quitter (q)
selection: """)
        if libelle_saisi == "q":
            return
        else:
            print("Libellé saisi: {}".format(libelle_saisi))
            selection = raw_input("""
LIBELLE OK (o), RECOMMENCER LA SAISIE (r)
selection: """)
            if selection not in ["o", "q", "r"]:
                print('Plage de valeurs incorrecte (choisir o ou r)')
            elif selection == "r":
                continue
            elif selection == "o":
                grades_neg = query_grade_neg(query = libelle_saisi, choices = choices, score_cutoff = score_cutoff)
                print("\nGrade NEG possibles pour {} (score_cutoff = {}):\n{}".format(
                    libelle_saisi, score_cutoff, grades_neg))
                selection2 = raw_input("""
NOMBRE, recommencer la saisie(r), quitter (q)
selection: """)
                if selection2 == "q":
                    return
                elif selection2 == "r":
                    continue
                elif selection2.isdigit() and int(selection2) in grades_neg.index:
                    grade_neg = grades_neg.loc[int(selection2), "libelle_grade_neg"]
                    return grade_neg


def select_corps(libelle_saisi = None, annee = None, versant = None):
    '''
    Sélectionne le corps dans la liste des corps dans le versant idoine

    Parameters
    ----------
    libelle_saisi: str, libellé saisi
    annee: int, année
    versant : str, 'H' ou 'T' indispensable

    Returns
    -------
    corps: str, le coprs
    '''
    # Provisoire: on regroupe les libellés que l'on souhaite classer comme corps dans
    # un grade ad hoc 'to_match_to_corps' pour chaque versant.
    # A modifier quand on obtient la liste des corps.

    print('Ici je pourrais choisir mon corps')
    corps = 'corps'
    return corps


def select_libelles_emploi(grade_triplet = None, grade_quadruplet = None, **kwargs):
    assert (grade_triplet is not None) ^ (grade_quadruplet is not None)  # ^ = xor
    if grade_triplet:
        return select_libelles_emploi_from_grade_triplet(grade_triplet = grade_triplet, **kwargs)
    if grade_quadruplet:
        return select_libelles_emploi_from_grade_quadruplet(grade_quadruplet = grade_quadruplet, **kwargs)


def select_libelles_emploi_from_grade_quadruplet(grade_quadruplet = None, libemplois = None,
        show_annee_range = False, show_count = False, remove_not_chosen = True):
    '''
    Sélectionne par l'utilisateur des libellés pouvant être rattaché au grade
    choisi par la fonction select_grade_neg.

    Arguments
    ---------
    grade_quadruplet : tuple (versant, date_debut_grade, date_fin_grade, libelle_NETNEH),
        grade de la nomenclature choisi à l'étape précédente
    libemplois : Series, with index = (annee, versant, frequence du libellé emploi slugifié

    Returns
    -------
    libelles_emploi_selectionnes : liste des libellés additionnels pouvant être rattachés au triplet précédent
    next_libelle : bool, passage au libelle suivant
    '''
    assert grade_quadruplet is not None  # (versant, grade, date_debut_grade, date_fin_grade,)
    assert libemplois is not None
    libelles_emploi_selectionnes = list()
    libelles_emploi_non_selectionnes = list()
    versant, grade, date_debut_grade, date_fin_grade = grade_quadruplet
    annee_debut_grade = datetime.strptime(date_debut_grade, '%Y-%m-%d').year
    annee_fin_grade = datetime.strptime(date_fin_grade, '%Y-%m-%d').year

    # When slicing a pandas index, both the start bound AND the stop bound are included
    libemplois.name = 'frequence'
    libelles = libemplois.loc[
        annee_debut_grade:annee_fin_grade, versant].reset_index()['libemploi_slugified'].tolist()
    libelles_init = libemplois.loc[
        annee_debut_grade:annee_fin_grade, versant].reset_index()['libemploi_slugified'].tolist()

    libelles_emploi_deja_renseignes_dataframe = get_correspondance_data_frame(which = 'grade', netneh = True)
    libelles_emploi_deja_renseignes = (libelles_emploi_deja_renseignes_dataframe
        .query("(date_fin_grade == @date_fin_grade) & (date_debut_grade == @date_debut_grade) &  (versant == @versant)")
        ).libelle.tolist()
    #
    libelles_purges = list(
        set(libelles_init).difference(libelles_emploi_deja_renseignes)
        )
    #
    assert set(libelles_purges) <= set(libelles), "Libellés purgés invalides {}".format(
        set(libelles_purges).difference(set(libelles))
        )

    libelles = libelles_purges
    next_libelle = False
    last_min_score = 100

    while True:
        if libelles_emploi_selectionnes:
            print("libellés emploi sélectionnés:")
            pprint.pprint(libelles_emploi_selectionnes)
            libelles = [libemploi for libemploi in libelles if libemploi not in libelles_emploi_selectionnes]

        if libelles_emploi_non_selectionnes and remove_not_chosen:
            libelles = [libemploi for libemploi in libelles if libemploi not in libelles_emploi_non_selectionnes]

        libelles_emploi_additionnels = query_libelles_emploi(
            query = grade,
            choices = libelles,
            last_min_score = last_min_score,
            )

        libelles_emploi_additionnels = (libelles_emploi_additionnels
            .merge(
                libemplois
                    .reset_index()
                    .query('versant == @versant')
                    .drop(['versant'], axis = 1)
                    .rename(columns = dict(libemploi_slugified = 'libelle_emploi')),
                how = 'inner',
                )
            .groupby(['libelle_emploi', 'score']).agg(
                dict(
                    annee = ['min', 'max'],
                    frequence = ['sum'],
                    )
                )
            .reset_index()
            .sort_values(['score', ('frequence', 'sum')], ascending = False)
            .reset_index()
            )

        printed_columns = ['libelle_emploi', 'score']

        show_count = True
        show_annee_range = True
        if show_count:
            printed_columns.append('frequence')
        if show_annee_range:
            printed_columns.append('annee')

        print("\nAutres libellés emploi possibles:\n{}".format(libelles_emploi_additionnels[printed_columns]))
        selection = raw_input("""
liste de nombre (ex: 1:4,6,8,10:11), o (tous), n (aucun), r (recommencer selection),
q (quitter/libelle suivant), s (sauvegarde et stats)

selection: """)

        if any((c in [str(i) for i in range(0, 10)]) for c in selection):
            if any((c not in [str(i) for i in '0123456789,:']) for c in selection):
                print('Plage de valeurs incorrecte.')
                continue
            problem = False
            for s in selection.split(","):
                if ":" in s:
                    if s.split(":")[0] == "" or s.split(":")[1] == "":
                        problem = True
                        break
                    start = int(s.split(":")[0])
                    stop = int(s.split(":")[1])
                else:
                    start = stop = int(s)

                if not (
                    libelles_emploi_additionnels.index[0] <=
                    start <=
                    stop <=
                    libelles_emploi_additionnels.index[-1:]
                        ):
                    problem = True
                    break

            if problem:
                print('Plage de valeurs incorrecte.')
                continue

            for s in selection.split(","):
                if ":" in s:
                    start = int(s.split(":")[0])
                    stop = int(s.split(":")[1])
                else:
                    start = stop = int(s)
                libelles_emploi_selectionnes += libelles_emploi_additionnels.loc[
                    start:stop, 'libelle_emploi'].tolist()
            diff = set(libelles_emploi_additionnels.libelle_emploi.tolist()) - set(libelles_emploi_selectionnes)
            libelles_emploi_non_selectionnes += list(diff)
            continue

        elif selection == 'o':
            libelles_emploi_selectionnes += libelles_emploi_additionnels.libelle_emploi.tolist()
            continue

        elif selection == 'n':
            libelles_emploi_non_selectionnes += libelles_emploi_additionnels.libelle_emploi.tolist()
            last_min_score = libelles_emploi_additionnels.score.min()
            log.debug('last_min_score = {}'.format(last_min_score))
            continue

        elif selection == 's':
            break

        elif selection == 'r':
            last_min_score = 100
            libelles = libelles_init
            libelles_emploi_selectionnes = list()
            continue

        elif selection == 'q':
            next_libelle = True
            break

        else:
            print('Non valide')
            continue

    return libelles_emploi_selectionnes, next_libelle


def select_libelles_emploi_from_grade_triplet(grade_triplet = None, libemplois = None, annee = None, versant = None,
        show_annee_range = False, show_count = False, remove_not_chosen = True):
    '''
    Sélectionne par l'utilisateur des libellés pouvant être rattaché au grade
    choisi par la fonction select_grade_neg.

    Arguments
    ---------
    grade_triplet : tuple (versant, annee, grade), grade de la nomenclature choisi à l'étape précédente
    libemplois :  list, libellés classés par versant, annee, frequence

    Returns
    -------
    libelles_emploi_selectionnes : liste des libellés additionnels pouvant être rattachés au triplet précédent
    next_libelle : bool, passage au libelle suivant
    '''
    assert grade_triplet is not None  # (versant, libelle_grade, date_effet_grille)
    assert annee is not None
    assert libemplois is not None
    assert versant is not None
    libelles_emploi_selectionnes = list()
    libelles_emploi_non_selectionnes = list()
    libelles = libemplois.loc[annee, versant].index.tolist()
    libelles_init = libemplois.loc[annee, versant].index.tolist()
    annee_cible = annee
    libelles_emploi_deja_renseignes_dataframe = get_correspondance_data_frame(which = 'grade')
    libelles_emploi_deja_renseignes = (libelles_emploi_deja_renseignes_dataframe
        .loc[pd.to_datetime(
            libelles_emploi_deja_renseignes_dataframe.date_effet
            ).dt.year <= annee_cible]
        .query("(annee >= @annee_cible) &  (versant == @versant)")
        ).libelle.tolist()
    #
    libelles_purges = (libemplois
        .loc[annee_cible, versant]
        .loc[~libemplois.loc[annee_cible, versant].index.isin(libelles_emploi_deja_renseignes)]
        )
    #
    assert set(libelles_purges.index.tolist()) < set(libelles)

    libelles = libelles_purges.index.tolist()
    next_libelle = False
    last_min_score = 100

    while True:
        if libelles_emploi_selectionnes:
            print("libellés emploi sélectionnés:")
            pprint.pprint(libelles_emploi_selectionnes)
            libelles = [libemploi for libemploi in libelles if libemploi not in libelles_emploi_selectionnes]

        if libelles_emploi_non_selectionnes and remove_not_chosen:
            libelles = [libemploi for libemploi in libelles if libemploi not in libelles_emploi_non_selectionnes]

        libelles_emploi_additionnels = query_libelles_emploi(
            query = grade_triplet[1],
            choices = libelles,
            last_min_score = last_min_score,
            )

        libelles_emploi_additionnels = (libelles_emploi_additionnels
            .merge(
                libemplois
                    .reset_index()
                    .query('versant == @versant')
                    .drop(['versant'], axis = 1)
                    .rename(columns = dict(libemploi_slugified = 'libelle_emploi')),
                how = 'inner')
            .groupby(['libelle_emploi', 'score']).agg(
                dict(
                    annee = dict(min = np.min, max = np.max),
                    count = dict(freq = np.sum),
                    )
                )
            .reset_index()
            )

        printed_columns = ['libelle_emploi', 'score']

        if show_count:
            printed_columns.append('count')
        if show_annee_range:
            printed_columns.append('annee')

        print("\nAutres libellés emploi possibles:\n{}".format(libelles_emploi_additionnels[printed_columns]))
        selection = raw_input("""
liste de nombre (ex: 1:4,6,8,10:11), o (tous), n (aucun), r (recommencer selection),
q (quitter/libelle suivant), s (sauvegarde et stats)

selection: """)

        if any((c in [str(i) for i in range(0, 10)]) for c in selection):
            if any((c not in [str(i) for i in '0123456789,:']) for c in selection):
                print('Plage de valeurs incorrecte.')
                continue
            problem = False
            for s in selection.split(","):
                if ":" in s:
                    if s.split(":")[0] == "" or s.split(":")[1] == "":
                        problem = True
                        break
                    start = int(s.split(":")[0])
                    stop = int(s.split(":")[1])
                else:
                    start = stop = int(s)

                if not (
                    libelles_emploi_additionnels.index[0] <=
                    start <=
                    stop <=
                    libelles_emploi_additionnels.index[-1:]
                        ):
                    problem = True
                    break

            if problem:
                print('Plage de valeurs incorrecte.')
                continue

            for s in selection.split(","):
                if ":" in s:
                    start = int(s.split(":")[0])
                    stop = int(s.split(":")[1])
                else:
                    start = stop = int(s)
                libelles_emploi_selectionnes += libelles_emploi_additionnels.loc[
                    start:stop, 'libelle_emploi'].tolist()
            diff = set(libelles_emploi_additionnels.libelle_emploi.tolist()) - set(libelles_emploi_selectionnes)
            libelles_emploi_non_selectionnes += list(diff)
            continue

        elif selection == 'o':
            libelles_emploi_selectionnes += libelles_emploi_additionnels.libelle_emploi.tolist()
            continue

        elif selection == 'n':
            libelles_emploi_non_selectionnes += libelles_emploi_additionnels.libelle_emploi.tolist()
            last_min_score = libelles_emploi_additionnels.score.min()
            continue

        elif selection == 's':
            break

        elif selection == 'r':
            last_min_score = 100
            libelles = libelles_init
            libelles_emploi_selectionnes = list()
            continue

        elif selection == 'q':
            next_libelle = True
            break

        else:
            print('Non valide')
            continue

    return libelles_emploi_selectionnes, next_libelle


def store_libelles_emploi(libelles_emploi = None, annee = None, grade_triplet = None, grade_quadruplet = None,
        libemplois = None, new_table_name = None, print_summary = True):
    '''
    Enregistre des libellés attribués à un triplet (grade, versant, date d'effet)
    dans la table de correspondance.

    Parameters
    ----------
    libelles_emploi : list, liste des libellés classés à enregistrer
    annee : année
    grade_triplet : tuple, (versant, grade, date) assigné aux libellés à enregistrer
    grade_quadruplet : tuple (versant, date_debut_grade, date_fin_grade, libelle_NETNEH) assigné aux libellés
        à enregistrer
    libemplois: list, libellés  (pour le count de la proportion de libellés classés)
    '''
    assert libelles_emploi, 'libelles_emploi is None or empty'
    assert isinstance(libelles_emploi, list)

    assert (grade_triplet is not None) ^ (grade_quadruplet is not None)  # ^ = xor
    assert libemplois is not None or not print_summary

    if grade_triplet:
        assert grade_triplet is not None and annee is not None
        versant, grade, date_effet = grade_triplet
        correspondance_data_frame = get_correspondance_data_frame(which = 'grade')
        for libelle in libelles_emploi:
            correspondance_data_frame = correspondance_data_frame.append(pd.DataFrame(
                data = [[versant, grade, date_effet, annee, libelle]],
                columns = ['versant', 'grade', 'date_effet', 'annee', 'libelle']
                ))

        print("Libellés renseignés pour le grade {}:".format(grade))
        if not correspondance_data_frame.empty:
            pprint.pprint(
                correspondance_data_frame.set_index(
                    ['versant', 'grade', 'date_effet', 'annee']
                    )
                .loc[versant, grade, date_effet, annee]
                )

    if grade_quadruplet:
        netneh = True
        versant, grade, date_debut_grade, date_fin_grade = grade_quadruplet
        correspondance_data_frame = get_correspondance_data_frame(which = 'grade', netneh = True)
        for libelle in libelles_emploi:
            correspondance_data_frame = correspondance_data_frame.append(pd.DataFrame(
                data = [[versant, grade, date_debut_grade, date_fin_grade, libelle]],
                columns = ['versant', 'grade', 'date_debut_grade', 'date_fin_grade', 'libelle']
                ))

        print("Libellés renseignés pour le grade {}:".format(grade))
        if not correspondance_data_frame.empty:
            pprint.pprint(correspondance_data_frame
                .set_index(['versant', 'grade', 'date_debut_grade', 'date_fin_grade'])
                .loc[(versant, grade, date_debut_grade, date_fin_grade), 'libelle']
                .sort_values()
                )

    log.info('Writing correspondance_data_frame to {}'.format(correspondance_data_frame_path))
    correspondance_data_frame.to_hdf(
        correspondance_data_frame_path, 'correspondance', format = 'table', data_columns = True
        )

    if print_summary:
        print_stats(
            libemplois = libemplois,
            annee = annee,
            versant = versant,
            netneh = True
            )


def print_stats(libemplois = None, annee = None, versant = None, netneh = False):
    libemplois.name = 'count'
    if netneh:
        correspondance_data_frame = get_correspondance_data_frame(which = 'grade', netneh = True)[
            ['versant', 'grade', 'date_debut_grade', 'date_fin_grade', 'libelle']
            ].rename(
                columns = dict(libelle = 'libemploi_slugified')
                ).copy()

        merged_libemplois = (libemplois
            .reset_index()
            .query("libemploi_slugified != ''")  # On ne garde pas les libellés vides
            .merge(
                correspondance_data_frame,
                on = ['versant', 'libemploi_slugified'],
                )
            )
        merged_libemplois['annee_debut_grade'] = pd.to_datetime(merged_libemplois.date_debut_grade).dt.year
        merged_libemplois['annee_fin_grade'] = pd.to_datetime(merged_libemplois.date_fin_grade).dt.year

        libelles_emploi_deja_renseignes = (merged_libemplois
            .query('annee_debut_grade <= annee <= annee_fin_grade')
            .drop(['annee_debut_grade', 'annee_fin_grade'], axis = 1)
            .drop_duplicates()
            )

    else:
        correspondance_data_frame = get_correspondance_data_frame(which = 'grade')[
            ['versant', 'annee', 'date_effet', 'libelle']
            ].rename(
                columns = dict(annee = 'annee_stop', libelle = 'libemploi_slugified')
                ).copy()
        correspondance_data_frame['annee_start'] = pd.to_datetime(
            correspondance_data_frame.date_effet
            ).dt.year
        del correspondance_data_frame['date_effet']

        merged_libemplois = (libemplois
            .reset_index()
            .query("libemploi_slugified != ''")  # On ne garde pas les libellés vides
            .merge(
                correspondance_data_frame,
                )
            )

        if annee:
            libelles_emploi_deja_renseignes = (merged_libemplois
                .query('annee_start <= annee <= annee_stop')
                .drop(['annee_start', 'annee_stop'], axis = 1)
                )
        else:
            libelles_emploi_deja_renseignes = merged_libemplois

        libelles_emploi_deja_renseignes = libelles_emploi_deja_renseignes.drop_duplicates()

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


def get_libelle_to_classify(libemplois = None, annee_cible = None, ignored_libelles = None):
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
    if annee_cible is None:
        annee_cible = max(annees)

    result = dict()
    for versant in VERSANTS:
        libelles_emploi_deja_renseignes = (libelles_emploi_deja_renseignes_dataframe
            .loc[pd.to_datetime(
                libelles_emploi_deja_renseignes_dataframe.date_effet
                ).dt.year <= annee_cible]
            .query("(annee >= @annee_cible) &  (versant == @versant)")
            ).libelle.tolist()

        libelles_emploi_ignores = (ignored_libelles
            .query("(annee == @annee_cible) &  (versant == @versant)")
            .libelle.tolist()
            )

        excluded_libelles = libelles_emploi_deja_renseignes + libelles_emploi_ignores

        result[versant] = (libemplois
            .loc[annee_cible, versant]
            .loc[~libemplois.loc[annee_cible, versant].index.isin(excluded_libelles)]
            ).head(1)

    if result['T'].empty and result['H'].empty:
        return

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
        annee = annee_cible,
        versant = versant
        )

    return versant, annee_cible, libelle


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


def select_grade_neg_from_libelle(libelle_emploi = None, annee = None, versant = None, libemplois = None):
    grade_triplet = select_grade_neg(
        libelle_saisi = libelle_emploi,
        annee = annee,
        versant = versant,
        )
    if grade_triplet == 'quit':
        return 'quit'

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

    return grade_triplet


def select_libelle_from_grade_neg(grade_triplet = None, annee = None, versant = None, libemplois = None):
    while True:
        libelles_emploi_selectionnes, next_libelle = select_libelles_emploi(
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
        if next_libelle:
            return 'next_libelle'


def validate_correspondance(correspondance_data_frame, check_only = False, netneh = False):
    valid_data_frame = True
    if correspondance_data_frame.duplicated().any():
        print("The are {} duplicated lines".format(correspondance_data_frame.duplicated().sum()))
        log.info("Cleaning duplicated data")
        correspondance_data_frame_cleaned = correspondance_data_frame.drop_duplicates()
        valid_data_frame = False
        if check_only:
            return False
    else:
        correspondance_data_frame_cleaned = correspondance_data_frame

    if netneh:
        print 'NETNEH'
        counts = correspondance_data_frame_cleaned.groupby(
            ['versant', 'grade', 'date_debut_grade', 'date_fin_grade', 'libelle',]
            ).count()
        print counts
        log.info('TODO: Complete validaion')  # TODO FIXME
        return True  # REMOVE ME
    else:
        counts = correspondance_data_frame_cleaned.groupby(['versant', 'annee', 'libelle']).count()
        if counts.max().values.tolist() != [1, 1]:
            if check_only:
                return False
            valid_data_frame = False
            erroneous_entry = counts.query('grade > 1 or date_effet > 1').index.tolist()
            correct_entry = counts.query('grade == 1 and date_effet == 1').index.tolist()
            correspondance_data_frame_cleaned = (correspondance_data_frame_cleaned
                .set_index(['versant', 'annee', 'libelle'])
                .ix[correct_entry]
                .reset_index()
                )
            for libelle in erroneous_entry:
                log.info("CLEANING duplicated neg")
                grade_triplet = select_grade_neg(
                    versant = libelle[0], annee = libelle[1], libelle_saisi = libelle[2]
                    )
                if grade_triplet == "quit":
                    print("Le libelle {} n'est pas reclassé".format(libelle[2]))
                    continue
                else:
                    correspondance_data_frame_cleaned = correspondance_data_frame_cleaned.append(pd.DataFrame(
                        data = [[grade_triplet[0], grade_triplet[1], grade_triplet[2], libelle[1], libelle[2]]],
                        columns = ['versant', 'grade', 'date_effet', 'annee', 'libelle']
                        ))

    if check_only:
        return True
    return valid_data_frame, correspondance_data_frame_cleaned


def wrap_get_libelle_to_classify(libemplois = None, annee_cible = None, ignored_libelles = None):
    while True:
        # 1. Choice of the libelle to be matched
        versant, annee, libelle_emploi = get_libelle_to_classify(
            libemplois = libemplois,
            annee_cible = annee_cible,
            ignored_libelles = ignored_libelles,
            )

        if libelle_emploi == "":
            log.info("On ignore les libelle_emploi vides")
            continue

        print("""
annee: {}
versant: {}
libelle emploi: {}
""".format(annee, versant, libelle_emploi))
        keep = raw_input("""
Voulez-vous classer ce libelle? o : oui. n : non.
selection: """)
        if keep == "n":
            ignored_libelles = ignored_libelles.append(
                pd.DataFrame(
                    [[versant, annee, libelle_emploi]],
                    columns = ['versant', 'annee', 'libelle']
                    )
                )
            continue
        else:
            return versant, annee, libelle_emploi, ignored_libelles


def validate_and_save(correspondance_data_frame_path, netneh = False):
    """
    Validate correspondance table before exiting
    """
    correspondance_data_frame = pd.read_hdf(correspondance_data_frame_path, 'correspondance')
    valid_data_frame = False
    while not valid_data_frame:
        log.info('Validating correspondance data frame')
        valid_data_frame, correspondance_data_frame = validate_correspondance(
            correspondance_data_frame, netneh = netneh)

    log.info('Writing correspondance_data_frame to {}'.format(correspondance_data_frame_path))
    correspondance_data_frame.to_hdf(
        correspondance_data_frame_path, 'correspondance', format = 'table', data_columns = True
        )


def main():
    # Loading the dataframe of slugified libelles (from extract_libelle).
    # (replace load_libelles in the previous version)
    libemploi_h5 = os.path.join(libelles_emploi_directory, 'libemploi.h5')
    libemplois = pd.read_hdf(libemploi_h5, 'libemploi')
    ignored_libelles = pd.DataFrame(columns= ['versant', 'annee', 'libelle'])
    annee_cible = None
    while True:
        versant, annee, libelle_emploi, ignored_libelles = wrap_get_libelle_to_classify(
            libemplois = libemplois,
            annee_cible = annee_cible,
            ignored_libelles = ignored_libelles,
            )

        grade_triplet = select_grade_neg_from_libelle(
            libelle_emploi = libelle_emploi,
            annee = annee,
            versant = versant,
            libemplois = libemplois,
            )

        if grade_triplet == 'continue':
            continue

        elif grade_triplet == 'quit':
            what_next = 'quit'

        else:
            what_next = select_libelle_from_grade_neg(
                grade_triplet = grade_triplet,
                annee = annee,
                versant = versant,
                libemplois = libemplois,
                )

            if what_next == 'next_libelle':
                continue

        if what_next == 'quit':
            while True:
                selection = raw_input("""
    o: passage à l'année suivante. q : quitter
    selection: """)
                if selection == "o":
                    annee_cible = annee - 1
                    break
                if selection == "q":
                    validate_and_save(correspondance_data_frame_path)
                    return
                else:
                    continue


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    main()
