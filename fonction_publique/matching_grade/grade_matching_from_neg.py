#!/usr/bin/env python
# -*- coding:utf-8 -*-


from __future__ import division

import logging
import os
import sys
from fonction_publique.base import parser

import pandas as pd
from fonction_publique.matching_grade.grade_matching import (
    get_grilles_cleaned, select_libelle_from_grade_neg, validate_and_save,
    query_grade_neg, print_stats,
    )


pd.options.display.max_colwidth = 0
pd.options.display.max_rows = 999

log = logging.getLogger(__name__)


DEBUG = False
VERSANTS = ['T', 'H']

correspondance_data_frame_path = parser.get('correspondances', 'h5')
corps_correspondance_data_frame_path = parser.get('correspondances', 'corps_h5')
libelles_emploi_directory = parser.get('correspondances', 'libelles_emploi_directory')


def select_grade_neg_by_hand(libelles_grade_NEG = None, grilles = None):  # Rename select_grade_or_corps
    '''
    Parameters
    ----------

    Returns
    -------
    grade_neg : tuple, (versant, grade, date d'effet) du grade correspondant
    '''
    score_cutoff = 95

    while True:
        print("Saisir un libellé NEG à la main:")
        libelle_saisi = raw_input("""
SAISIR UN LIBELLE, quitter (q)
selection: """)
        if libelle_saisi == "q":
            return "quit"
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
                while True:
                    grades_neg = query_grade_neg(query = libelle_saisi, choices = libelles_grade_NEG, score_cutoff = score_cutoff)
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
                        break
                break

    date_effet_grille = grilles.loc[
        grilles.libelle_grade_NEG == grade_neg
        ].date_effet_grille.min().strftime('%Y-%m-%d')
    versant = grilles.loc[grilles.libelle_grade_NEG == grade_neg].libelle_FP.unique().squeeze().tolist()
    versant = 'T' if versant == 'FONCTION PUBLIQUE TERRITORIALE' else 'H'  # TODO: clean this mess

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
    new_year_versant = True
    
    while True:
        if new_year_versant: 
            print("Choix de l'année (date d'effet max)")
            annee = raw_input("""
        SAISIR UNE ANNEE
        selection: """)
            if annee in map(str,range(2000, 2015)):
                print("Annee d'effet de la grille:{}".format(annee))
            else:
                print("Annee saisie incorrect: {}. Choisir une annee entre 2000 et 2014".format(annee))
                continue
        
        
            print("Choix du versant")
            versant = raw_input("""
        SAISIR UN VERSANT (T: territorial, H: hospitaliere)
        selection: """)
            if versant in ["T","H"]:
                print("Versant de la grille:{}".format(versant))
            else:
                print("Versant saisi incorrect: {}. Choisir T ou H".format(versant))
                continue
            
        annee = int(annee)
        grilles = get_grilles_cleaned(annee)
        
        print_stats(libemplois = libemplois, annee = annee, versant = versant)       
        
        libelles_grade_NEG = grilles['libelle_grade_NEG'].unique()

        grade_triplet = select_grade_neg_by_hand(
        libelles_grade_NEG = libelles_grade_NEG, grilles = grilles
        )

        if grade_triplet == 'quit':
            validate_and_save(correspondance_data_frame_path)            
            return 'quit' 
        
        what_next = select_libelle_from_grade_neg(
            grade_triplet = grade_triplet,
            annee = annee,
            versant = versant,
            libemplois = libemplois,
            )

        if what_next == 'next_libelle':
            print("Changement de grade. Changer l'année ({}) et/ou le versant({}) ?".format(annee, versant))
            new_year = raw_input("""
         o: oui, n: non
        selection: """)
            if new_year == "n":
                new_year_versant = False
            continue

        if what_next == 'quit':
            validate_and_save(correspondance_data_frame_path)
            return


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    main()
    
    

