#!/usr/bin/env python
# -*- coding:utf-8 -*-


from __future__ import division

import logging
import numpy as np
import os
import pandas as pd
import sys


from slugify import slugify
from fuzzywuzzy import process


from fonction_publique.matching_grade.grade_matching import (
    correspondance_data_frame_path,
    get_grilles_cleaned,
    libelles_emploi_directory,
    print_stats,
    validate_and_save,
    VERSANTS,
    )


pd.options.display.max_colwidth = 0
pd.options.display.max_rows = 999

log = logging.getLogger(__name__)


def select_grade_netneh_by_hand(versant = None, libelles_NETNEH = None, grilles = None):  # Rename select_grade_or_corps
    '''
    Parameters
    ----------

    Returns
    -------
    grade_neg : tuple  (versant, grade, date de début, date de fin) définissant une grille sur laquelle sont matchés
    les libellés.
    '''
    assert versant in VERSANTS
    score_cutoff = 95

    while True:
        print(u"Saisir un libellé NETNEH à la main:")
        libelle_saisi = raw_input("""
SAISIR UN LIBELLE, quitter (q)
selection: """)
        if libelle_saisi == "q":
            return "quit"
        else:
            print("Libellé saisi: {}".format(libelle_saisi))
            selection = raw_input("""
LE LIBELLE EST-IL CORRECT ? OUI (o), NON ET RECOMMENCER LA SAISIE (r)
selection: """)
            if selection not in ["o", "r"]:
                print('Plage de valeurs incorrecte (choisir o ou r)')
            elif selection == "r":
                continue
            elif selection == "o":
                while True:
                    grades = query_grade_netneh(
                        query = libelle_saisi, choices = libelles_NETNEH, score_cutoff = score_cutoff)
                    print("\nGrade NEG possibles pour {} (score_cutoff = {}):\n{}".format(
                        libelle_saisi, score_cutoff, grades))
                    selection2 = raw_input("""
    NOMBRE, plus de choix (n),  quitter (q)
    selection: """)
                    if selection2 == "q":
                        return "quit"
                    elif selection2 == "n":
                        score_cutoff -= 5
                        continue
                    elif selection2.isdigit() and int(selection2) in grades.index:
                        grade = grades.loc[int(selection2), "libelle_NETNEH"]
                        print("Le grade NETNEH {} a été choisi".format(grade))
                        break
                break

    # TODO: ne pas prendre le min mais toutes les grilles possibles avec ce neg.
    grilles = grilles.loc[
        grilles.libelle_NETNEH == grade,
        ['date_debut_grade', 'date_fin_grade', 'libelle_NETNEH', 'libelle_grade_NEG', 'code_grade_NEG', 'libelle_FP']
        ].drop_duplicates().sort_values('date_debut_grade').reset_index(drop = True)

    if len(grilles) == 1:
        while True:
            print(grilles)
            date_debut_grade = grilles.date_debut_grade.dt.strftime('%Y-%m-%d').unique()[0]
            date_fin_grade = grilles.date_fin_grade.dt.strftime('%Y-%m-%d').unique()[0]
            print date_debut_grade
            print(u"\nIl n'y a qu'un seul grade qui correspond. Ce grade convient-il ? ")
            libelle_saisi = raw_input("""
VALIDER ?, oui (o), quitter (q)
selection: """)
            if libelle_saisi == "q":
                return "quit"
            elif selection == "o":
                break
            else:
                continue
    else:
        while True:
            print("\nGrade  possibles:\n{}".format(
                grilles))
            selection2 = raw_input("""
NOMBRE, quitter (q)
selection: """)
            if selection2 == "q":
                return "quit"
            elif selection2.isdigit() and int(selection2) in grilles.index:
                        grade = grilles.loc[int(selection2), "libelle_NETNEH"]
                        print("Le grade NETNEH {} a été choisi".format(grade))
                        break
            else:
                continue

    libelle_FP = grilles.loc[grilles.libelle_NETNEH == grade].libelle_FP.unique().squeeze().tolist()
    # libelle_FP is 'FONCTION PUBLIQUE TERRITORIALE' or 'FONCTION PUBLIQUE HOSPITALIERE' or the list containing both
    if versant == 'H':
        assert libelle_FP == 'FONCTION PUBLIQUE HOSPITALIERE' or 'FONCTION PUBLIQUE HOSPITALIERE' in libelle_FP
    elif versant == 'T':
        assert libelle_FP == 'FONCTION PUBLIQUE TERRITORIALE' or 'FONCTION PUBLIQUE TERRITORIALE' in libelle_FP

    assert versant in VERSANTS, "versant {} is not in {}".format(versant, VERSANTS)
    print("""Le grade NEG suivant a été sélectionné:
 - versant: {}
 - libellé du grade: {}
 - date de debut du grade: {}
 - date de fin du grade: {}""".format(
        versant,
        grade,
        date_debut_grade,
        date_fin_grade,
        ))
    return (versant, grade, date_debut_grade, date_fin_grade,)


def query_grade_netneh(query = None, choices = None, score_cutoff = 95):
    '''
    A partir de libelés observés, va chercher les 50 libellés les plus proches dans
    la liste des libellés officiels des grades. En l'absence de résultats, on abaisse le seuil.


    Arguments:
        - Libéllé à classer
        - Liste possible des libellés de grade "officiels" NETNEH
        - Score
    Sortie:
        - Liste de grade correspondants avec les score de matching associés.
    '''
    # TODO consolidate with query_grade_neg
    assert query is not None
    assert choices is not None
    slugified_choices = [slugify(choice, separator = '_') if (choice is not np.nan) else '' for choice in choices]
    results = process.extractBests(query, slugified_choices, score_cutoff = score_cutoff, limit = 50)
    if results:
        choice_by_slug = dict(zip(slugified_choices, choices))
        data_frame = pd.DataFrame.from_records(results, columns = ['slug_libelle', 'score'])
        data_frame['libelle_NETNEH'] = data_frame.slug_libelle.map(choice_by_slug)
        return data_frame
    else:
        return query_grade_netneh(query, choices = choices, score_cutoff = score_cutoff - 5)


def select_libelle_from_grade_netneh(grade_quadruplet = None, versant = None, libemplois = None):
    while True:
        libelles_emploi_selectionnes, next_libelle = select_libelles_emploi(
            grade_quadruplet = grade_quadruplet,
            libemplois = libemplois,
            versant = versant,
            )

        if libelles_emploi_selectionnes:
            store_libelles_emploi(
                libelles_emploi = libelles_emploi_selectionnes,
                grade_quadruplet = grade_quadruplet,
                libemplois = libemplois,
                )
        if next_libelle:
            return 'next_libelle'



def main():
    libemploi_h5 = os.path.join(libelles_emploi_directory, 'libemploi.h5')
    libemplois = pd.read_hdf(libemploi_h5, 'libemploi')
    change_versant = True

    while True:
        if change_versant:
            print("Choix du versant")
            versant = raw_input(u"""
        SAISIR UN VERSANT (T: territoriale, H: hospitaliere), OU QUITTER (q)
        selection: """)
            if versant in VERSANTS:
                print("Versant de la grille:{}".format(versant))
            elif versant == "q":
                print("Quitting matching")
                return
            else:
                print("Versant saisi incorrect: {}. Choisir T ou H (ou q)".format(versant))
                continue

        # annee = 2014
        subset = [
            'code_grade_NEG',
            'date_debut_grade',
            'date_fin_grade',
            'libelle_FP',
            'libelle_grade_NEG',
            'libelle_NETNEH',
            ]
        grilles = get_grilles_cleaned(versant = versant, force_rebuild = False, subset = subset)
        print_stats(libemplois = libemplois, versant = versant)
        libelle_FP = 'FONCTION PUBLIQUE HOSPITALIERE' if versant == 'H' else 'FONCTION PUBLIQUE TERRITORIALE'  # noqa
        libelles_NETNEH = grilles.query('libelle_FP == @libelle_FP')['libelle_NETNEH'].unique()
        grade_quadruplet = select_grade_netneh_by_hand(
            versant = versant,
            libelles_NETNEH = libelles_NETNEH,
            grilles = grilles
            )

        if grade_quadruplet == 'quit':
            validate_and_save(correspondance_data_frame_path)
            return 'quit'

#        print("Classer les libellés dans la grille {} ?".format(grade_triplet))
#            new_versant = raw_input("""
#         o: oui, n: non
#        selection: """)

        what_next = select_libelle_from_grade_netneh(
            grade_quadruplet = grade_quadruplet,
            versant = versant,
            libemplois = libemplois,
            )

        if what_next == 'next_libelle':
            print("Changement de grade. Changer le versant({}) ?".format(versant))
            new_versant = raw_input("""
         o: oui, n: non
        selection: """)
            if new_versant == "n":
                change_versant = False
            continue

        if what_next == 'quit':
            validate_and_save(correspondance_data_frame_path)
            return


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    main()
