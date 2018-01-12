#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_libelle: save a dataframe with all the libellés of all the decennie,
that will be matched in the grade_matching.py script.
"""

import logging
import os
import sys
import pandas as pd


from fonction_publique.base import clean_directory_path, raw_directory_path, asset_path, get_careers, parser, DEFAULT_CHUNKSIZE
from fonction_publique import raw_data_cleaner
from slugify import slugify


libelles_emploi_directory = parser.get('correspondances', 'libelles_emploi_directory')


def load_libelles(data_path = None, debug = False):
    libemploi = get_careers(variable = 'libemploi', data_path = data_path, debug = debug)
    libemploi['libemploi_slugified'] = libemploi.libemploi.apply(slugify, separator = "_")
    statut = get_careers(variable = 'f_coll', data_path = data_path, debug = debug)
    statut['statut'] = statut['f_coll']
    libemploi = (libemploi
        .merge(
            statut.query("statut in ['T', 'H']"),
            how = 'inner',
            )
        )
    libemploi = libemploi[libemploi.libemploi != '']
    return libemploi


def save_subset_libelle(load_path = None, save_path = None):
    load_libelle_file = os.path.join(load_path, "libemploi.h5")
    load_slugified_file = os.path.join(load_path, "correspondance_libemploi_slug.h5")

    libelles_file = pd.read_hdf(load_libelle_file)
    slugified_file = pd.read_hdf(load_slugified_file)

    sub_libemplois = libelles_file.sample(frac=0.05)

    list_sub_libelles = sub_libemplois.index.get_level_values('libemploi_slugified').tolist()
    sub_correspondance = slugified_file.loc[(slugified_file.libemploi_slugified.isin(list_sub_libelles))]

    save_libelle_file = os.path.join(save_path, "libemploi.h5")
    save_slugified_file = os.path.join(save_path, "correspondance_libemploi_slug.h5")

    sub_libemplois.sort_index().to_hdf(save_libelle_file, 'libemploi')
    sub_correspondance.sort_index().to_hdf(save_slugified_file, 'correspondance_libemploi_slug')


def main(clean_data = False, debug = False, ):
    # Etape 1: data_cleaning
    if clean_data:
        raw_data_cleaner.main(
            raw_directory_path = os.path.join(raw_directory_path, "csv"),
            subset_data = ["export2_g1940_1959.csv", "export2_g1960_1969.csv", "export2_g1970_1979.csv", "export2_g1980.csv"],
            subset_var = ["f_coll","libemploi"],
            clean_directory_path = clean_directory_path,
            debug = debug,
            chunksize = DEFAULT_CHUNKSIZE,
            year_min = 2000,
            )
    # Etape 2: extract_libelles and merge
    data_to_extract = ["2_1940_carrieres.h5", "2_1960_carrieres.h5", "2_1970_carrieres.h5", "2_1980_carrieres.h5"]
    for data_path in data_to_extract:
        log.info("Processing data {}".format(data_path))
        libemploi = load_libelles(data_path = data_path, debug = debug)
        if data_path == data_to_extract[0]:
            libemploi_all = libemploi
        else:
            libemploi_all = libemploi_all.append(libemploi)

    # Etape 3: save slugified libelles as libemplois
    libemploi_h5 = os.path.join(libelles_emploi_directory, "libemploi.h5")
    libemploi_all.rename(columns = dict(statut = 'versant'), inplace = True)
    libemplois = libemploi_all.groupby([u'annee', u'versant'])['libemploi_slugified'].value_counts()
    log.info("Generating and saving libellés emploi to {}".format(libemploi_h5))
    libemplois.to_hdf(libemploi_h5, 'libemploi')

    # Etape 4: save corresponding bw slug and normal libemploi
    correspondance_libemploi_slug_h5 = os.path.join(libelles_emploi_directory, "correspondance_libemploi_slug.h5")
    correspondance_libemploi_slug = (libemploi_all[[u'versant', u'libemploi', u'annee', u'libemploi_slugified']]
        .drop_duplicates()
        )
    correspondance_libemploi_slug.to_hdf(correspondance_libemploi_slug_h5, 'correspondance_libemploi_slug')

if __name__ == "__main__":
    sys.exit(main(clean_data = True, debug = False))