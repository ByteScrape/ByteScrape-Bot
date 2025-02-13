
# ByteScrape Bot

This is a Discord bot designed for managing a community server with features like:

* **Automated Subscription Management:** Tracks user subscriptions, sends renewal reminders, and optionally integrates with Pterodactyl to suspend/unsuspend servers based on payment status.
* **Ticket System:** Allows users to create tickets for support requests, categorized by service type.
* **Role Management:** Provides a role selection system for announcements and polls.
* **GitHub Integration:** Pulls and manages repositories from a GitHub organization.
* **Welcome Messages:** Greets new members with a welcome message and assigns them a default role.
* **Sell System:** Allows administrators to easily share (or "sell") project files from locally stored repositories.

## Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/ByteScrape-Bot.git](https://github.com/your-username/ByteScrape-Bot.git)
2.  **Install dependencies:**
    
    
    ```
    pip install -r requirements.txt
    ```
    
3.  **Configure the bot:**
    -   Create a `config.json` file based on the provided example and fill in the required information.
    -   This includes your bot token, guild ID, role IDs, database credentials, and more.

## Usage

Once the bot is configured, you can run it using:

```
python launcher.py
```

## Requirements

-   Python 3.7 or higher
-   Discord.py library
-   MongoDB database
-   (Optional) Pterodactyl panel access for server management

## Commands

The bot offers various slash commands for managing subscriptions, repositories, and server setup.

**Subscription Management:**

-   `/add_subscription`: Adds a new user subscription.
-   `/configure-subscription`: Updates an existing subscription.
-   `/remove_subscription`: Removes a user's subscription.
-   `/list-subscriptions`: Lists all active subscriptions.

**GitHub Integration:**

-   `/pull-repo`: Pulls a specific repository from GitHub.
-   `/pull-all-repos`: Pulls all available repositories from the organization.
-   `/list-repos`: Lists all repositories in the GitHub organization.
-   `/list-local-repos`: Lists locally downloaded repositories.
-   `/remove-repo`: Removes a locally stored repository.

**Server Setup:**

-   `/server_setup`: Sends pre-configured embed messages for rules, ticket creation, and role selection.

**Sell System:**

-   `/sell`: Sends a selected repository file to the channel.

## Configuration

The `config.json` file holds all the essential settings for the bot:
| Setting | Description | Example |
|--|--|--|
| bot.token	|Your Discord bot token.|"YOUR_DISCORD_BOT_TOKEN"|
|bot.description|A brief description of your bot.|"A bot for managing subscriptions and more."|
bot.subscription_delay|How often (in hours) the bot checks for expired subscriptions.|24
bot.presence.activity|The text displayed as the bot's "Playing" status.|"with subscriptions"|
bot.presence.status|	Controls the online status of the bot.|	0 (online), 1 (idle), 2 (dnd), 3 (invisible)|
bot.ids.guild|	The ID of your Discord server.	|"YOUR_GUILD_ID"|
bot.ids.member|The ID of the default role assigned to new members.|"MEMBER_ROLE_ID"|
bot.ids.welcome|The ID of the channel where welcome messages are sent.|"WELCOME_CHANNEL_ID"|
bot.ids.team|The ID of the role that has elevated permissions.|"TEAM_ROLE_ID"|
bot.ids.subscriptions|The ID of the channel where subscription notifications are sent.|"SUBSCRIPTIONS_CHANNEL_ID"
|bot.design.thumbnail|Default thumbnail URL for embeds.|"https://example.com/thumbnail.png"
bot.design.image|Default image URL for embeds.|"https://example.com/image.png"
|bot.design.color|Default embed color (hexadecimal).|"36393F"|
|bot.design.footer.text|Default footer text for embeds.	|"ByteScrape Bot"|
|bot.design.footer.icon|URL for the footer icon.	|"https://example.com/icon.png"|
|bot.design.footer.timestamp|	Whether to include a timestamp in embeds.|	true or false|
database.mongodb.uri|	Your MongoDB connection string.	|"mongodb://username:password@localhost:27017/"|
database.mongodb.dbs	|A list of database names that the bot will use.|	["ByteScrape"]|
github.organisation|	The name of your GitHub organization.|	"YOUR_GITHUB_ORG"|
github.username	|Your GitHub username.|"YOUR_GITHUB_USERNAME"| 
|github.token|A GitHub personal access token.|"YOUR_GITHUB_TOKEN"|
|pterodactyl.token|Your Pterodactyl application API key.|"YOUR_PTERODACTYL_API_KEY"|
|pterodactyl.url|The base URL of your Pterodactyl panel.|"https://your.pterodactyl.panel"|
|logging.save|	Whether to save logs to a file.	|true or false|
|logging.destination|The file path where logs will be saved.|"logs/bytescrape.log"|
|paypal	|Your PayPal link for subscription payments.	|"https://www.paypal.me/yourpaypal"|


Make sure to properly configure this file according to your needs and environment.
