

# Imputation des grades en rétrospectif

Cette note vise récapituler et préciser l'approche pour l'imputation des grades en rétrospectif quand l'information
du CIR n'est pas disponible, en utilisant l'information apportée par les libellés remplis à la main. 

L'objectif de cette imputation est double: 
- Augmenter le recul temporel disponible pour analyser les trajectoires de carrières
- Obtenir pour chaque individu une durée passée dans le grade pour pouvoir simuler les évolutions indiciaires. 
 

Le redressement des libellés ne sera pas exhaustif et doit donc être circonscrit dans l'espace (quels grades traite-t-on?) et le temps (jusqu'à quand remonte-t-on?).  
La liste des grades à redresser a été établie par la CdC, et se trouve en annexe. L'année de remontée n'est pas encore arrêtée à ce stade. Elle peut en outre dépendre 
des grades considérés car les fusions de grilles peuvent compliquer le redressement. 

Le redressement des libellés se fait par trois méthodologies distinctes et successives: 
1. Redressement sur la base des années d'affiliation pour les grades initiaux (Anthony)
2. Redressement sur la base des correspondances C_CIR/libellés pour les années pour lesquelles les deux sont disponibles (Isabelle)
3. Redressement sur la base du matching entre libellés et grilles. 


# Etape 1: Redressement des libellés à partir des années d'affiliation

Anthony

# Etape 2: Redressement des libellés à partir du C_CIR

Isabelle

# Etape 3: Matching entre grilles et libellés


L'objectif du matching est d'attribuer à un maximum de libellés une correspondance sur une grille (code NEG, code NETNEH, période de validité). 
Dans la deuxième version du matching, l'approche sera la suivante: 
1. Détermination de la grille que l'on souhaite traiter. 
2. Classification des libellés correspondant à cette grille

### Détermination de la grille à traiter. 

Une grille est déterminée à partir : (i) du libellé NETNEH (ii) de la période de validité. 
La première étape est donc la saisie du libellé NETNEH à la volée, et de la comparaison avec la liste des libellés "officiels" que l'on veut classer. 
On choisit donc à partir d'une liste présentée le libellé que l'on classe. 
Sont présentées ensuite l'ensemble des grilles comportant ce nom, pour différentes périodes de validité. 
L'utilisateur choisit ensuite la grille sur laquelle il veut classer les libellés. 

### Classification des libellés

Une fois la grille sélectionnée, nous comparons le libellé "officiel" du grade avec l'ensemble des libéllés présents dans la base carrière parmi les libellés 
(i) non classés (avec prise en compte ou non des étapes 1 et 2) et (ii) apparaissant dans la base aux années de validité de la grille. 

Pour chaque libellé, un score de correspondance avec le libellé de référence est calculé. Le programme de matching affiche l'ensemble des libellés, 
classés par score. On sélection alors les libellés que l'on souhaite classer dans la grille. 

Après discussion avec Laurent le classement suivra les modalités suivantes: 
- Au plus 20 libellés affichés 
- Sortie du pool des libellés à classer pour les libellés affichés qui ne sont pas classés d'une étape à l'autre. 


### Liste des problèmes à anticiper



#### Organisation du travail: 

Gérer le travail en parallèle sur différents grades. Flag des grades déjà traités (et du niveau de correspondance atteint?)


#### Tests de cohérance

Il est possible de tester la cohérance du redressement à partir des IB. Si l'IB correspond à un échelon présent sur la grille, cela veut dire que le redressement est
potentiellement bon (pas forcément bon, il s'agit d'une condition nécessaires mais non suffisante car un même ib est présent sur plusieurs grilles).

Nous pourrons utiliser ce test pour évaluer la qualité du matching et éventuellement comparer les résultats donnés par les étapes 1, 2 et 3. 

#### Rupture statistique pour les libellés non classés. 

Si l'on cherche à déterminer le changement de grade à partir des libellés reclassés, nous risquons de surestimer la probabilité de
changement de grade aux années pour lesquelles nous avons des ruptures statistiques (présence du C_CIR en 2011, regroupement de grilles). 
En effet, si l'on considère que l'on a un changement de grade quand libellé(t) != libellé (t-1), si la probabilité d'avoir un libellé classé 
diminue de manière discontinue à une année donnée, la probabilité d'identifier un changement de grade à cette année augmentera aussi. 

Il faudra donc surveiller l'évolution de la part des libellés classées au cours du temps et réfléchir à la manière de gérer les discontinuités le cas échéant. 


#### Gestion des retards dans les changements de grille

Une des questions concerne la présence potentielle de libellés correspondant à des grilles ayant disparu. Par exemple 
si l'on trouve encore beaucoup d'agents de salubrité après la disparition du corps en 2006, cela pourrait poser problème
car le matching en état ne permet pas de classer des libellés en dehors de la date de validité d'une grille. Nous pouvons
toutefois considérer que ce problème est de second ordre, sous preuve du contraire. A titre d'illustration il semble que 
la disparition du grade des agents de salubrité sa traduit bien en disparition des libellés correspondants. 

| annee | versant | libemploi_slugified | count |
|-------|---------|---------------------|-------|
| 2000  | T       | agent_de_salubrite  | 4054  |
| 2001  | T       | agent_de_salubrite  | 4363  |
| 2002  | T       | agent_de_salubrite  | 4921  |
| 2003  | T       | agent_de_salubrite  | 5601  |
| 2004  | T       | agent_de_salubrite  | 6297  |
| 2005  | T       | agent_de_salubrite  | 7486  |
| 2006  | T       | agent_de_salubrite  | 5     |
| 2007  | T       | agent_de_salubrite  | 1     |
| 2011  | T       | agent_de_salubrite  | 87    |
| 2012  | T       | agent_de_salubrite  | 93    |
| 2013  | T       | agent_de_salubrite  | 78    |
| 2014  | T       | agent_de_salubrite  | 66    |
| 2015  | T       | agent_de_salubrite  | 35    |




# Annexes

### Liste des grades à traiter

### Description des données de grilles 





