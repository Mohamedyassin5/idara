# WhatsApp

Users talk to the agents from WhatsApp with slash commands:

| Message | Effect |
|---|---|
| `/menu` or `/` | list of agents |
| `/parking` | select the agent; the next messages go to it |
| `/louage station pour Sousse ?` | select the agent and ask in one message |
| `/stop` | end the conversation and start a fresh one |
| a location pin | forwarded to the active agent as "Ma position : latitude …, longitude …" |

Commands: `/bureaucratie` (`/admin`), `/steg` (`/sonede`), `/entrepreneuriat`, `/louage`, `/parking`,
`/souk` (`/marche`), `/bac`, `/job` (`/emploi`), `/immobilier` (`/immo`). Agent answers keep their bold text, and
map results arrive as Google Maps links.

## Meta setup (WhatsApp Cloud API)

1. https://developers.facebook.com > **Create app** > type *Business* > add the **WhatsApp** product.
2. WhatsApp > **API Setup**: note the **Phone number ID** and the **temporary access token** (valid 24 h).
   For a token that does not expire: Business Settings > System users > create one, assign the app,
   generate a token with `whatsapp_business_messaging` and `whatsapp_business_management`.
3. App settings > Basic: copy the **App secret**.
4. Choose any string as the **verify token** (for example a long random one).
5. Set these on the backend (Azure: Environment variables; local: `.env`):
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_APP_SECRET`
   - `WHATSAPP_VERIFY_TOKEN`
6. WhatsApp > **Configuration** > Webhook: callback URL `https://<backend>.azurewebsites.net/whatsapp/webhook`,
   verify token from step 4 > **Verify and save**, then subscribe to the **messages** field.
7. API Setup > add your own phone as a recipient, send a message to the test number: `/menu`.

## Alternative: secret in the callback URL

If Meta's app secret is not available, set `WHATSAPP_WEBHOOK_SECRET` (a random string of at least 24 characters,
letters and digits) and use `https://<backend>.azurewebsites.net/whatsapp/webhook/<that string>` as the callback URL.
The verify token still has to match. The secret in the URL is what authenticates deliveries, so keep it private.

## Limits to know

- With Meta's **test number**, only up to 5 recipients you add by hand can message the bot. To let *any* user
  write to it you need your own WhatsApp Business phone number, a verified Meta business, and the app set to Live.
- Meta only lets the bot send free-form messages within 24 h of the user's last message, which fits this flow
  (the user always writes first).
- Agents take 30-90 s. The webhook answers Meta immediately and sends the reply afterwards.
- The webhook is public by design; it is protected by Meta's HMAC signature (`WHATSAPP_APP_SECRET`) and refuses
  every request when that secret is not set.
- The chosen agent per user is kept in memory: a backend restart only sends users back to the menu.

## Test without Meta

`python scripts/test_whatsapp.py` checks command parsing, formatting, signatures and duplicate deliveries.
