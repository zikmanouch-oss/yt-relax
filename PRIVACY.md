# Privacy Policy — Calm Haven Uploader

_Last updated: November 4, 2026_

Calm Haven Uploader ("the Client") is a private, internal tool operated by the owner of the
YouTube channel **Calm Haven Sounds**. It uses the **YouTube API Services** only to upload the
channel's own relaxation videos.

## YouTube API Services
- The Client uses YouTube API Services. By using the Client you agree to be bound by the
  **YouTube Terms of Service**: https://www.youtube.com/t/terms
- Google's privacy practices apply: **Google Privacy Policy** — https://policies.google.com/privacy

## What data is accessed
- Only the owner's own YouTube channel is accessed, through OAuth 2.0 with the scopes
  `youtube.upload` and `youtube`.
- The Client uploads videos, sets their thumbnails, titles, descriptions and tags, and may add
  them to the channel's playlists.
- The Client does not read, collect or analyse any other user's data (no comments, no viewer
  data, no statistics of other channels).

## What data is stored
- An OAuth refresh token for the owner's channel, stored only as an encrypted secret
  (GitHub Actions secret). It is never shared.
- A local publication history (video ID, title, date) of the channel's own uploads.
- No personal data of any third party is stored, shared or sold.

## Deletion and revocation
- The owner can revoke the Client's access at any time from the Google security settings page:
  https://security.google.com/settings/security/permissions
- On revocation, the stored refresh token is deleted. Any data obtained from the YouTube API
  Services is deleted within 30 days of revocation or upon request.

## Contact
Questions can be sent through the "Calm Haven Sounds" YouTube channel page:
https://www.youtube.com/channel/UC5TLLkK5ytg4wTOEYdFcf2Q
