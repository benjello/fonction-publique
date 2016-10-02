# -*- coding:utf-8 -*-


from __future__ import division


import pandas as pd


from fonction_publique.base import get_careers


def build_transitions_pct_by_echantillon(decennie = 1970):
    """Compute the distribution of the number of transitions"""
    carrieres = get_careers(variable = 'c_netneh', decennie = decennie).sort_values(['ident', 'annee'])

    def get_transitions(carrieres, normalize = True):
        transitions = pd.DataFrame()
        selection = carrieres.c_netneh.shift().notnull() & (carrieres.ident == carrieres.shift().ident)
        transitions['ident'] = carrieres.ident[selection]
        transitions['transition'] = (carrieres.c_netneh != carrieres.c_netneh.shift())[selection]
        return transitions.groupby('ident').sum().astype(int).squeeze().value_counts(normalize = normalize)

    return pd.concat(dict(
        annees_2010_2014 = get_transitions(carrieres),
        annees_2011_2014 = get_transitions(carrieres[carrieres.annee != 2010]),
        annees_2010_2014_purgees = get_transitions(clean_empty_netneh(carrieres)),  # 110 transitions,
        annees_2011_2014_purgees = get_transitions(clean_empty_netneh(carrieres.query('annee != 2010'))),  # 390701
        )).reset_index().rename(
            columns = {
                'level_0': 'echantillon',
                'level_1': 'transitions',
                'transition': 'population',
                }
            ).sort_values(['echantillon', 'transitions'])


def build_transitions_pct_by_grade_initial(decennie = 1970):
    """Compute the distribution of the number of transitions condtionnal of the first grade"""
    carrieres = get_careers(variable = 'c_netneh', decennie = decennie).sort_values(['ident', 'annee'])

    def get_transitions_grade_init(carrieres):
        df = pd.DataFrame()
        selection = carrieres.c_netneh.shift().notnull() & (carrieres.ident == carrieres.shift().ident)
        df['ident'] = carrieres.ident[selection]
        premiere_annee = carrieres.annee.min()  # analysis:ignore

        premier_grade = carrieres.query('annee == @premiere_annee')[['ident', 'c_netneh']]
        df['transition'] = (carrieres.c_netneh != carrieres.c_netneh.shift())[selection]
        transitions = (df
            .merge(premier_grade, on = 'ident', how = 'left')
            .groupby(['ident', 'c_netneh'])['transition']
            .sum()
            .astype(int)
            .reset_index()
            )
        result = pd.DataFrame()
        result['population'] = (transitions
            .groupby('c_netneh')['transition']
            .value_counts()
            .sort_values(ascending = False)
            .cumsum()
            )
        result['cdf'] = result.population / result.population.max()
        return result

    return pd.concat(dict(
        annees_2010_2014 = get_transitions_grade_init(carrieres),
        annees_2011_2014 = get_transitions_grade_init(carrieres[carrieres.annee != 2010]),
        annees_2010_2014_purgees = get_transitions_grade_init(clean_empty_netneh(carrieres)),
        annees_2011_2014_purgees = get_transitions_grade_init(clean_empty_netneh(carrieres.query('annee != 2010'))),
        ))


def clean_empty_netneh(df):
    df = df.copy()
    df['dummy'] = df.c_netneh == ''
    dummy_by_ident = (df.groupby('ident')['dummy'].sum() == 0).reset_index()
    idents = dummy_by_ident.query('dummy').ident.unique()
    return df[df.ident.isin(idents)].copy()


def get_transitions_dataframe(carrieres):
    transitions = pd.DataFrame()
    selection = carrieres.c_netneh.shift().notnull() & (carrieres.ident == carrieres.shift().ident)
    carrieres['selection'] = selection  # boolean index of the final point
    carrieres
    transitions['ident'] = carrieres.ident[selection]
    transitions['transition'] = (carrieres.c_netneh != carrieres.c_netneh.shift())[selection]
    transitions['initial'] = carrieres.c_netneh[selection.shift(-1).fillna(False)]
    transitions['final'] = carrieres.c_netneh[selection]
    return transitions


def get_destinations_by_grade(carrieres):
    transitions = get_transitions_dataframe(carrieres.sort_values(['ident', 'annee']))
    real_transitions = transitions.query('transition')
    destinations = real_transitions.groupby('initial')['final'].value_counts()
    destinations.name = 'population'
    destinations = destinations.reset_index()
    destinations_by_grade = pd.DataFrame(dict(
        population = destinations.groupby('initial')['population'].agg(sum),
        population_pct = destinations.groupby('initial')['population'].agg(sum) / destinations.population.sum(),
        nombre = destinations.groupby('initial')['population'].count(),
        largest_1_pct = destinations.groupby('initial')['population'].apply(
            lambda x: (x.nlargest(1) / x.sum()).squeeze()
            ),
        largest_2_pct = destinations.groupby('initial')['population'].apply(
            lambda x: (x.nlargest(2) / x.sum()).sum()
            ),
        largest_3_pct = destinations.groupby('initial')['population'].apply(
            lambda x: (x.nlargest(3) / x.sum()).sum()
            ),
        largest_5_pct = destinations.groupby('initial')['population'].apply(
            lambda x: (x.nlargest(5) / x.sum()).sum()
            ),
        )).sort_values('population', ascending = False).reset_index()

    destinations_by_grade['cdf'] = destinations_by_grade.population_pct.cumsum()
    return destinations_by_grade


def build_destinations_by_grade(decennie = None):
    """Compute the distribution of the number of destination grades"""
    carrieres = get_careers(variable = 'c_netneh', decennie = decennie).sort_values(['ident', 'annee'])
    return pd.concat(dict(
        annees_2010_2014 = get_destinations_by_grade(carrieres),
        annees_2011_2014 = get_destinations_by_grade(carrieres[carrieres.annee != 2010]),
        annees_2010_2014_purgees = get_destinations_by_grade(clean_empty_netneh(carrieres)),
        annees_2011_2014_purgees = get_destinations_by_grade(clean_empty_netneh(carrieres.query('annee != 2010'))),
        ))
