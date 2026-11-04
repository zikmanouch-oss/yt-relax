# yt-relax

Chaîne YouTube de sons de pluie, entièrement automatique et gratuite.

- **Son** : pluie synthétisée par le code (`src/audio.py`) — aucun droit d'auteur, boucle sans coupure.
- **Image** : scène de pluie nocturne générée (`src/visual.py`), miniature avec texte.
- **Montage** : ffmpeg, image fixe + son (`src/render.py`).
- **Publication** : API YouTube Data v3 (`src/upload.py`).
- **Planning** : GitHub Actions, lundi / mercredi / vendredi (`.github/workflows/publish.yml`).

## Réglages

Tout se règle dans `config.yaml` : durée, confidentialité, variantes (intensité, tonnerre).

## Lancer un test

Onglet **Actions** → **Publier une vidéo pluie** → **Run workflow** (mode test coché).
Une vidéo de 3 minutes est générée et téléchargeable dans l'onglet du run (« apercu »), sans publication.

## Secrets nécessaires (Settings → Secrets and variables → Actions)

| Nom | Contenu |
|---|---|
| `YT_CLIENT_ID` | ID client OAuth Google |
| `YT_CLIENT_SECRET` | Secret client OAuth Google |
| `YT_REFRESH_TOKEN` | Jeton d'actualisation de la chaîne |

Tant que ces secrets sont absents, les publications planifiées sont simplement ignorées.

## Local

```bash
pip install -r requirements.txt
python -m src.main --hours 0.05 --dry-run
```
