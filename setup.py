#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" -- simulating French public servants' careers"""


from setuptools import setup, find_packages


setup(
    name = 'Fonction-Publique',
    version = '0.3.3',
    author = 'IPP Team',
    author_email = 'mahdi.benjelloul@ipp.eu',
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    description = u'',
    keywords = 'public servant france microsimulation career earnings',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url = 'https://git.framasoft.org/ipp/fonction-publique',
    entry_points = {
        'console_scripts': [
            'clean_grilles=fonction_publique.scripts.clean_grilles:main',
            'clean_raw_carreer=fonction_publique.scripts.clean_raw_career:main',
            'generate_data=fonction_publique.scripts.generate_data:main',
            'grade_matching_from_neg=fonction_publique.matching_grade.grade_matching_from_neg:main',
            'grade_matching=fonction_publique.matching_grade.grade_matching:main',
            'simulation=fonction_publique.estimation.simulation:main',
            'test_script=fonction_publique.test_script:main'
            ],
        },
    data_files = [
        ('share/openfisca/fonction-publique', ['LICENSE', 'README.md']),
        ],

    include_package_data = True,  # Will read MANIFEST.in
    install_requires = [
        'fuzzywuzzy >= 0.11.1',
        'numpy >= 1.6',
        # 'OpenFisca-France >= 0.5.3',
        'pandas >= 0.18.1',
        'python-slugify',
        'pyxdg >= 0.25',
        ],
    packages = find_packages(exclude=['fonction_publique.tests*']),
    test_suite = 'nose.collector',
    )
