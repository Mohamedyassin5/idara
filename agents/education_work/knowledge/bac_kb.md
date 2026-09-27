<!--
Contenu à vérifier et enrichir avec des sources officielles (service-public.tn, sites des ministères) avant mise en production.
Sources à privilégier : ministère de l'Éducation et portail national de l'orientation universitaire.

Périmètre : uniquement des informations générales et stables sur le baccalauréat et l'orientation.
Ne JAMAIS ajouter de dates de l'année en cours (épreuves, inscriptions, résultats), de scores
d'orientation par filière, ni de capacités d'accueil : ces données changent chaque année.
Ce fichier ne contient volontairement AUCUNE date au format jour/mois ni aucun score chiffré :
il sert de référence au test de régression (scripts/test_bac_agent.py).

Format : une section « ## » par sujet. Chaque section est indexée comme un document
indépendant dans la base vectorielle — garder chaque section autonome (moins de ~4000 caractères).
Les mentions « (à confirmer) » signalent les informations incertaines.
-->

# Baccalauréat et orientation universitaire en Tunisie

## Structure générale du baccalauréat tunisien

**Ce qu'est le baccalauréat :** examen national de fin d'études secondaires, passé à l'issue de la dernière année du lycée. Il sanctionne la fin du secondaire et conditionne l'accès à l'enseignement supérieur.

**Les sections (filières) :**
- **Mathématiques**
- **Sciences expérimentales**
- **Sciences techniques**
- **Sciences de l'informatique**
- **Économie et gestion**
- **Lettres**
- **Sport** (à confirmer selon les années et les établissements)

L'élève choisit sa section pendant le lycée ; chaque section a ses matières dominantes et ses propres coefficients.

**Principe des épreuves :**
- Les épreuves finales sont essentiellement écrites et nationales : mêmes sujets et même calendrier pour tout le pays
- Certaines matières donnent lieu à des épreuves pratiques ou orales selon la section (travaux pratiques, langues, sport) (à confirmer)
- Chaque matière porte un **coefficient** propre à la section : une même matière ne pèse pas autant en Mathématiques qu'en Lettres
- L'examen comporte une **session principale** puis une **session de contrôle** (rattrapage) pour les candidats qui n'ont pas été admis directement et remplissent les conditions (à confirmer)

**Calendrier :** les épreuves se déroulent en fin d'année scolaire, la session de contrôle suivant la session principale. Les dates exactes sont fixées chaque année par le ministère de l'Éducation et ne figurent pas dans cette base.

## Comment est calculée la moyenne du bac

**Les deux composantes :** la moyenne du baccalauréat combine le travail de l'année et les épreuves finales.
- La **moyenne annuelle** (contrôle continu de la dernière année) compte pour une part de la moyenne finale
- La **note des épreuves finales** compte pour le reste, avec un poids nettement plus important
- La répartition exacte entre ces deux composantes est fixée par la réglementation et peut évoluer : les proportions ne figurent pas dans cette base (à confirmer auprès de l'établissement ou du ministère de l'Éducation)

**Le rôle des coefficients :**
- Chaque matière a un coefficient dépendant de la section : les matières de spécialité ont les coefficients les plus élevés
- La moyenne est une moyenne pondérée : la note de chaque matière est multipliée par son coefficient, et le total est divisé par la somme des coefficients
- Une bonne note dans une matière à fort coefficient pèse donc bien plus qu'une bonne note dans une matière à faible coefficient

**Admission :**
- L'admission est prononcée à partir d'un seuil de moyenne générale, sur 20 (à confirmer pour les règles précises)
- Selon les résultats, un candidat peut être admis à la session principale, autorisé à passer la session de contrôle, ou ajourné (à confirmer)
- Des mentions peuvent être attribuées selon la moyenne obtenue (à confirmer)

**À savoir :** la moyenne du bac ne sert pas seulement à l'admission, elle entre aussi dans le calcul du score utilisé pour l'orientation universitaire.

## L'orientation universitaire après le bac

**Principe :** l'affectation dans l'enseignement supérieur public se fait par un système national d'orientation, en ligne. Le bachelier ne s'inscrit pas librement dans l'établissement de son choix : il exprime des vœux, et l'affectation dépend de son score et de ces vœux.

**Les étapes générales :**
1. Après la publication des résultats, le bachelier reçoit un accès personnel au système d'orientation en ligne
2. Il consulte la liste des filières proposées, chacune avec son code
3. Il saisit ses **vœux, classés par ordre de préférence**
4. Le système calcule un **score d'orientation** pour chaque filière demandée
5. Les candidats sont classés par score décroissant, filière par filière, dans la limite des places disponibles
6. Chaque bachelier reçoit une affectation, et une phase complémentaire peut être organisée pour les places restantes (à confirmer)

**Le score d'orientation :** il est calculé à partir de la moyenne du bac et des notes de certaines matières, avec des coefficients qui dépendent de la filière demandée. Une même moyenne ne donne donc pas le même score pour toutes les filières : les matières importantes pour la filière comptent davantage (à confirmer pour les formules exactes, qui peuvent évoluer).

**L'ordre des vœux est déterminant :**
- Classer les vœux par préférence réelle, et non par « chances d'être pris »
- Saisir un nombre suffisant de vœux, en combinant des filières très demandées et d'autres plus accessibles
- Se renseigner sur le contenu réel des filières et leur lieu avant de les classer
- Respecter les délais : le système ferme à une date fixée chaque année

**Les scores des années précédentes :** les scores du dernier candidat orienté dans chaque filière sont en général publiés après l'affectation. Ils donnent une indication, mais varient chaque année selon le nombre de candidats et les places offertes. Ils ne figurent pas dans cette base.

**Où se renseigner :** auprès du lycée, du conseiller d'orientation, et sur le portail officiel d'orientation universitaire mis en place par le ministère de l'Enseignement supérieur (adresse et calendrier à vérifier chaque année).

## Les filières universitaires selon la section du bac

**Principe général :** la plupart des filières sont ouvertes à plusieurs sections du bac, mais avec des coefficients de score différents. Une section n'interdit donc pas une filière : elle la rend plus ou moins accessible. L'aperçu ci-dessous donne les débouchés les plus courants, sans être exhaustif et sans citer d'établissements.

- **Mathématiques et Sciences techniques :** cycles préparatoires et écoles d'ingénieurs, filières scientifiques et technologiques, architecture, statistiques et informatique
- **Sciences expérimentales :** études de santé (médecine, pharmacie, médecine dentaire), sciences biologiques, agronomie et sciences vétérinaires, filières scientifiques
- **Sciences de l'informatique :** informatique, génie logiciel, technologies de l'information, filières scientifiques proches
- **Économie et gestion :** sciences économiques, gestion, comptabilité et finance, commerce, filières juridiques
- **Lettres :** droit, langues et lettres, sciences humaines et sociales, information et communication, filières de l'enseignement
- **Sport :** filières liées aux sciences et techniques du sport et de l'éducation physique (à confirmer)

**À savoir :**
- Les filières très demandées, notamment en santé et en ingénierie, exigent les scores les plus élevés
- À côté des universités publiques, il existe un secteur privé avec ses propres conditions d'admission, hors du système national d'orientation (à confirmer)
- Le contenu et l'intitulé des filières évoluent : la liste officielle de l'année en cours fait foi

## Conseils de méthode pour réviser le bac

**Organiser le temps :**
- Établir un planning de révision réaliste, matière par matière, plutôt que de réviser au hasard
- Donner plus de temps aux matières à fort coefficient dans votre section, sans abandonner les autres
- Réviser régulièrement sur plusieurs mois : les révisions réparties dans le temps sont plus efficaces que le bachotage de dernière minute
- Prévoir des pauses courtes et régulières pendant les séances de travail

**Travailler efficacement :**
- S'entraîner sur des sujets d'annales et des épreuves blanches, en conditions réelles : même durée, sans notes
- Corriger ses épreuves blanches et analyser ses erreurs, plutôt que de seulement refaire des exercices réussis
- Apprendre à gérer le temps pendant l'épreuve : répartir les minutes entre les exercices et garder du temps pour la relecture
- Reformuler le cours avec ses mots, faire des fiches courtes, expliquer une notion à quelqu'un d'autre
- Travailler en groupe pour les points difficiles, à condition que la séance reste consacrée au travail

**Gérer le stress et la fatigue :**
- Dormir suffisamment, en particulier la veille des épreuves : la nuit blanche de révision est contre-productive
- Manger correctement et garder une activité physique légère
- Préparer la veille les documents et le matériel nécessaires, et vérifier le lieu de l'examen à l'avance
- Un stress modéré est normal ; en cas d'angoisse importante, en parler à un proche, à un enseignant ou au conseiller d'orientation du lycée

**À savoir :** aucune méthode ne garantit un résultat. Ces conseils sont des repères généraux, à adapter à votre façon de travailler et aux consignes de vos enseignants.

## Limites de ce que cet agent peut savoir

**Cet assistant n'a pas accès aux données de l'année en cours.** Sa base de connaissances contient uniquement des informations générales et stables sur le baccalauréat et l'orientation.

**Informations que cet assistant ne peut PAS fournir :**
- **Dates de l'année en cours :** calendrier des épreuves, dates de la session de contrôle, dates d'ouverture et de fermeture de la saisie des vœux, dates de publication des résultats
- **Scores d'orientation :** le score requis pour une filière ou une université, y compris celui des années précédentes, car il change chaque année
- **Résultats :** il ne peut consulter aucun résultat individuel, ni relevé de notes, ni affectation
- **Places disponibles :** capacités d'accueil des filières et des établissements
- **Formules et coefficients exacts :** les coefficients par matière et les formules de calcul des scores peuvent évoluer d'une année à l'autre
- **Listes d'établissements** et conditions particulières d'un établissement précis

**Comment obtenir ces informations :**
- S'adresser au lycée, au surveillant général ou au conseiller d'orientation, qui reçoivent les informations officielles
- Consulter les publications officielles du ministère de l'Éducation pour le calendrier des épreuves et les résultats
- Consulter le portail officiel d'orientation universitaire du ministère de l'Enseignement supérieur pour le calendrier de l'orientation, la liste des filières et les scores publiés après affectation
