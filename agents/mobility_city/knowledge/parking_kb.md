<!--
Contenu à vérifier et enrichir avec des sources officielles (service-public.tn, sites des municipalités) avant mise en production.

Périmètre : uniquement le fonctionnement général et stable du stationnement en Tunisie.
Ne JAMAIS ajouter de disponibilité de places en temps réel, ni de tarif exact pour un parking
précis : ces données changent en permanence et l'agent n'a pas accès à une source en temps réel.
Les fourchettes de prix en dinars ci-dessous servent aussi de liste blanche au test de régression
(scripts/test_parking_agent.py) : un montant absent de ce fichier est considéré comme inventé.

Format : une section « ## » par sujet. Chaque section est indexée comme un document
indépendant dans la base vectorielle — garder chaque section autonome (moins de ~4000 caractères).
Les mentions « (à confirmer) » signalent les informations incertaines.
-->

# Le stationnement en Tunisie

## Le stationnement payant en Tunisie — principe général

**Qui organise le stationnement :** le stationnement sur la voie publique relève de la municipalité de la ville. Les règles, les zones payantes et les tarifs sont donc fixés localement et varient d'une ville à l'autre (à confirmer).

**Les zones payantes :** dans les centres-villes des grandes villes, certaines rues et places sont en stationnement payant, souvent délimitées par un marquage au sol et des panneaux. Le paiement peut se faire à un horodateur quand il y en a, ou auprès d'un agent qui délivre un reçu (à confirmer selon la ville et la zone). Le stationnement payant s'applique en général pendant la journée en semaine, avec des horaires affichés sur place ; il est souvent gratuit la nuit, le dimanche et les jours fériés (à confirmer localement).

**Les gardiens de parking :** dans la pratique, une grande partie du stationnement en centre-ville et près des lieux très fréquentés (marchés, plages, administrations, stades) est encadrée par des gardiens de parking, reconnaissables à un gilet. La situation est variable :
- Certains sont mandatés par la municipalité ou exploitent un emplacement en concession, et délivrent un reçu
- D'autres exercent de façon informelle, sans reçu, et demandent une somme au moment où l'on se gare ou au retour
- Il est d'usage de leur remettre une petite somme ; dans les faits, refuser peut créer une tension, mais aucun paiement n'est dû sans reçu à un gardien non mandaté (à confirmer)

**Stationnement interdit ou gênant :** trottoirs, passages piétons, arrêts de bus, doubles files, entrées de garage et emplacements réservés (personnes handicapées, véhicules officiels) sont interdits au stationnement. Le véhicule s'expose à une contravention et, dans les cas gênants, à une mise en fourrière.

## Comment payer le stationnement

**À l'horodateur (là où il y en a) :**
1. Repérer l'horodateur de la zone et les horaires payants affichés
2. Sélectionner la durée souhaitée et payer, en général en pièces (à confirmer selon l'appareil)
3. Récupérer le ticket et le placer sur le tableau de bord, bien visible derrière le pare-brise
4. Revenir avant la fin de la durée payée

**Auprès d'un agent ou d'un gardien de parking :**
- Demander le tarif avant de se garer, et demander un reçu quand la place est gérée officiellement
- Le paiement se fait en espèces ; prévoir de la monnaie
- Le paiement se fait selon les cas au moment où l'on se gare ou au retour au véhicule (à confirmer)

**Dans un parking privé ou couvert :**
1. Prendre un ticket à la barrière d'entrée
2. Payer à la caisse (automatique ou guichet) avant de rejoindre le véhicule, ou à la sortie selon le parking
3. Conserver le ticket : sa perte entraîne en général la facturation d'un forfait (à confirmer)

**Paiement par application mobile :** des solutions de paiement du stationnement par application existent dans certaines villes ou pour certains parkings, mais leur disponibilité varie et ne peut pas être garantie (à confirmer localement).

**Conseils :**
- Garder de la monnaie dans le véhicule : les horodateurs et les gardiens ne rendent pas toujours la monnaie
- Conserver le reçu ou le ticket jusqu'au départ

## Tarifs indicatifs du stationnement

**Principe :** les tarifs de la voie publique sont fixés par la municipalité et varient selon la ville et la zone. Les parkings privés fixent librement leurs tarifs. Les montants ci-dessous sont des ordres de grandeur, pas les tarifs d'un lieu précis.

**Facteurs qui influencent le prix :**
- La **durée** du stationnement (tarif à l'heure, à la demi-journée ou forfait journée)
- La **zone** : un centre-ville ou un quartier très fréquenté coûte plus cher qu'un quartier périphérique
- Le **type d'emplacement** : voie publique, parking de surface, parking couvert, parking d'aéroport
- La **période** : événements, saison estivale près des plages, jours de marché (à confirmer)

**Fourchettes indicatives (ordres de grandeur) :**
- Stationnement sur la voie publique en zone payante : de l'ordre de 1 à 2 DT pour un stationnement de courte durée (à confirmer)
- Somme habituellement remise à un gardien de parking : de l'ordre de 1 à 3 DT selon la ville et la durée (à confirmer)
- Parking couvert ou de surface payant : de l'ordre de 1 à 3 DT par heure, avec des forfaits à la journée plus avantageux (à confirmer)
- Forfait journée dans un parking couvert : de l'ordre de 5 à 15 DT (à confirmer)

**À savoir :**
- Ces fourchettes sont indicatives et peuvent ne plus correspondre aux tarifs pratiqués ; le tarif exact d'un lieu se vérifie sur place, sur le panneau d'affichage du parking ou auprès de l'agent
- Les parkings d'aéroport appliquent en général un tarif horaire et des forfaits par journée entamée, plus élevés que les parkings de centre-ville (à confirmer)

## Contravention ou mise en fourrière

**En cas de contravention (amende de stationnement) :**
- L'avis de contravention est en général laissé sur le pare-brise ou dressé par un agent
- Le paiement s'effectue auprès de la recette des finances (perception) dont dépend le lieu de l'infraction ; des solutions de paiement en ligne ou par application peuvent exister (à confirmer)
- Une amende non réglée dans le délai indiqué peut être majorée (à confirmer)
- Conserver le reçu de paiement

**Documents utiles pour toute démarche :**
- Carte d'identité nationale (CIN) du conducteur ou du propriétaire
- Carte grise du véhicule
- Attestation d'assurance en cours de validité
- L'avis de contravention s'il a été laissé sur le véhicule

**En cas de mise en fourrière (véhicule enlevé) :**
1. Vérifier d'abord que le véhicule a bien été enlevé et non volé : se renseigner au poste de police ou de la garde nationale de la zone, ou auprès de la municipalité
2. Demander où se trouve la fourrière qui détient le véhicule et quelles sont ses heures d'ouverture
3. Se présenter avec les documents ci-dessus, au nom du propriétaire ou avec une procuration (à confirmer)
4. Régler la contravention, les frais d'enlèvement et les frais de gardiennage, qui augmentent pour chaque journée de garde (à confirmer)
5. Récupérer le véhicule et vérifier son état avant de quitter la fourrière

**Contester :** une contravention peut en principe être contestée auprès du service qui l'a établie ; la procédure exacte et les délais sont à vérifier sur place (à confirmer).

**Délai :** la récupération du véhicule se fait en général le jour même, si le dossier est complet et la fourrière ouverte (à confirmer).

**Coût :** les frais d'enlèvement et de gardiennage s'ajoutent au montant de l'amende ; les montants dépendent de la ville et du type de véhicule (à confirmer).

## Parkings couverts et parkings privés

**Où en trouver :** centres commerciaux, grandes surfaces, aéroports, gares, hôpitaux, hôtels et certains immeubles de bureaux disposent de parkings réservés à leurs visiteurs ou ouverts au public.

**Fonctionnement :**
- Accès par barrière avec ticket ou badge ; le ticket sert au calcul du temps de stationnement
- Paiement à la caisse avant de reprendre le véhicule, ou directement à la sortie selon l'installation
- La durée facturée est en général calculée par heure entamée, avec parfois des forfaits (à confirmer)

**Centres commerciaux :** certains offrent une période de stationnement gratuite à leurs clients, parfois conditionnée à un achat ou à la validation du ticket à un point d'accueil. Cette pratique varie d'un établissement à l'autre (à confirmer).

**Aéroports :** les parkings sont en général organisés en zones (dépose-minute de courte durée, parking de longue durée). Le tarif dépend de la durée totale et de la zone choisie (à confirmer).

**À savoir :**
- Les horaires d'ouverture varient : certains parkings ferment la nuit, ce qui peut empêcher de récupérer le véhicule
- Vérifier le tarif affiché à l'entrée avant d'entrer
- Ne pas laisser d'objets de valeur visibles dans le véhicule
- La responsabilité du parking en cas de dommage ou de vol dépend des conditions affichées par l'exploitant (à confirmer)

## Limites de ce que cet agent peut savoir

**Cet assistant n'a pas accès à des données en temps réel.** Sa base de connaissances contient uniquement des informations générales et stables sur le fonctionnement du stationnement.

**Informations que cet assistant ne peut PAS fournir :**
- **Disponibilité de places :** il ne peut pas savoir s'il reste de la place dans une rue, sur une avenue ou dans un parking précis, ni maintenant ni à un autre moment
- **Tarif exact d'un lieu précis :** il ne connaît que des fourchettes indicatives générales ; le tarif d'un parking ou d'une zone donnée se vérifie sur place
- **Affluence et trafic :** il ne connaît ni l'état du trafic, ni l'affluence d'un quartier à un moment donné
- **Situation d'une rue :** travaux, fermeture, changement de réglementation, événement en cours ou zone devenue interdite au stationnement
- **Statut d'un véhicule :** il ne peut pas savoir si un véhicule a été verbalisé, enlevé, ni dans quelle fourrière il se trouve
- **Horaires et fonctionnement d'un établissement précis :** heures d'ouverture d'un parking, d'une fourrière ou d'un service municipal

**Comment obtenir ces informations :**
- Se rendre sur place ou demander à une personne présente sur le lieu
- Pour une zone payante : lire les panneaux et l'affichage de la zone, ou demander à l'agent présent
- Pour un parking privé : consulter l'affichage à l'entrée ou s'adresser à l'accueil de l'établissement
- Pour un véhicule enlevé ou une contravention : s'adresser au poste de police de la zone ou à la municipalité
- Pour le trafic et la disponibilité en temps réel : utiliser une application de navigation, qui dispose de données en direct
