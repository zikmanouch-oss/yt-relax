# yt-relax

Chaîne YouTube de sons de pluie, entièrement automatique et gratuite.

- **Vidéo** : vrais clips de pluie Pixabay (`src/sources.py`), enchaînés en fondus dans une séquence de 15 min qui boucle sans raccord visible (`src/footage.py`).
- **Son** : vrais enregistrements CC0 de Freesound, mixés en continu avec variations d'intensité et tonnerre lointain, sans répétition sur 8 h (`src/soundscape.py`).
- **Miniature** : image tirée de la vidéo + texte (`src/visual.py`).
- **Publication** : API YouTube Data v3 (`src/upload.py`).
- **Planning** : GitHub Actions, lundi / mercredi / vendredi (`.github/workflows/publish.yml`).

## Réglages

Tout se règle dans `config.yaml` : durée, ambiances (fenêtre, forêt, ville, toit), tonnerre, confidentialité.

## Lancer un test

Onglet **Actions** → **Publier une vidéo pluie** → **Run workflow** (mode test coché).
Une vidéo de 3 minutes est générée et téléchargeable dans l'onglet du run (« apercu »), sans publication.

## Secrets nécessaires (Settings → Secrets and variables → Actions)

| Nom | Contenu |
|---|---|
| `PIXABAY_API_KEY` | Clé API Pixabay (vidéos) |
| `FREESOUND_API_KEY` | Clé API Freesound (sons) |
| `YT_CLIENT_ID` | ID client OAuth Google |
| `YT_CLIENT_SECRET` | Secret client OAuth Google |
| `YT_REFRESH_TOKEN` | Jeton d'actualisation de la chaîne |

Sans les clés Pixabay/Freesound rien ne tourne ; sans les clés YouTube, seul le mode test fonctionne.

## Local

```bash
pip install -r requirements.txt
python -m src.main --hours 0.05 --dry-run
```
