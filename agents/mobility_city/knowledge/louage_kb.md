<!--
Contenu à vérifier et enrichir avec des sources officielles (service-public.tn, sites des ministères) avant mise en production.

Périmètre : uniquement des informations générales et stables sur le système du louage.
Ne JAMAIS ajouter d'horaires précis, de disponibilités ou de prix exacts par trajet : ces données
changent en permanence et l'agent n'a pas accès à une source en temps réel.
Les fourchettes de prix en dinars ci-dessous servent aussi de liste blanche au test de régression
(scripts/test_louage_agent.py) : un montant absent de ce fichier est considéré comme inventé.

Format : une section « ## » par sujet. Chaque section est indexée comme un document
indépendant dans la base vectorielle — garder chaque section autonome (moins de ~4000 caractères).
Les mentions « (à confirmer) » signalent les informations incertaines.
-->

# Le louage en Tunisie

## Qu'est-ce qu'un louage et comment ça fonctionne

**Principe :** le louage est un taxi collectif interurbain. Des véhicules partagés (généralement des monospaces ou minibus d'environ 8 places passagers) relient les villes entre elles, au départ de stations dédiées.

**Fonctionnement :**
- Chaque station de louage est organisée par **lignes** : une zone ou un emplacement par destination, souvent signalé par un panneau ou annoncé à voix haute par les chauffeurs et les responsables de la station
- Le passager se rend à la ligne de sa destination et prend place dans le véhicule en cours de remplissage
- **Le véhicule part quand il est plein**, et non à une heure fixe : il n'y a pas d'horaires de départ
- Le temps d'attente dépend de l'affluence : court aux heures chargées et sur les lignes fréquentées, plus long aux heures creuses ou sur les lignes peu demandées
- Les passagers peuvent en pratique payer les places restantes pour partir sans attendre que le véhicule se remplisse (à confirmer selon la station)
- En général, il n'y a pas de réservation : on se présente à la station (à confirmer)
- Il est souvent possible de descendre en cours de route sur l'itinéraire, en prévenant le chauffeur ; le prix payé est en général celui du trajet complet de la ligne (à confirmer)

**Reconnaître un louage :** véhicules de couleur blanche avec une bande de couleur. La bande rouge correspond en général aux liaisons entre gouvernorats (interurbain), la bande bleue aux liaisons à l'intérieur d'un même gouvernorat ; d'autres couleurs existent pour le transport rural (à confirmer).

**Horaires :** les départs sont fréquents en journée sur les grandes lignes. Ils deviennent plus rares en soirée et la nuit, et certaines lignes cessent de fonctionner le soir (à confirmer selon la ligne et la station). Il n'existe pas d'horaire officiel publié pour les louages.

## Où trouver une station de louage

**Principe général :** chaque ville importante possède au moins une station de louage (aussi appelée « gare louage »), d'où partent les véhicules vers les autres villes. Dans les grandes villes, il peut y avoir plusieurs stations, chacune desservant une direction géographique. Les villes plus petites ont en général une seule station, souvent proche du centre ou de la gare routière des bus (à confirmer).

**Tunis :**
- La **station Moncef Bey** dessert principalement les destinations du Sud et du Sahel (par exemple Sousse, Sfax) (à confirmer)
- La **station Bab Saadoun** dessert principalement les destinations du Nord et du Nord-Ouest (à confirmer)
- La répartition exacte des lignes entre les stations peut évoluer : se renseigner avant de partir (à confirmer)

**Sousse :** la ville dispose d'une station principale de louage desservant les autres villes du Sahel, Tunis et le Sud (emplacement exact à confirmer localement).

**Sfax :** la ville dispose d'une station principale de louage desservant Tunis, le Sahel et le Sud (emplacement exact à confirmer localement).

**Comment trouver la bonne station :**
- Demander aux habitants, à un chauffeur de taxi ou de louage : les stations sont très connues localement
- Pour un retour, les louages déposent en général les passagers à la station de la ville d'arrivée, d'où partent aussi les louages vers la ville d'origine

## Tarifs indicatifs du louage

**Principe :** le prix d'une place en louage est fixé par ligne (par trajet) et n'est pas négocié en principe ; les tarifs sont réglementés et révisés périodiquement (à confirmer). Le prix est le même pour tous les passagers d'une même ligne.

**Facteurs qui influencent le prix :**
- La **distance** du trajet : c'est le facteur principal
- La **région** et le type de liaison (à l'intérieur d'un gouvernorat ou entre gouvernorats)
- Les révisions officielles des tarifs (hausse du carburant, etc.) (à confirmer)

**Fourchettes indicatives (ordre de grandeur, pas un prix par trajet) :**
- Trajets courts, moins de 50 km environ : de l'ordre de 2 à 6 DT (à confirmer)
- Trajets moyens, de 100 à 200 km environ : de l'ordre de 10 à 20 DT (à confirmer)
- Longs trajets, plus de 250 km environ : de l'ordre de 20 à 40 DT (à confirmer)

**À savoir :**
- Ces fourchettes sont indicatives et peuvent ne plus correspondre aux tarifs en vigueur ; le prix exact d'un trajet se vérifie à la station, auprès du responsable de la ligne ou du chauffeur
- Un supplément peut être demandé pour des bagages volumineux (à confirmer)
- Payer les places vides pour partir plus tôt revient à payer le prix de chaque place supplémentaire (à confirmer)

## Louage ou autres transports (bus, train)

**Louage :**
- Avantages : départs fréquents sur les grandes lignes, pas besoin de réservation, souvent plus rapide que le bus ou le train sur les trajets moyens, dessert de nombreuses villes
- Inconvénients : pas d'horaire fixe (attente variable), peu d'espace pour les bagages, confort limité sur les longs trajets, départs rares le soir et la nuit

**Bus interurbains (SNTRI) et bus régionaux :**
- La SNTRI (Société Nationale du Transport Interurbain) assure des liaisons nationales en autocar entre les grandes villes, avec des horaires fixes ; des sociétés régionales de transport assurent les liaisons à l'intérieur des régions (à confirmer)
- Avantages : horaires connus à l'avance, souvent moins cher que le louage, plus de place pour les bagages, liaisons de nuit sur certaines lignes (à confirmer)
- Inconvénients : moins de départs, trajets souvent plus longs

**Train (SNCFT) :**
- La SNCFT (Société Nationale des Chemins de Fer Tunisiens) exploite le réseau ferroviaire, notamment la ligne desservant Tunis, Sousse, Sfax et le Sud (à confirmer pour les dessertes exactes)
- Avantages : horaires fixes, plus de confort et d'espace, possibilité de choisir une classe
- Inconvénients : réseau limité à certaines villes, nombre de départs réduit, retards possibles (à confirmer)

**Quand préférer quoi (repères généraux) :**
- Partir rapidement en journée sans avoir planifié, sur une grande ligne : louage
- Voyager le soir ou la nuit, ou avec beaucoup de bagages : bus ou train, selon les horaires disponibles
- Rechercher le confort sur un long trajet desservi par le rail : train
- Petit budget : comparer avec le bus, souvent moins cher (à confirmer)

## Règles et bon sens pour les passagers

**Paiement :**
- Le paiement se fait en espèces, au chauffeur ou au guichet / responsable de la ligne selon la station (à confirmer)
- Prévoir de la monnaie : les chauffeurs n'ont pas toujours de quoi rendre la monnaie sur les gros billets

**Bagages :**
- L'espace est limité (coffre ou galerie de toit) : privilégier un bagage de taille raisonnable
- Signaler un bagage volumineux au chauffeur avant de monter ; un supplément peut être demandé (à confirmer)
- Garder les objets de valeur et les documents sur soi

**Être sur la bonne ligne :**
- Vérifier la destination affichée sur la ligne ou sur le véhicule
- Demander confirmation au chauffeur ou au responsable de la ligne avant de monter et de payer
- Si l'on descend en cours de route, le signaler au chauffeur dès le départ

**Sécurité :**
- Attacher sa ceinture de sécurité quand elle est disponible
- En cas de conduite dangereuse, il est possible de demander au chauffeur de ralentir
- Éviter de voyager tard le soir sur des lignes peu fréquentées, où les départs peuvent être rares et l'attente longue (à confirmer)
- En cas d'urgence sur la route : Garde nationale au 193, Protection civile au 198

## Limites de ce que cet agent peut savoir

**Cet assistant n'a pas accès à des données en temps réel.** Sa base de connaissances contient uniquement des informations générales et stables sur le fonctionnement du louage.

**Informations que cet assistant ne peut PAS fournir :**
- **Horaires de départ :** le louage n'a pas d'horaires fixes (le véhicule part quand il est plein), et l'assistant ne sait pas si des véhicules partent à un moment donné
- **Disponibilité en temps réel :** l'assistant ne peut pas savoir s'il y a un louage disponible maintenant, ce soir ou à une heure précise, ni combien de places restent
- **Prix exact du jour pour un trajet donné :** l'assistant ne connaît que des fourchettes indicatives générales ; le tarif en vigueur pour une ligne se vérifie à la station
- **Perturbations :** grèves, fermetures de routes, changements d'emplacement de station, affluence exceptionnelle (fêtes, fin de semaine)

**Comment obtenir ces informations :**
- Se renseigner directement à la station de louage de départ (sur place ou auprès de personnes qui s'y rendent régulièrement)
- Pour un départ le soir, prévoir de l'avance et une solution de repli (bus ou train), car les départs de louage deviennent rares en soirée
- Pour les horaires fixes des bus et des trains, se renseigner auprès de la SNTRI ou de la SNCFT (gare routière, gare ferroviaire) (à confirmer)
