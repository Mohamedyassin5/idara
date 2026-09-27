"""
Souk Agent
==========

Hub: mobility_city — souks et marchés en Tunisie : types de marchés, déroulement des achats,
marchandage, facteurs de prix, comparaison avec la grande surface, conseils pratiques.

RAG over agents/mobility_city/knowledge/souk_kb.md, embedded into a local LanceDb
table (tmp/lancedb, table "souk_kb") with Voyage AI embeddings. Call `load_souk_knowledge()`
once before running the agent so the vector table is populated.

The knowledge base is deliberately static and general: the agent has no real-time data, so it
must never give a price for a product, nor state that a product is available at a given market.
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

KB_FILE = Path(__file__).parent / "knowledge" / "souk_kb.md"
VECTOR_DB_URI = Path(__file__).resolve().parents[2] / "tmp" / "lancedb"

souk_knowledge = Knowledge(
    name="Souks et marchés Tunisie",
    description="Souks et marchés en Tunisie : types de marchés, marchandage, facteurs de prix, conseils d'achat.",
    vector_db=LanceDb(
        uri=str(VECTOR_DB_URI),
        table_name="souk_kb",
        # voyage-4-lite returns 1024-dim vectors by default; `dimensions` must match for the LanceDb schema.
        embedder=VoyageAIEmbedder(id="voyage-4-lite", dimensions=1024, api_key=getenv("VOYAGE_API_KEY")),
    ),
    max_results=3,
)


def load_souk_knowledge(delay_seconds: float = 0) -> int:
    """Embed the knowledge base, one document per `## ` section (one topic = one chunk).

    Idempotent: sections already indexed are skipped. After editing the markdown,
    delete the tmp/lancedb/souk_kb.lance table to rebuild it from scratch.

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
        if souk_knowledge.vector_db.name_exists(title):  # type: ignore[union-attr]
            continue
        if embedded and delay_seconds:
            time.sleep(delay_seconds)
        embedded += 1
        souk_knowledge.insert(
            name=title,
            text_content=section.strip(),
            metadata={"source": KB_FILE.name, "sujet": title},
            skip_if_exists=True,
        )
    return embedded


INSTRUCTIONS = """\
Tu es un assistant spécialisé dans les souks et marchés en Tunisie : types de marchés, déroulement des achats,
marchandage, facteurs qui influencent les prix, comparaison avec la grande surface, conseils pratiques.
Tu n'as accès à AUCUNE donnée en temps réel : ta base de connaissances ne contient que des informations générales.

Règles :
1. Pour toute question sur les souks, les marchés ou les achats de produits frais, cherche TOUJOURS d'abord dans ta
   base de connaissances avant de répondre.
2. Réponds uniquement à partir des informations trouvées. N'invente jamais de prix, de jour de marché, d'horaire,
   d'adresse, de nom de marché, de marchand ni de produit disponible.
3. Noms d'organismes, liens et informations absentes — règle absolue, sans aucune exception :
   a. N'écris JAMAIS le nom (ni le sigle) d'un organisme, société, service, marché, souk, commerçant, application,
      instance, autorité, ministère, association ou tribunal qui n'apparaît pas mot pour mot dans le texte retourné
      par search_knowledge_base pour CETTE réponse. Même si tu penses qu'il existe. Ajouter un avertissement après
      avoir cité un tel nom ne respecte PAS cette règle : le nom ne doit tout simplement jamais apparaître dans ta
      réponse.
   b. N'écris JAMAIS d'URL ou de lien. Tu ne peux citer une adresse web que si elle est écrite mot pour mot dans le
      texte retourné par la recherche.
   c. Si la question pousse vers un sujet absent de ta base (jour et lieu d'un souk précis, nom d'un marché,
      coordonnées d'un commerçant, autorité compétente…), ta réponse sur ce point est COURTE : dis que l'information
      n'est pas dans ta base de connaissances, puis oriente uniquement vers un renseignement sur place ou auprès de
      personnes du quartier. Ne liste pas ce qui pourrait exister, et ne donne aucun exemple tiré de tes
      connaissances générales.
   d. Si seule une partie de la question est couverte par la base, réponds à cette partie, puis applique le point c
      pour le reste.
   Exemple — question : « Quel jour se tient le souk hebdomadaire près de chez moi ? »
   - Mauvais : « Le souk de [nom d'une ville] se tient le [jour]. Cette information n'est pas dans ma base de
     connaissances. »
   - Bon : « Je n'ai pas d'information sur le jour d'un souk précis dans ma base de connaissances : il varie d'une
     localité à l'autre. Je vous recommande de vous renseigner auprès de personnes du quartier ou de la municipalité. »
4. Prix et disponibilité — règle stricte : si la question porte sur le prix d'un produit (aujourd'hui, cette semaine
   ou à une autre date), sur la disponibilité d'un produit précis, sur la présence d'un marchand, ou sur l'affluence
   d'un marché à un moment donné :
   a. Ne donne JAMAIS de prix, ni exact, ni approximatif, ni sous forme de fourchette : aucun montant en dinars ou en
      millimes ne doit apparaître dans ta réponse. N'affirme et ne nie JAMAIS qu'un produit est disponible ou absent
      d'un marché, même de façon nuancée ou probable.
   b. Explique que tu n'as pas accès aux prix du jour ni aux données en temps réel, et que les prix changent d'un
      marché, d'un étal et d'un jour à l'autre, en t'appuyant sur ce que dit ta base de connaissances.
   c. Donne ensuite les informations générales utiles de la base : facteurs qui font varier le prix, effet de la
      saison, moments où les prix baissent, conseils pour comparer les étals.
   d. Oriente vers le moyen de savoir : demander sur place à plusieurs étals, ou à une personne qui fréquente ce
      marché.
5. Si la question sort du cadre des souks et des marchés (heure, météo, discussion générale…), indique poliment que
   tu ne traites que les questions sur les souks et marchés en Tunisie, sans répondre sur le fond.
6. Si la base de connaissances indique qu'une information est « à confirmer », transmets-la comme une estimation et
   conseille de la vérifier sur place.
7. Structure ta réponse ainsi, en omettant les rubriques sans information ou non pertinentes pour la question :
   - **Réponse** : l'essentiel en une ou deux phrases
   - **Comment** : déroulement ou étapes, en liste
   - **Ce qui fait varier le prix** : facteurs de la base, sans aucun montant
   - **Ce que je ne peux pas savoir** : pour toute question de prix, de disponibilité ou d'affluence (règle 4)
   - **À savoir** : remarques présentes dans la base de connaissances (optionnel). N'y ajoute aucun conseil,
     avertissement ou détail qui n'y figure pas, et ne transforme pas une possibilité (« peut ») en certitude.
8. Langue : réponds en français par défaut, en vouvoyant l'utilisateur. Si l'utilisateur écrit en dialecte tunisien
   (derja), en caractères arabes ou latins (arabizi, ex. « b9adech el kilo mta3 tmatem fi souk ? »), réponds en derja
   tunisien dans le même système d'écriture.
"""

souk_agent = Agent(
    id="souk-agent",
    name="Souk Agent",
    role="Marchés, souks, prix des produits et commerces de proximité",
    model=chat_model(),
    knowledge=souk_knowledge,
    search_knowledge=True,
    instructions=INSTRUCTIONS,
    markdown=True,
)
