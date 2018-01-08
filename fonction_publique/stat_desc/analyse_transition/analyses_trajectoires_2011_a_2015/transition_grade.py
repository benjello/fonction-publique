# -*- coding: utf-8 -*-

# Filters: individuals at least one time in the corps
from __future__ import division

import os
import pandas as pd
import numpy as np
from fonction_publique.base import raw_directory_path, get_careers, parser
from slugify import slugify
import matplotlib.pyplot as plt

fig_save_path = "C:/Users/l.degalle/CNRACL/fonction-publique/fonction_publique/ecrits/note_1_Lisa/Figures"

libelles_emploi_directory = parser.get('correspondances',
                                       'libelles_emploi_directory')
save_path = 'M:/CNRACL/output'

data_AT = pd.read_csv(
    os.path.join(save_path,"corps_AT_2011_w_echelon_conditions.csv")
    )

ids_full = pd.DataFrame(data_AT.groupby(['ident'])['annee', 'trimestre'].count() == 20).reset_index()
ids_full = ids_full.loc[(ids_full['annee']) & (ids_full['trimestre'])]

data = data_AT.loc[data_AT['ident'].isin(ids_full['ident'])]
data = data.set_index(['ident', 'annee', 'trimestre'])

# Create lags for code neg
data = data.sort_index()
data['lagged_grade'] = data.groupby(level=0)['code_grade_NETNEH'].shift(1); data
data['lagged_echelon'] = data.groupby(level=0)['echelon_y'].shift(1); data
data['lagged_date_effet'] = data_groupby(level=0)['date_]