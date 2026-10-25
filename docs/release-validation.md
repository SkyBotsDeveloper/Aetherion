# Aetherion release validation

Validation date: 26 October 2026.
Repository: https://github.com/SkyBotsDeveloper/Aetherion

## Branding and deployment

- Updated the bot preset to `The_RaHa_BoT`, owner username to `iflexelite`, and owner ID to `73265606`.
- Replaced legacy branding in startup output, introductory messages, translated credits, handwriting captions, and README badges.
- Kept SkyBotsDeveloper credits and the original upstream acknowledgment and license.
- Corrected example repository URLs and HTTP user-agent links.
- Preserved feature API endpoints, API configuration names, and feature defaults.
- Removed embedded Telegram API credentials and the previous log-chat preset. Deployment credentials come from the environment; missing values produce a startup error before clients are created.
- Excluded local environments, cookies, sessions, generated media, and logs from the release.

## Bugs fixed

- Callback authorization now checks the user pressing a button instead of the bot that authored its message.
- Group owners retain moderation permissions when Telegram does not return explicit privilege flags.
- Privilege decorators reject ordinary members and handle private-chat commands safely.
- Zombie-cleanup confirmations cannot target a different chat through callback data.
- `/botschk` reuses an already running assistant, including assistants other than the first, without starting a duplicate session or disconnecting playback.
- Bot capability checks and generated bot links use the authenticated bot identity.
- Startup no longer deletes user images from the project root; stale partial downloads are still cleaned.
- Configuration parsing handles blank default owner values and reports invalid integer fields without echoing their contents.

## Verification

Local environment: Windows, Python 3.12.13, FFmpeg/ffprobe 8.0.1.

- Full runtime requirements installed; dependency compatibility check passed.
- Requirements also resolved for Python 3.12 on Linux x86_64.
- Offline regression suite: **166 tests passed**. Includes real image/video rendering, localized rich buttons and navigation, sticker pack ownership, Git update failures, autoplay, voiceplay, authorization, and startup configuration.
- All **113 plugin modules** imported successfully in an isolated process with synthetic configuration and outbound connections blocked. This verifies imports, not live Telegram or MongoDB connections.
- Ruff syntax and undefined-name checks passed (`F821,F822,F823,E9`).
- Bash syntax checks passed for `setup` and `start`.
- Deployment JSON, workflow YAML, and all five language YAML files parsed successfully.
- Secret-pattern scan and legacy-name scan found no matches in release source and documentation.
- Added GitHub Actions to repeat dependency, syntax, launcher, and offline regression checks on pushes and pull requests.

## Live public-provider checks

**16/16 checks passed** using synthetic input and public sample media:

| Check | Count | Result |
| --- | ---: | --- |
| Movie lookup: Inception, Sholay | 2 | Passed |
| Catbox and TempFile upload/download byte comparison | 2 | Passed |
| Anime image/animation tags: maid, hug, awoo | 3 | Passed |
| Image enhancement and transparent background removal | 2 | Passed |
| Reference-image backup video, validated with ffprobe | 1 | Passed; local H.264 backup clip |
| Quote image rendering service | 1 | Passed |
| Instagram, Facebook, Snapchat, TikTok, X sample downloads | 5 | Passed |

Command: `python -X utf8 scripts/check_public_providers.py --skip-ai --output <temporary-report-path>`.
These are point-in-time results; external services can change.

## Remaining live verification

No deployment credentials were supplied. Telegram login, assistant voice-chat playback, real MongoDB persistence, authenticated ESSE/STT/AI calls, and Heroku deployment require a configured deployment. Anonymous AI chat/image/text-to-video inference was not included in the public-provider run. Docker was unavailable locally, so a container image was not built.
