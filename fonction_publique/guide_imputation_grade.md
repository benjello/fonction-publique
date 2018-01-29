# Correspondance entre libellé et grade: guide d'utilisation

## Introduction

Objectif du programme: obtenir les grades correspondants aux libellés remplis à la main pour les années 2000 à 2014.

Toutes les manipulations de l'utilisateur se font dans le terminal (invite de commande http://fr.wikihow.com/changer-de-r%C3%A9pertoire-dans-le-mode-de-commande)

Liste des étapes pour la mise en oeuvre du matching
  - Initialisation: installation de l'environnement de travail (Python, chemins)
  - Programme de matching qui crée la table de correspondance entre libellé et grade.


## Initialisation : installation de Python et gestion des chemins

1. Installation de Python et des paquets idoines (fait sur l'ordinateur de Laurent)
L'utilisation du programme nécessite l'installation de python ainsi que l'installation à la main des packages suivants:
- fuzzywuzzy
- python-Levenshstein
- python-slugify

Il est possible de vérifier qu'ils sont installés en faisant : `pip list`

S'ils ne sont pas installés il peuvent être récupérés sur les sites suivants:
- fuzzywuzzy : https://pypi.python.org/pypi/fuzzywuzzy/0.13.0
- python-Levenshstein : http://www.lfd.uci.edu/~gohlke/pythonlibs/#python-levenshtein
- python-slugify : https://pypi.python.org/pypi/python-slugify/1.2.1

Pour les installer le paquet, il y a deux possibilités :
- `pip instal nom_du_paquet.whl`
- Aller dans le répertoire du paquet (ou se trouve le fichier setup.py) et faire `pip install .`

L'initialisation du programme fournit ici se fait de la manière suivante:
    - se rendre dans le répertoire fonction-publique
    - installer le paquet fonction_publique : `pip install .`

2. Gestion des chemins
    Doivent être précisés dans un fichier config.ini (à partir du config_template.ini) les chemins suivants:
    - Données (`[data]`) : emplacement des données initiales (raw) et des données retravaillée (clean). Inutiles sid onnées sur les libellés emplois ont été transmises.
    - Correspondances (`[correspondances]`): emplacement du dossier où l'on souhaite conserver la table de correspondance.

Normalement un ficheir `config.ini` contenant les lignes suivantes devrait convenir:

```
[correspondances]
h5 = /chemin/vers/le/fichier/correspondances.h5
libelles_emploi_directory = /chemin/vers/le/repertoire/contenant/les/fichiers/libelles/
```

## Programmes d'imputation des grade pour les libellés observés entre 2000 et 2014.

inputs :
 - liste des libellés observés chaque année pour chaque versant de la fonction publique (base libemploi)
 - éventuellement une table de correspondance déjà commencée que l'on complète avec les libellés qui n'ont pas encore été renseignés.

output: table de correspondance entre les libellés et les grades officiels.

programmes:
 - `grade_matching_from_netneh`

N.B Pour chaque décennie, le chargement de la base pour la première fois prend du temps, car l'on lance une procédure pour neutraliser
les différences entre libellés simplement dus aux différences de majuscule, d'espace, ou d'accent.

##  Résumé des étapes à réaliser:

 - Installer python et les packages
 - Lancer le setup.py ('pip install .')
 - Renseigner les chemisn dans le ficheirs de configuration  
 - Lancer l'algorithme de classification des libellés ('grade_matching_from_netneh')
