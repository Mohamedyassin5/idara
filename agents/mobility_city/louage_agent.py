"""
Louage Agent
============

Hub: mobility_city — le louage en Tunisie : fonctionnement, stations, tarifs indicatifs,
comparaison avec le bus et le train, conseils aux passagers.

RAG over agents/mobility_city/knowledge/louage_kb.md, embedded into a local LanceDb
table (tmp/lancedb, table "louage_kb") with Voyage AI embeddings. Call `load_louage_knowledge()`
once before running the agent so the vector table is populated.

The knowledge base is deliberately static and general: the agent has no real-time data, so it
must never give departure times, availability or an exact price for a given trip.
"""

import re
import time
from os import getenv
from pathlib import Path

from agno.agent import Agent
from agno.knowledge import Knowledge
from agno.knowledge.embedder.voyageai import VoyageAIEmbedder
from agno.vectordb.lancedb import LanceDb

from app.settings import chat_model

KB_FILE = Path(__file__).parent / "knowledge" / "louage_kb.md"
VECTOR_DB_URI = Path(__file__).resolve().parents[2] / "tmp" / "lancedb"

louage_knowledge = Knowledge(
    name="Louage Tunisie",
    description="Le louage en Tunisie : fonctionnement, stations, tarifs indicatifs, alternatives, conseils, limites.",
    vector_db=LanceDb(
        uri=str(VECTOR_DB_URI),
        table_name="louage_kb",
        # voyage-4-lite returns 1024-dim vectors by default; `dimensions` must match for the LanceDb schema.
        embedder=VoyageAIEmbedder(id="voyage-4-lite", dimensions=1024, api_key=getenv("VOYAGE_API_KEY")),
    ),
    max_results=3,
)


def load_louage_knowledge(delay_seconds: float = 0) -> int:
    """Embed the knowledge base, one document per `## ` section (one topic = one chunk).

    Idempotent: sections already indexed are skipped. After editing the markdown,
    delete the tmp/lancedb/louage_kb.lance table to rebuild it from scratch.

    Args:
        delay_seconds: pause before each embedding call after the first. Each section costs
            one Voyage request; the free tier without a payment method allows 3 requests/minute,
            so pass ~21 there. A section that fails to embed is only logged by agno, not raised,
            and is simply retried on the next call.

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


INSTRUCTIONS = """\
Tu es un assistant spécialisé dans le louage en Tunisie : fonctionnement du système, stations, tarifs indicatifs,
comparaison avec le bus et le train, conseils pratiques pour les passagers.
Tu n'as accès à AUCUNE donnée en temps réel : ta base de connaissances ne contient que des informations générales.

Règles :
1. Pour toute question sur le louage ou le transport interurbain, cherche TOUJOURS d'abord dans ta base de
   connaissances avant de répondre.
2. Réponds uniquement à partir des informations trouvées. N'invente jamais d'horaire, de prix, de durée de trajet,
   d'adresse, d'emplacement de station, de numéro de téléphone ou de ligne.
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
"""

louage_agent = Agent(
    id="louage-agent",
    name="Louage Agent",
    role="Transport en Tunisie : louage, bus, métro, train, taxi",
    model=chat_model(),
    knowledge=louage_knowledge,
    search_knowledge=True,
    instructions=INSTRUCTIONS,
    markdown=True,
)
