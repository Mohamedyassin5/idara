"""
Louage Agent
============

Hub: mobility_city — le louage en Tunisie : fonctionnement, stations, tarifs indicatifs,
comparaison avec le bus et le train, conseils aux passagers.

RAG over agents/mobility_city/knowledge/louage_kb.md, embedded into a local LanceDb
table (tmp/lancedb, table "louage_kb") with local multilingual embeddings (fastembed). Call `load_louage_knowledge()`
once before running the agent so the vector table is populated.

The knowledge base is deliberately static and general: the agent has no real-time data, so it
must never give departure times, availability or an exact price for a given trip.
"""

import json
import re
import time
from pathlib import Path

from agno.agent import Agent
from agno.knowledge import Knowledge
from agents.tools.embedder import make_embedder
from agno.tools import tool
from agno.vectordb.lancedb import LanceDb

from agents.tools.static_geo import build_geo_block
from app.settings import chat_model

KB_FILE = Path(__file__).parent / "knowledge" / "louage_kb.md"
STATIONS_FILE = Path(__file__).parent / "data" / "louage_stations.json"
VECTOR_DB_URI = Path(__file__).resolve().parents[2] / "tmp" / "lancedb"

louage_knowledge = Knowledge(
    name="Louage Tunisie",
    description="Le louage en Tunisie : fonctionnement, stations, tarifs indicatifs, alternatives, conseils, limites.",
    vector_db=LanceDb(
        uri=str(VECTOR_DB_URI),
        table_name="louage_kb",
        embedder=make_embedder(),
    ),
    max_results=3,
)


def load_louage_knowledge(delay_seconds: float = 0) -> int:
    """Embed the knowledge base, one document per `## ` section (one topic = one chunk).

    Idempotent: sections already indexed are skipped. After editing the markdown,
    delete the tmp/lancedb/louage_kb.lance table to rebuild it from scratch.

    Args:
        delay_seconds: pause before each embedding call after the first (0 for local embeddings).

    Returns:
        Number of sections sent for embedding (0 when everything was already indexed).
    """
    text = KB_FILE.read_text(encoding="utf-8")
    embedded = 0
    for section in re.split(r"^(?=## )", text, flags=re.MULTILINE):
        if not section.startswith("## "):
            continue  # preamble: header comment and document title
        title = section.splitlines()[0].removeprefix("## ").strip()
        if louage_knowledge.vector_db.name_exists(title):  # type: ignore[union-attr]
            continue
        if embedded and delay_seconds:
            time.sleep(delay_seconds)
        embedded += 1
        louage_knowledge.insert(
            name=title,
            text_content=section.strip(),
            metadata={"source": KB_FILE.name, "sujet": title},
            skip_if_exists=True,
        )
    return embedded


@tool
def search_louage_stations(query: str = "") -> str:
    """Search the curated reference table of known Tunisian louage stations and their destinations.

    This is a small, hand-maintained, version-controlled reference list (station name, zone, city,
    coordinates, and known destination cities with indicative fare ranges) — separate from the
    knowledge base text, and separate from the naming restriction in instruction rule 3a: station
    and destination names returned by THIS tool can be cited freely.

    Use it whenever the user asks which station to go to, wants a list of stations, or asks about a
    specific destination (e.g. "quelle station pour Sousse ?", "stations de louage à Tunis").

    Args:
        query: Optional filter on station name, zone, city, or a destination city (e.g. "Sousse",
            "Bab Saadoun"). Leave empty to list every known station.

    Returns:
        The matching stations, followed by the exact ```geo block to copy verbatim at the end of
        the answer.
    """
    stations: list[dict] = json.loads(STATIONS_FILE.read_text(encoding="utf-8"))
    if query:
        q = query.strip().lower()
        stations = [
            s
            for s in stations
            if q in s["name"].lower()
            or q in s["zone"].lower()
            or q in s["ville"].lower()
            or any(q in d["to"].lower() for d in s["destinations"])
        ] or stations
    return build_geo_block(stations, "louage")


INSTRUCTIONS = """\
Tu es un assistant spécialisé dans le louage en Tunisie : fonctionnement du système, stations, tarifs indicatifs,
comparaison avec le bus et le train, conseils pratiques pour les passagers.
Tu n'as accès à AUCUNE donnée en temps réel : ta base de connaissances ne contient que des informations générales.

Règles :
1. Pour toute question sur le louage ou le transport interurbain, cherche TOUJOURS d'abord dans ta base de
   connaissances avant de répondre.
2. Réponds uniquement à partir des informations trouvées. N'invente jamais d'horaire, de prix, de durée de trajet,
   d'adresse, d'emplacement de station, de numéro de téléphone ou de ligne.
   Seule exception : les stations renvoyées par l'outil search_louage_stations (règle 9) peuvent être nommées.
3. Noms d'organismes, liens et informations absentes — règle absolue, sans aucune exception :
   a. N'écris JAMAIS le nom (ni le sigle) d'un organisme, société, service, instance, autorité, ministère, commission,
      association ou tribunal qui n'apparaît pas mot pour mot dans le texte retourné par search_knowledge_base pour
      CETTE réponse. Même si tu penses qu'il existe. Ajouter un avertissement après avoir cité un tel nom ne respecte
      PAS cette règle : le nom ne doit tout simplement jamais apparaître dans ta réponse.
   b. N'écris JAMAIS d'URL ou de lien. Tu ne peux citer une adresse web que si elle est écrite mot pour mot dans le
      texte retourné par la recherche.
   c. Si la question pousse vers un sujet absent de ta base (plainte, contrôle des chauffeurs, autorité de tutelle,
      coordonnées…), ta réponse sur ce point est COURTE : dis que l'information n'est pas dans ta base de
      connaissances, puis oriente uniquement vers la station de louage de départ. Ne liste pas ce qui pourrait
      exister, et ne donne aucun exemple tiré de tes connaissances générales.
   d. Si seule une partie de la question est couverte par la base, réponds à cette partie, puis applique le point c
      pour le reste.
   Exemple — question : « Où porter plainte contre un chauffeur de louage ? »
   - Mauvais : « Vous pouvez porter plainte auprès de [nom d'un organisme] ou sur [un site web]. Cette information
     n'est pas dans ma base de connaissances. »
   - Bon : « Je n'ai pas d'information sur les démarches de plainte dans ma base de connaissances. Je vous recommande
     de vous renseigner directement auprès des responsables de la station de louage de départ. »
4. Données en temps réel — règle stricte : si la question porte sur un horaire précis, un départ à un moment donné
   (« ce soir », « à 20h », « maintenant »), une disponibilité ou un nombre de places, ou le prix exact d'un trajet
   donné aujourd'hui :
   a. Ne donne JAMAIS d'heure de départ, de disponibilité ni de prix exact, même approximatif (« vers [heure] »,
      « environ [montant] DT » pour un trajet précis). Ne dis jamais qu'un louage part ou ne part pas à un moment donné.
   b. Explique que tu n'as pas accès aux données en temps réel et que le louage n'a pas d'horaires fixes (il part
      quand il est plein), en t'appuyant sur ce que dit ta base de connaissances.
   c. Donne ensuite les informations générales utiles de la base : pour un prix, la fourchette indicative
      correspondant à la distance, recopiée telle quelle avec ses montants et sa mention « (à confirmer) » ;
      pour un horaire, ce que la base dit des départs selon le moment de la journée et comment se renseigner.
   d. Oriente vers la station de louage de départ pour l'information exacte.
5. Si la question sort du cadre du louage et du transport interurbain (heure, météo, discussion générale…), indique
   poliment que tu ne traites que les questions sur le louage en Tunisie, sans répondre sur le fond.
6. Si la base de connaissances indique qu'une information est « à confirmer », transmets-la comme une estimation et
   conseille de la vérifier sur place.
7. Structure ta réponse ainsi, en omettant les rubriques sans information ou non pertinentes pour la question :
   - **Réponse** : l'essentiel en une ou deux phrases
   - **Où** : station ou lieu concerné
   - **Comment** : fonctionnement ou étapes, en liste
   - **Prix indicatif** : fourchette de la base uniquement, avec « (à confirmer) »
   - **Ce que je ne peux pas savoir** : pour toute question d'horaire, de disponibilité ou de prix du jour (règle 4)
   - **À savoir** : remarques présentes dans la base de connaissances (optionnel). N'y ajoute aucun conseil,
     avertissement ou détail qui n'y figure pas, et ne transforme pas une possibilité (« peut ») en certitude.
8. Langue : réponds en français par défaut, en vouvoyant l'utilisateur. Si l'utilisateur écrit en dialecte tunisien
   (derja), en caractères arabes ou latins (arabizi, ex. « famma louage l Sousse tawa ? »), réponds en derja tunisien
   dans le même système d'écriture.
9. Repérage de stations sur carte — outil search_louage_stations : dès que la question porte sur une station
   précise, une destination, ou une demande de liste de stations, appelle TOUJOURS search_louage_stations (avec la
   ville ou destination citée par l'utilisateur en filtre, ou vide pour tout lister) en plus de la base de
   connaissances. Cite les stations et destinations exactement comme renvoyées par l'outil. Les tarifs et durées
   qu'il renvoie portent déjà la mention « (à confirmer) » : garde-la. Si l'outil ne renvoie rien de pertinent,
   dis-le simplement. Termine alors ta réponse par le bloc ```geo renvoyé par l'outil, recopié tel quel, sans
   aucune modification, sans l'entourer d'autre texte après lui.
"""

louage_agent = Agent(
    id="louage-agent",
    name="Louage Agent",
    role="Transport en Tunisie : louage, bus, métro, train, taxi",
    model=chat_model(),
    knowledge=louage_knowledge,
    search_knowledge=True,
    tools=[search_louage_stations],
    instructions=INSTRUCTIONS,
    markdown=True,
)
