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


@timing
def merge_libelles_emploi_data(debug = True, decennie):

    libemploi_h5 = os.path.join(libelles_emploi_tmp_directory, 'libemploi_{}.h5')
    list_decennie = [1950, 1970]
    for decennie in list_decennie:
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
