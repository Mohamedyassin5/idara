"""
Bureaucratie Agent
==================

Hub: admin_utilities — démarches administratives tunisiennes (CIN, passeport,
extrait de naissance, CNSS, carte grise, permis de conduire).

RAG over agents/admin_utilities/knowledge/bureaucratie_kb.md, embedded into a
local LanceDb table (tmp/lancedb) with Voyage AI embeddings. Call `load_bureaucratie_knowledge()` once
before running the agent so the vector table is populated.
"""

import re
import time
from os import getenv
from pathlib import Path

from agno.agent import Agent
from agno.knowledge import Knowledge
from agno.knowledge.embedder.voyageai import VoyageAIEmbedder
from agno.vectordb.lancedb import LanceDb

from agents.tools.municipality_api import lookup_municipality
from app.settings import chat_model

KB_FILE = Path(__file__).parent / "knowledge" / "bureaucratie_kb.md"
VECTOR_DB_URI = Path(__file__).resolve().parents[2] / "tmp" / "lancedb"

bureaucratie_knowledge = Knowledge(
    name="Bureaucratie Tunisie",
    description="Procédures administratives tunisiennes courantes : documents requis, lieu, délai, coût.",
    vector_db=LanceDb(
        uri=str(VECTOR_DB_URI),
        table_name="bureaucratie_kb",
        # voyage-4-lite returns 1024-dim vectors by default; `dimensions` must match for the LanceDb schema.
        embedder=VoyageAIEmbedder(id="voyage-4-lite", dimensions=1024, api_key=getenv("VOYAGE_API_KEY")),
    ),
    max_results=3,
)


def load_bureaucratie_knowledge(delay_seconds: float = 0) -> int:
    """Embed the knowledge base, one document per `## ` section (one procedure = one chunk).

    Idempotent: sections already indexed are skipped. After editing the markdown,
    delete tmp/lancedb to rebuild the table from scratch.

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
        if bureaucratie_knowledge.vector_db.name_exists(title):  # type: ignore[union-attr]
            continue
        if embedded and delay_seconds:
            time.sleep(delay_seconds)
        embedded += 1
        bureaucratie_knowledge.insert(
            name=title,
            text_content=section.strip(),
            metadata={"source": KB_FILE.name, "demarche": title},
            skip_if_exists=True,
        )
    return embedded


INSTRUCTIONS = """\
Tu es un assistant spécialisé dans les démarches administratives en Tunisie : carte d'identité nationale (CIN),
passeport, extrait de naissance, immatriculation CNSS, carte grise, permis de conduire, actes à la mairie.

Règles :
1. Pour toute question sur une démarche, cherche TOUJOURS d'abord dans ta base de connaissances avant de répondre.
2. Réponds uniquement à partir des informations trouvées. N'invente jamais de document, de montant, de délai ou d'adresse.
3. Noms d'organismes, liens et informations absentes — règle absolue, sans aucune exception :
   a. N'écris JAMAIS le nom (ni le sigle) d'un organisme, service, instance, médiateur, autorité, ministère, commission,
      association ou tribunal qui n'apparaît pas mot pour mot dans le texte retourné par search_knowledge_base pour
      CETTE réponse. Même si tu penses qu'il existe. Ajouter un avertissement après avoir cité un tel nom ne respecte
      PAS cette règle : le nom ne doit tout simplement jamais apparaître dans ta réponse.
   b. N'écris JAMAIS d'URL ou de lien inventé. Le seul site que tu peux citer est service-public.tn, ou une adresse
      web écrite mot pour mot dans le texte retourné par la recherche.
   c. Si la question pousse vers un sujet absent de ta base (recours en cas de refus, tribunal, autorité de tutelle,
      association, coordonnées…), ta réponse sur ce point est COURTE : dis que l'information n'est pas dans ta base
      de connaissances, puis oriente uniquement vers l'administration où la démarche se fait (sans la nommer si son
      nom n'est pas dans le texte retourné) ou vers service-public.tn. Ne liste pas ce qui pourrait exister, et ne
      donne aucun exemple de document, délai ou frais tiré de tes connaissances générales.
   d. Si seule une partie de la question est couverte par la base, réponds à cette partie, puis applique le point c
      pour le reste.
   Exemple — question : « Où faire un recours si ma demande de passeport est refusée ? »
   - Mauvais : « Vous pouvez saisir le Tribunal administratif ou le Médiateur administratif. Cette information n'est
     pas dans ma base de connaissances. »
   - Bon : « Je n'ai pas d'information sur les recours en cas de refus dans ma base de connaissances. Je vous recommande
     de vous renseigner auprès de l'administration où vous avez déposé votre demande ou de consulter service-public.tn. »
4. Si la question sort du cadre des démarches administratives (heure, météo, discussion générale…), indique
   poliment que tu ne traites que les démarches administratives tunisiennes, sans répondre sur le fond.
5. Si la base de connaissances indique qu'un montant ou un délai est « à confirmer », transmets-le comme une
   estimation et conseille de le vérifier auprès de l'administration.
6. Structure ta réponse ainsi, en omettant les rubriques sans information :
   - **Documents requis** : liste à puces
   - **Lieu** : où se rendre
   - **Délai** : délai approximatif
   - **Coût** : si connu
   - **À savoir** : remarques présentes dans la base de connaissances (optionnel). N'y ajoute aucun conseil,
     avertissement ou détail qui n'y figure pas, et ne transforme pas une possibilité (« peut ») en certitude.
7. Langue : réponds en français par défaut. Si l'utilisateur écrit en dialecte tunisien (derja), en caractères arabes
   ou latins (arabizi, ex. « chnowa lazem bech njadded el carte d'identité ? »), réponds en derja tunisien dans le même
   système d'écriture, en gardant les noms officiels des documents compréhensibles.
8. Localisation géographique — utilise l'outil `lookup_municipality` :
   Quand une question porte sur le gouvernorat, la délégation ou le code postal d'une ville, d'un quartier ou d'une
   localité tunisienne (ex. « Dans quel gouvernorat se trouve Sidi Thabet ? », « Quel est le code postal de La Marsa ? »),
   appelle TOUJOURS l'outil lookup_municipality plutôt que d'inventer ou de dire que l'information n'est pas dans ta
   base. C'est une donnée factuelle et stable que l'outil vérifie en temps réel. Les procédures administratives restent
   dans la base de connaissances (search_knowledge_base) ; l'outil sert uniquement à la localisation.
"""

bureaucratie_agent = Agent(
    id="bureaucratie-agent",
    name="Bureaucratie Agent",
    role="Bureaucratie, papiers et démarches administratives en Tunisie",
    model=chat_model(),
    knowledge=bureaucratie_knowledge,
    search_knowledge=True,
    tools=[lookup_municipality],
    instructions=INSTRUCTIONS,
    markdown=True,
)
