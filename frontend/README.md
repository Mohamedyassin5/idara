# Idara — front office (Angular)

Interface web « à la tunisienne » pour l'orchestrateur AgentOS : accueil par domaines, une page dédiée par
agent (thème, questions types, formulaire rapide), interface en FR / AR (RTL) / EN.

## Lancer

Backend (depuis la racine du repo) :

```sh
python -m app.main            # écoute sur http://localhost:7777
# ou: docker compose up -d    # écoute sur http://localhost:8000
```

Frontend :

```sh
cd frontend
npm install
npm start
```

Ouvrir http://localhost:4200. Le serveur de dev proxifie `/api/*` vers le backend (`proxy.conf.js`) : il détecte au
démarrage si AgentOS répond sur le port 8000 (Docker) ou 7777 (`python -m app.main`), donc **démarrez le backend
avant `npm start`** (ou relancez `npm start` après). Pour forcer une adresse : `BACKEND_URL=http://localhost:7777
npm start` (PowerShell : `$env:BACKEND_URL="http://localhost:7777"; npm start`). Aucun changement de CORS n'est
nécessaire.

## Fonctionnement

- Seul le `master-orchestrator` est exposé par AgentOS : chaque page envoie ses questions à
  `POST /teams/master-orchestrator/runs` (non streamé). Sur une page d'agent, un court indice
  `[Domaine : …]` est ajouté au message pour orienter le routage ; la page affiche l'agent qui a réellement
  répondu (lu dans `member_responses`) et signale s'il diffère de celui de la page.
- `src/app/core/agents.ts` : catalogue des 4 hubs / 11 agents (textes FR/AR/EN, questions types, formulaires).
  Les `backendId` et `hubId` doivent rester alignés sur `agents/**/*_agent.py` et `agents/hubs.py`.
- `src/app/core/i18n.ts` : textes de l'interface et bascule de langue (`dir="rtl"` en arabe).
- Le nom affiché (« Idara ») est la clé `appName` de `i18n.ts`.

## Commandes

```sh
npm test          # tests unitaires (vitest)
npm run build     # build de production
```
