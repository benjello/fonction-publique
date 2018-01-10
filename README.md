# Fonction publique

Modelling French public servants' careers.

## Test on binder

[![Binder](http://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/benjello/fonction-publique/binder?urlpath=lab)

## Install

````shell
git clone https://framagit.org/ipp/fonction-publique
cd fonction-publique
pip install -e .
````

## Requirements

To be able to use this package you need access to CNRACL career data and salary scale data.


## Configuration

You need to configure some important paths through the file `config.ini` located in in the user configuration directory for `fonction-publique`.
You can retrieve this location by running the following test:
````shell
nosetests fonction_publique/tests/test_config.py -svx
````


## Clean the raw career data

Raw data needs to be cleaned to be used by the various programs.
This takes a long time and can be achieved by executing the following command
````shell
clean_career -v
````

## Clean the grilles legislation data
````shell
clean_grilles
````

## Generate relevant data for analysis

Extract the relevant information from the clean data and filter it to keep only what is needed for the estimation
````shell
generate_data -v
````



<!-- ## Estimation et prédiction du grade en t+1
A partir des coefficients estimés à l'étape estimation, on prédit le grade à l'année suivante.
Les différentes modalités sont à ce stade (i) rester dans le grade (no exit) (ii) partir dans le grade suivant dans le corps et (iii) partir dans un autre grade hors du corps. Pour chaque individu nous tirons la modalité prédite.
Le grade à l'année suivante en découle immédiatement pour les modalités (i) et (ii).
Pour la modalité (iii) les grades possibles dépendent directement des différents grades possibles, ce qui sera arbitré par la CDC. A ce stade nous tirons le grade dans la distribution des grade de destination observés, par grade, et en prenant uniquement les grades dont on dispose dans les grilles.
(voir fonctions predict_next_year et predict_next_grade dans estimation/0_Outils_CNRACL.R)
 -->
  




