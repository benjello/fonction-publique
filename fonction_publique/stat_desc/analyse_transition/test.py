# -*- coding: utf-8 -*-

## Test sur corps des techniciens de la FPT

# Filters: individuals at least one time in the corps

import logging
import os
import sys
import pkg_resources
import inspect
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ggplot
from ggplot import *

from fonction_publique.


from fonction_publique.base import raw_directory_path, get_careers, parser
from fonction_publique.merge_careers_and_legislation import get_grilles
from slugify import slugify

load_path = 'M:/CNRACL/output'
save_path = 'U:/Projets/CNRACL/fonction-publique/fonction_publique/ecrits/modelisation_carriere/Figures'


def select_data():
    df =  pd.read_hdf(os.path.join(load_path,"corps1.h5"))
    # Keep only individuals with 75% at least in the corps
    list_neg = ['0793', '0794', '0795', '0796']
    df['ind_neg'] = (df['c_neg'].isin(list_neg)).astype(int)
    df['ind'] = 1
    df["count_obs"] = df.groupby(["ident"])["ind"].transform(sum)
    df["count_neg"] = df.groupby(["ident"])["ind_neg"].transform(sum)
    df["count_dif"] = df["count_obs"] - df["count_neg"]
    # Count nb of changing neg
    df['lagged_neg'] = df.c_neg.shift(1)
    df['first_obs'] = abs(df.duplicated(subset = ['ident'], keep = 'first').astype(int)-1)
    df['last_obs'] = abs(df.duplicated(subset = ['ident'], keep = 'last').astype(int)-1)
    df['change_neg'] = (df['lagged_neg'] != df['c_neg']).astype(int)
    df.change_neg.loc[df.first_obs == 1] = 0
    df["count_change"] =df.groupby(['ident'])[["change_neg"]].transform(sum)
    # Double filters: only same corps and 2 or 3 change
    filtered_df = df.loc[(df.count_dif == 0) & (df.count_change  > 1) & (df.count_change  < 4)]
    filtered_df =filtered_df[['ident', 'annee', 'libemploi', 'c_neg', 'change_neg', 'ib', 'echelon']]

    return filtered_df

def plot_career(libemploi):

    plt.axis([0, 10, 0, 1])
    plt.ion()

for i in range(20):
    y = np.random.random()
    plt.scatter(i, y)
    plt.pause(0.05)

filtered_df = filtered_df.sort(['ident', 'annee'])
ident = filtered_df['ident'].unique()
df_slice = filtered_df.loc[filtered_df['ident']<ident[100]][['ident', 'annee', 'libemploi', 'c_neg', 'change_neg', 'ib', 'echelon']]
df_slice['name'] = ''
p =  ggplot(df_slice, aes('annee', y='ib'))
p = p +\
geom_line() +\
scale_x_discrete(name = 'Annee', labels = (2007, 2015),  breaks = (2007, 2015))   +\
scale_y_discrete(name = 'Indice', limits = (300, 500), breaks = (300, 500))   +\
theme_bw() +\
facet_wrap("ident", nrow = 10, ncol = 10, )

p.save(filename = os.path.join(save_path,'facet_indices.pdf'))


    df_slice

  geom_point(aes(y = 'point'))




meat_lng = pd.melt(meat, id_vars=['date'])

p = ggplot(aes(x='annee', y='ib'), data=meat_lng)
p + geom_point() + \
    facet_wrap("variable",)



p + geom_hist() + facet_wrap("color")

p = ggplot(diamonds, aes(x='price'))
p + geom_density() + \
    facet_grid("cut", "clarity")

p = ggplot(diamonds, aes(x='carat', y='price'))
p + geom_point(alpha=0.25) + \
    facet_grid("cut", "clarity")

diamonds.hea



        ggplot(df_slice, aes(x='annee', y='ib')) + geom_point() +\
    geom_point(data=df_slice, aes_string(x='annee', y = 'point'))

    plot =   ggplot(aes('age'), data = df_slice) + geom_density())
p.append(ggplot(aes('age'), data = df_slice) + geom_density())
p



ggplot(mtcars, aes(x='wt', y='mpg')) +\
    geom_point() +\


while True:
    plt.pause(0.05)

    libemploi['libemploi_slugified'] = libemploi.libemploi.apply(slugify, separator = "_")
    libemploi_corps = ['adjoint_technique_de_2eme_classe', 'adjoint_technique_de_1ere_classe',
                       'adjoint_technique_principal_de_2eme_classe', 'adjoint_technique_principal_de_1ere_classe']
    subset_libemploi = libemploi[libemploi.libemploi_slugified.isin(libemploi_corps)]
    subset_ident = subset_libemploi.ident.unique()
    return subset_ident


def select_grilles():
    path_grilles = os.path.join(
    pkg_resources.get_distribution('fonction_publique').location,
    'fonction_publique',
    'assets',
    'grilles_fonction_publique',
    )
    grilles = pd.read_hdf(os.path.join(path_grilles,"grilles_old.h5"))
    libNEG_corps = ['ADJOINT TECHNIQUE DE 2EME CLASSE', 'ADJOINT TECHNIQUE DE 1ERE CLASSE',
                    'ADJOINT TECHNIQUE PRINCIPAL DE 2EME CLASSE', 'ADJOINT TECHNIQUE PRINCIPAL DE 1ERE CLASSE']
    subset_grilles = grilles[grilles.libelle_grade_NEG.isin(libNEG_corps)]
    return (subset_grilles)


def cleaning_data(dataset):
    # Carrière
    libemploi = load_career('libemploi', dataset)
    c_neg = load_career('c_neg', dataset)
    ib = load_career('ib', dataset)
    echelon = load_career('echelon', dataset)
    # Grilles
    grilles = select_grilles()
    # Indiv avec un lib dans le corps
    list_code = list(set(grilles.code_grade_NEG.astype(str)))
    list_code = ['0' + s for s in list_code]
    subset_ident = list(set(c_neg.ident[c_neg.c_neg.isin(list_code)]))
    # Merge lib + neg + ib
    c_neg_subset = c_neg.loc[c_neg.ident.isin(subset_ident)]
    libemploi_subset = libemploi.loc[libemploi.ident.isin(subset_ident)]
    ib_subset = ib.loc[(ib.trimestre == 1) & (ib.annee > 1999)]
    ib_subset = ib_subset.loc[ib_subset.ident.isin(subset_ident)]
    # Merge
    data = libemploi_subset.merge(c_neg_subset, how = "left", on = ['ident', 'annee'])
    data = data.merge(ib_subset, how = "left", on = ['ident', 'annee'])
    data = data.sort(['ident', 'annee'])
    # Final selection on year and missing lib
    clean_data = data.loc[data.annee > 2006].copy()
    clean_data = clean_data.loc[clean_data.libemploi != ""]

    return clean_data


def main():
    data =  pd.read_hdf(os.path.join(path_grilles,"grilles_old.h5"))

if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    main()
