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

data_AT_echelon_2011_T1 = data_AT.query(
        '(annee == 2011) & (trimestre == 1)'
        )[['ident', 'echelon_y']]
data_AT_without_1st_transition = data_AT[
        ~data_AT['ident'].isin(data_AT_echelon_2011_T1['ident'].tolist()) &
                data_AT['echelon_y'].isin(
                        data_AT_echelon_2011_T1['echelon_y'].tolist()
                        )]

#############################################################################
#              I. DISPERSION DES DUREES PASSEES DANS L'ECHELON              #
#############################################################################
data_AT = data_AT_without_1st_transition

list_min =  [24, 20, 30, 36, 18, 12, 40]
list_min.sort()


fig = plt.figure(figsize=(18, 18), dpi=100, facecolor='w', edgecolor='k')
for i in range(len(list_min)):
    min_mois = list_min[i]
    data_AT_min_mois = data_AT.query('min_mois == {}'.format(min_mois))
    count_trimestre = data_AT_min_mois.groupby(
        ['ident', 'echelon_y']
        )['trimestre'].count().reset_index()
    count_trimestre = count_trimestre.rename(
        columns = {'trimestre':'n_trimestres'}
        )
    count_trimestre['n_mois'] = count_trimestre['n_trimestres'] * 3
    #    ax = plt.subplot2grid((4,4),(0, 0))
    fig.subplots_adjust(hspace=1.5)
    plt.subplot(7, 1, i+1)
    plt.tight_layout
    plt.hist(count_trimestre['n_mois'], histtype='bar', rwidth=1, bins=range(
        int(min(count_trimestre['n_mois'])),
        int(max(count_trimestre['n_mois'])) + 1, 1),
        )
    plt.title("Minimum: {} mois".format(min_mois))
    plt.xticks(range(0, 60, 2), rotation=90)
    print min_mois
    print count_trimestre['n_mois'].value_counts()

plt.savefig(
    os.path.join(fig_save_path, 'graph_disp_min_duree_echelon.png'),
    bbox_inches='tight'
    )


list_max = [36, 24, 48, 12]
list_max.sort()

fig = plt.figure(figsize=(18, 18), dpi=100, facecolor='w', edgecolor='k')
for i in range(len(list_max)):
    max_mois = list_max[i]
    data_AT_max_mois = data_AT.query('max_mois == {}'.format(max_mois))
    count_trimestre = data_AT_max_mois.groupby(
        ['ident', 'echelon_y']
        )['trimestre'].count().reset_index()
    count_trimestre = count_trimestre.rename(
        columns = {'trimestre':'n_trimestres'}
        )
    count_trimestre['n_mois'] = count_trimestre['n_trimestres'] * 3
#    ax = plt.subplot2grid((4,4),(0, 0))
    fig.subplots_adjust(hspace=1.5)
    plt.subplot(7, 1, i+1)
    plt.tight_layout
    plt.hist(count_trimestre['n_mois'], histtype='bar', rwidth=1, bins=range(
        int(min(count_trimestre['n_mois'])),
        int(max(count_trimestre['n_mois'])) + 1, 1),
        )
    plt.title("Maximum: {} mois".format(max_mois))
    plt.xticks(range(0, 60, 2), rotation=90)
    print min_mois
    print count_trimestre['n_mois'].value_counts()

plt.savefig(
        os.path.join(fig_save_path, 'graph_disp_max_duree_echelon.png'),
        bbox_inches='tight'
        )

# Plot par min et max
data_min_max = data_AT.groupby(
        ['min_mois', 'max_mois']
        ).count().reset_index()[['min_mois', 'max_mois']]

fig = plt.figure(figsize=(18, 18), dpi=100, facecolor='w', edgecolor='k')
for i in range(len(data_min_max)):
    data = data_min_max.iloc[i]
    min_mois = data[0]
    max_mois = data[1]
    data = data_AT.query(
            '(min_mois == {}) & (max_mois == {})'.format(min_mois, max_mois)
            )
    count_trimestre = data.groupby(
        ['ident', 'echelon_y']
        )['trimestre'].count().reset_index()
    count_trimestre = count_trimestre.rename(
        columns = {'trimestre':'n_trimestres'}
        )
    count_trimestre['n_mois'] = count_trimestre['n_trimestres'] * 3
#    ax = plt.subplot2grid((4,4),(0, 0))
    fig.subplots_adjust(hspace=1.5)
    plt.subplot(3, 1, i+1)
    plt.tight_layout
    plt.hist(count_trimestre['n_mois'], histtype='bar', rwidth=1, bins=range(
        int(min(count_trimestre['n_mois'])),
        int(max(count_trimestre['n_mois'])) + 1, 1),
        )
    plt.title("Minimum: {} mois, Maximum: {} mois".format(min_mois, max_mois))
    plt.xticks(range(0, 60, 2), rotation=90)
    print min_mois
    print count_trimestre['n_mois'].value_counts()
plt.savefig(
        os.path.join(fig_save_path, 'graph_disp_min_max_duree_echelon.png'),
        bbox_inches='tight'
        )