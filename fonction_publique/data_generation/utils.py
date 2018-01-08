# -*- coding: utf-8 -*-

import logging
import os
import numpy as np
import pandas as pd


from fonction_publique.base import grilles, output_directory_path


log = logging.getLogger(__name__)


def get_grilles_including_bef_ATT(grilles = grilles):
    grade_NEG_bef_TTH1 = [27, 35, 391, 625, 769]
    grade_NEG_bef_769 = [32, 36, 37]
    grade_NEG_bef_26 = [30]
    grade_NEG_bef_25 = [29]
    grade_NEG_bef_TTH2 = [26, 34, 626]
    grade_NEG_bef_TTH3 = [25, 33, 627]
    grade_NEG_bef_TTH4 = [157, 156, 628]
    grades_NEG_bef_ATT = (
        grade_NEG_bef_TTH1 +
        grade_NEG_bef_TTH2 +
        grade_NEG_bef_TTH3 +
        grade_NEG_bef_TTH4 +
        grade_NEG_bef_769 +
        grade_NEG_bef_26 +
        grade_NEG_bef_25
        )
    grades_NEG_bef_ATT = map(str, grades_NEG_bef_ATT)
    grilles_ATT_bef = grilles.query('code_grade_NEG in @grades_NEG_bef_ATT').copy()
    grade_aft_2006 = {
        '25': "TTH3",
        '26': "TTH2",
        '27': "TTH1",
        '33': "TTH3",
        '34': "TTH2",
        '35': "TTH1",
        '625': "TTH1",
        '626': "TTH2",
        '627': "TTH3",
        '628': "TTH4",
        '156': "TTH4",
        '157': "TTH4",
        '769': "TTH1",
        '391': "TTH1",
        '36': "TTH1",
        '37': "TTH1",
        '32': "TTH1",
        '30': "TTH2",
        '29': "TTH3",
        }
    grilles_ATT_bef['code_grade_NETNEH'] = grilles_ATT_bef['code_grade_NEG'].map(grade_aft_2006)
    return grilles.query('code_grade_NEG not in @grades_NEG_bef_ATT').append(grilles_ATT_bef)


def add_change_grade_variable(data, annee, grilles = get_grilles_including_bef_ATT(grilles = grilles)):
    cas_uniques_with_indic_chgmt_grade = []
    log.debug(data.index)
    ib_befs = data.index.get_level_values('ib_bef').tolist()

    assert not bool(set(ib_befs) & set(['NaN', -1])), \
        "There are invalid ib_bef:\n - {} entries with ib_bef = 'Nan'\n - {} entries with ib_bef = -1\n {}".format(
        len([ib for ib in ib_befs if ib == 'NaN']),
        len([ib for ib in ib_befs if ib == -1]),
        data.query("(ib_bef == 'NaN') or (ib_bef == -1)")
        )
    for annee_, ib_bef, c_cir in data.index:
        assert annee_ == annee
        c_cir_now = str(c_cir)
        c_cir_now_lower = 'TTH{}'.format(int(c_cir_now[-1:]) - 1)
        ib_bef = int(ib_bef)
        grille_c_cir_now = get_possible_grilles(c_cir_now, annee, grilles)
        assert ib_bef not in(['NaN', -1])
        grille_c_cir_now_inter_ib_bef = grille_c_cir_now.query('ib == {}'.format(ib_bef))
        # Changement de grade certain
        if len(grille_c_cir_now_inter_ib_bef) == 0:
            if c_cir_now == 'TTH1':
                cas_uniques_with_indic_chgmt_grade.append(format_output(
                    c_cir_now = c_cir_now,
                    ib_bef = ib_bef,
                    c_cir_bef_predit = "autre",
                    nombre_de_grades_possibles_before = 1,
                    ambiguite_before = False,
                    change_grade_before = True,
                    annee = annee,
                    echelon = None,
                    min_mois = None,
                    max_mois = None,
                    date_effet_grille = None,
                    corps = None,
                    ))
            else:
                grille_c_cir_now_lower = get_possible_grilles(
                    c_cir_now_lower,
                    annee,
                    grilles,
                    ).query(
                        'ib == {}'.format(ib_bef)
                        )[[
                            'code_grade_NETNEH',
                            'date_effet_grille',
                            'echelon',
                            'min_mois',
                            'max_mois',
                            'moy_mois',
                            'corps_NETNEH',
                            ]]
                if len(grille_c_cir_now_lower) == 0:
                    cas_uniques_with_indic_chgmt_grade.append(format_output(
                        c_cir_now = c_cir_now,
                        ib_bef = ib_bef,
                        c_cir_bef_predit = "autre",
                        nombre_de_grades_possibles_before = 1,
                        ambiguite_before = False,
                        change_grade_before = True,
                        annee = annee,
                        echelon = None,
                        min_mois = None,
                        max_mois = None,
                        date_effet_grille = None,
                        corps = None,
                        ))
                else:
                    date_effet_grille_max = grille_c_cir_now_lower.date_effet_grille.unique().max()
                    grille_c_cir_now_lower = grille_c_cir_now_lower.query(
                        'date_effet_grille == @date_effet_grille_max'
                        )
                    cas_uniques_with_indic_chgmt_grade.append(format_output(
                        c_cir_now = c_cir_now,
                        ib_bef = ib_bef,
                        c_cir_bef_predit = c_cir_now_lower,
                        nombre_de_grades_possibles_before = 1,
                        ambiguite_before = False,
                        change_grade_before = True,
                        annee = annee,
                        echelon = None,
                        min_mois = None,
                        max_mois = None,
                        date_effet_grille = None,
                        corps = None,
                        ))

        else:
            grille_c_cir_now_inter_ib_bef = grille_c_cir_now_inter_ib_bef.head(1)
            if c_cir_now != 'TTH1':
                grille_c_cir_now_lower = get_possible_grilles(
                    c_cir_now_lower,
                    annee,
                    grilles,
                    )
                grades_possibles_bef = grille_c_cir_now_lower.query(
                    'ib == {}'.format(ib_bef)
                    )[[
                        'code_grade_NETNEH',
                        'date_effet_grille',
                        'echelon',
                        'min_mois',
                        'max_mois',
                        'moy_mois',
                        'corps_NETNEH',
                        ]]
                if len(grades_possibles_bef) != 0:
                    grades_possibles = grades_possibles_bef.append(
                        pd.DataFrame([
                            c_cir_now,
                            grille_c_cir_now_inter_ib_bef['date_effet_grille'].values[0],
                            grille_c_cir_now_inter_ib_bef['echelon'].values.astype(str)[0],
                            grille_c_cir_now_inter_ib_bef['min_mois'].values.astype(int)[0],
                            grille_c_cir_now_inter_ib_bef['max_mois'].values.astype(int)[0],
                            grille_c_cir_now_inter_ib_bef['moy_mois'].values.astype(int)[0],
                            grille_c_cir_now_inter_ib_bef['corps_NETNEH'].values.astype(str)[0],
                            ]).transpose().rename(
                            columns = {
                                0: 'code_grade_NETNEH',
                                1: 'date_effet_grille',
                                2: 'echelon',
                                3: 'min_mois',
                                4: 'max_mois',
                                5: 'moy_mois',
                                6: 'corps_NETNEH',
                                }))
                    rang_grade_possible = 1
                    for index, row in grades_possibles.iterrows():
                        rang_grade_possible += 1
                        cas_uniques_with_indic_chgmt_grade.append(format_output(
                            c_cir_now = c_cir_now,
                            ib_bef = ib_bef,
                            c_cir_bef_predit = row["code_grade_NETNEH"],
                            nombre_de_grades_possibles_before = len(grades_possibles.code_grade_NETNEH.unique()),
                            change_grade_before = row["code_grade_NETNEH"] != c_cir_now,
                            ambiguite_before = len(grades_possibles) != 1,
                            annee = annee,
                            echelon = row["echelon"],
                            min_mois = row["min_mois"],
                            max_mois = row["max_mois"],
                            date_effet_grille = row["date_effet_grille"],
                            corps = row["corps_NETNEH"]
                            ))

                else:
                    cas_uniques_with_indic_chgmt_grade.append(format_output(
                        c_cir_now = c_cir_now,
                        ib_bef = ib_bef,
                        c_cir_bef_predit = c_cir_now,
                        nombre_de_grades_possibles_before = 1,
                        change_grade_before = False,
                        ambiguite_before = False,
                        annee = annee,
                        echelon = grille_c_cir_now_inter_ib_bef["echelon"].values.astype(str)[0],
                        min_mois = grille_c_cir_now_inter_ib_bef["min_mois"].values.astype(int)[0],
                        max_mois = grille_c_cir_now_inter_ib_bef["max_mois"].values.astype(int)[0],
                        date_effet_grille = grille_c_cir_now_inter_ib_bef["date_effet_grille"].values[0],
                        corps = grille_c_cir_now_inter_ib_bef["corps_NETNEH"].values.astype(str)[0]
                        ))
            else:
                grades_possibles_bef = None
                rang_grade_possible = 1
                for index, row in grille_c_cir_now_inter_ib_bef.iterrows():
                    cas_uniques_with_indic_chgmt_grade.append(format_output(
                        c_cir_now = c_cir_now,
                        ib_bef = ib_bef,
                        c_cir_bef_predit = c_cir_now,
                        nombre_de_grades_possibles_before = 1,
                        change_grade_before = False,
                        ambiguite_before = False,
                        annee = annee,
                        echelon = row["echelon"],
                        min_mois = row["min_mois"],
                        max_mois = row["max_mois"],
                        date_effet_grille = row["date_effet_grille"],
                        corps = row["corps_NETNEH"]
                        ))

    cas_uniques_w_indic_df = pd.concat(cas_uniques_with_indic_chgmt_grade)
    assert (cas_uniques_w_indic_df.query('ambiguite').groupby(
        ['annee', 'ib_bef', 'c_cir']
        )['c_cir_bef_predit'].count() > 1).all()
    assert (cas_uniques_w_indic_df.query("(not(ambiguite)) & (c_cir != 'TTH1')").groupby(
        ['annee', 'ib_bef', 'c_cir']
        )['c_cir_bef_predit'].count() == 1).all()
    c_cir_bef_predits = (cas_uniques_w_indic_df.query(
        '(change_grade == True) & (ambiguite == False)').c_cir_bef_predit
        .value_counts(dropna = False)
        .index.tolist()
        )
    assert 'TTH1' in c_cir_bef_predits
    return cas_uniques_w_indic_df


def format_output(
        c_cir_now,
        ib_bef,
        c_cir_bef_predit,
        nombre_de_grades_possibles_before,
        ambiguite_before,
        change_grade_before,
        annee,
        echelon,
        min_mois,
        max_mois,
        date_effet_grille,
        corps):
    return pd.DataFrame({
        "ib_bef": [ib_bef],
        "c_cir": [c_cir_now],
        "c_cir_bef_predit": [c_cir_bef_predit],
        "nombre_de_grades_possibles": [nombre_de_grades_possibles_before],
        "ambiguite": [ambiguite_before],
        "change_grade": [change_grade_before],
        "annee": [annee],
        "echelon": [echelon],
        "min_mois": [min_mois],
        "max_mois": [max_mois],
        "date_effet_grille": [date_effet_grille],
        "corps_NETNEH": [corps]
        }).set_index(["annee", "ib_bef", "c_cir"])


def get_career_transitions(
        data = None,
        annee = None,
        unique = False,
        ):
    """Returns an empty dataframe which important part is the index"""

    if data is None:
        data = pd.read_csv(
            os.path.join(output_directory_path, 'filter','data_ATT_{}_filtered.csv'.format(start_year)),
            index_col = 0,
            )
    columns_keep_1 = ['ident', 'annee', 'c_cir']
    columns_keep_2 = ['ident', 'ib']
    log.debug(data.query('annee == @annee').loc[data.query('annee == @annee').ib == -1])


    data_transition = (data
        .query('annee == @annee')
        .filter(columns_keep_1, axis = 1)
        .merge(
            data.query('annee == {}'.format(annee - 1))[columns_keep_2],
            on = ['ident'],
            how = 'inner'
            )
        .rename(columns = {"ib": "ib_bef"})
        )

    if unique:
        data_transition = data_transition[['annee', 'c_cir', 'ib_bef']].drop_duplicates().set_index(
            ["annee", 'ib_bef', "c_cir"]
            )
        return data_transition
    else:
        return data_transition


def get_possible_grilles(c_cir_now, annee, grilles = get_grilles_including_bef_ATT(grilles = grilles)):
    """ /!\ arbitrary choice of handling lag of one year in grille change implementation in 2009 and 2007 """
    date_effet_grille_bef = grilles[
        (grilles['code_grade_NETNEH'] == c_cir_now) &
        (grilles['date_effet_grille'] <= pd.datetime(annee - 1, 12, 31))
        ].date_effet_grille.max()
    if annee == 2009:
        list_date_effet_grille_bef = [date_effet_grille_bef]
        date_effet_grille_bef_precedente = grilles[
            (grilles['code_grade_NETNEH'] == c_cir_now) &
            (grilles['date_effet_grille'] < date_effet_grille_bef)
            ].date_effet_grille.max()
        list_date_effet_grille_bef.append(date_effet_grille_bef_precedente)
        grille_c_cir_now = grilles[
            (grilles['code_grade_NETNEH'] == c_cir_now) &
            (grilles['date_effet_grille'].isin(list_date_effet_grille_bef))
            ]
    elif annee == 2007:
        grilles_fusionnees_en_c_cir_now = get_grilles_pre_ATT_in_effect(c_cir_now, 2006)
        grille_c_cir_now = grilles_fusionnees_en_c_cir_now
    elif annee == 2006:
        grille_c_cir_now = get_grilles_pre_ATT_in_effect(c_cir_now, 2006).append(
            get_grilles_pre_ATT_in_effect(c_cir_now, 2005))
    elif annee < 2006:
        grille_c_cir_now = get_grilles_pre_ATT_in_effect(c_cir_now, annee)
    else:
        grille_c_cir_now = grilles[
            (grilles['code_grade_NETNEH'] == c_cir_now) &
            (grilles['date_effet_grille'] == date_effet_grille_bef)
            ]
    return grille_c_cir_now


def get_grilles_pre_ATT_in_effect(c_cir, annee, grilles = get_grilles_including_bef_ATT(grilles = grilles)):
    return grilles.merge(
        (grilles.query(
            '(code_grade_NETNEH == @c_cir) & (date_effet_grille <= @annee)'
            ).groupby(
                ['code_grade_NEG']
                ).agg({'date_effet_grille': np.max}).reset_index()),
        on = ['code_grade_NEG', 'date_effet_grille'],
        how = 'inner'
        )


def reshape_wide_to_long(data = None, start_year = None):
    if data is None:
        data = pd.read_csv(
            os.path.join(output_directory_path, 'filter', 'data_ATT_{}_filtered.csv'.format(start_year)),
            index_col = 0,
            ).query('annee >= annee_min_to_consider')
    data = data.rename(columns = {'ib': 'ib4'})
    data = pd.wide_to_long(
        data, ['ib'], i = ['ident', 'annee'], j = ''
        ).reset_index().rename(columns = {'': 'quarter'})
    data['quarter'] = data['quarter'].astype(int)
    return data
