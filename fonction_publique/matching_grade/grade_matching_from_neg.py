#!/usr/bin/env python
# -*- coding:utf-8 -*-


from __future__ import division

import logging
import os
import sys

import pandas as pd
from fonction_publique.matching_grade.grade_matching import (
    correspondance_data_frame_path,
    get_grilles_cleaned,
    libelles_emploi_directory,
    query_grade_neg,
    print_stats,
    select_libelle_from_grade_neg,
    validate_and_save,
    VERSANTS,
    )


pd.options.display.max_colwidth = 0
pd.options.display.max_rows = 999

log = logging.getLogger(__name__)


def select_grade_neg_by_hand(versant = None, libelles_grade_NEG = None, grilles = None):  # Rename select_grade_or_corps
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
        print(u"Saisir un libellé NEG à la main:")
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
                    grades_neg = query_grade_neg(
                        query = libelle_saisi, choices = libelles_grade_NEG, score_cutoff = score_cutoff)
                    print("\nGrade NEG possibles pour {} (score_cutoff = {}):\n{}".format(
                        libelle_saisi, score_cutoff, grades_neg))
                    selection2 = raw_input("""
    NOMBRE, plus de choix (n),  quitter (q)
    selection: """)
                    if selection2 == "q":
                        return "quit"
                    elif selection2 == "n":
                        score_cutoff -= 5
                        continue
                    elif selection2.isdigit() and int(selection2) in grades_neg.index:
                        grade_neg = grades_neg.loc[int(selection2), "libelle_grade_neg"]
                        print("Le grade {} a été choisi".format(grade_neg))
                        break
                break

    # TODO: ne pas prendre le min mais toutes les grilles possibles avec ce neg.
    grilles = grilles.loc[
        grilles.libelle_grade_NEG == grade_neg
        ].date_effet_grille.min().strftime('%Y-%m-%d')
    libelle_FP = grilles.loc[grilles.libelle_grade_NEG == grade_neg].libelle_FP.unique().squeeze().tolist()
    # libelle_FP is 'FONCTION PUBLIQUE TERRITORIALE' or 'FONCTION PUBLIQUE HOSPITALIERE' or the list containing both
    if versant == 'H':
        assert libelle_FP == 'FONCTION PUBLIQUE HOSPITALIERE' or 'FONCTION PUBLIQUE HOSPITALIERE' in libelle_FP
    elif versant == 'T':
        assert libelle_FP == 'FONCTION PUBLIQUE TERRITORIALE' or 'FONCTION PUBLIQUE TERRITORIALE' in libelle_FP

    assert versant in VERSANTS, "versant {} is not in {}".format(versant, VERSANTS)
    print("""Le grade NEG suivant a été sélectionné:
 - versant: {}
 - libellé du grade: {}
 - date d'effet la plus ancienne: {}""".format(
        versant,
        grade_neg,
        date_effet_grille,
        ))
    return (versant, grade_neg, date_effet_grille)


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

        annee = 2014
        grilles = get_grilles_cleaned(annee, versant, force_rebuild = True)
        print_stats(libemplois = libemplois, annee = annee, versant = versant)
        libelle_FP = 'FONCTION PUBLIQUE HOSPITALIERE' if versant == 'H' else 'FONCTION PUBLIQUE TERRITORIALE'  # noqa
        libelles_grade_NEG = grilles.query('libelle_FP == @libelle_FP')['libelle_grade_NEG'].unique()
        grade_triplet = select_grade_neg_by_hand(
            versant = versant,
            libelles_grade_NEG = libelles_grade_NEG,
            grilles = grilles
            )

        if grade_triplet == 'quit':
            validate_and_save(correspondance_data_frame_path)
            return 'quit'

#        print("Classer les libellés dans la grille {} ?".format(grade_triplet))
#            new_versant = raw_input("""
#         o: oui, n: non
#        selection: """)

        what_next = select_libelle_from_grade_neg(
            grade_triplet = grade_triplet,
            annee = annee,
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
