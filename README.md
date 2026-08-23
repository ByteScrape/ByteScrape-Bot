# ByteScrape Bot

ByteScrape Bot is a Discord management bot for subscription-based communities.  
It combines billing workflows, support ticket handling, role self-assignment, and GitHub repository delivery in one bot.

## Features

- **Subscription automation**
  - Track paid intervals in MongoDB
  - Notify users when subscriptions are overdue
  - Admin approval flow for payment confirmation and cancellation
  - Optional Pterodactyl server suspend/unsuspend by customer email
- **Ticket system**
  - Service-specific ticket creation with category routing
  - Controlled close/delete flow from message components
- **Server onboarding**
  - Welcome message + automatic member role assignment
  - Setup command to post rules, ticket, and role-selection embeds
- **Repository distribution**
  - Pull repositories from a configured GitHub organization
  - Store local ZIPs and send them directly through Discord

## Tech Stack

- Python
- `discord.py` (slash commands + component interactions)
- MongoDB (`motor`)
- `aiohttp` / `aiofiles`
- Optional Pterodactyl Application API integration

## Requirements

- Python **3.8+**
- MongoDB instance
- Discord bot application and token
- GitHub Personal Access Token (for repository pull commands)
- (Optional) Pterodactyl panel URL + application API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ByteScrape/ByteScrape-Bot.git
   cd ByteScrape-Bot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update `config.json` with your real values.
4. Start the bot:
   ```bash
   python launcher.py
   ```

## Command Overview

### Subscription
- `/add_subscription`
- `/configure-subscription`
- `/remove_subscription`
- `/list-subscriptions`

### GitHub Repository Management
- `/pull-repo`
- `/pull-all-repos`
- `/list-repos`
- `/list-local-repos`
- `/remove-repo`

### Server Setup and Delivery
- `/server_setup`
- `/sell`

> Most operational commands are permission-restricted to administrators.

## Configuration Reference (`config.json`)

| Key | Purpose |
|---|---|
| `name` | Logger/bot display name used in logs. |
| `bot.token` | Discord bot token. |
| `bot.description` | Bot description shown in Discord application context. |
| `bot.subscription_delay` | Interval (hours) for subscription expiration checks. |
| `bot.presence.activity` | Presence text displayed as game activity. |
| `bot.presence.status` | Status code (`0` online, `1` idle, `2` dnd, `3` invisible). |
| `bot.ids.guild` | Guild ID used by bot workflows. |
| `bot.ids.member` | Role ID automatically assigned on member join. |
| `bot.ids.welcome` | Channel ID for welcome messages. |
| `bot.ids.team` | Team/staff role used in ticket permissions. |
| `bot.ids.subscriptions` | Channel ID for subscription notifications. |
| `bot.ids.categories.*` | Ticket category channel IDs by service type. |
| `bot.ids.roles.announcements` | Role ID mapped to the announcements self-role option. |
| `bot.ids.roles.polls` | Role ID mapped to the polls self-role option. |
| `bot.design.thumbnail` / `bot.design.image` | Default embed media URLs. |
| `bot.design.color` | Default embed color hex value. |
| `bot.design.footer.*` | Default embed footer text/icon/timestamp behavior. |
| `database.mongodb.uri` | MongoDB connection URI. |
| `database.mongodb.dbs` | Database names loaded at startup. |
| `github.organisation` | Source GitHub organization for repository pull commands. |
| `github.username` / `github.token` | GitHub credentials used for API requests. |
| `pterodactyl.url` / `pterodactyl.token` | Pterodactyl admin API configuration. |
| `logging.save` / `logging.destination` | Optional file logging controls. |
| `paypal` | Payment link shown in subscription reminders. |

## Deployment Workflow

This repository includes `.github/deploy.yml`:
- Runs Qodana checks on pull requests and `main` pushes
- Deploys build artifacts to Pterodactyl when checks pass

## License

Licensed under **MIT with a Non-Production Clause**.  
See [LICENSE](LICENSE) for full terms.
