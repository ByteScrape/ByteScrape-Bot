# Discord Bot Template

This repository provides a template for building Discord bots using Python and discord.py. It includes features like slash commands, cogs (modules), a MongoDB database connection, and a custom logger.

## Features

* **Slash Commands:** Uses discord.py's `app_commands` for easy slash command creation.
* **Cogs:** Organizes bot functionality into separate modules (cogs) for better code structure.
* **MongoDB:** Includes a `MongoDB` class for seamless interaction with a MongoDB database.
* **Custom Logger:** Provides a `logger` object with colored output and emoji support for enhanced log readability.
* **Configuration:** Bot settings are stored in `config.json` for easy customization.

## Requirements

* Python 3.10 or higher
* discord.py
* emoji
* colorama
* motor

Install the necessary packages using `pip install -r requirements.txt`.

## Setup

1. Clone this repository.
2. Install the required packages.
3. Configure the bot by editing `config.json`.
    * Replace `"Your Token"` with your bot's token.
    * Update the bot's description, presence, and other settings.
    * Configure the MongoDB connection URI and database names.
4. Create your bot's commands and logic in the `cogs` directory.
5. Run the bot using `python launcher.py`.

## Usage

The template includes a `test.py` cog with a `/test` command as an example. You can expand upon this or create your own cogs.



You're right, the previous format for the configuration section might be a bit difficult to read. Here's an alternative using a table, which should provide a clearer and more organized presentation:

## Configuration

The `config.json` file allows you to customize various aspects of the Discord bot. Here's a breakdown of the configuration options:

| Key | Description | Type |
|---|---|---|
| `name` | The name of your Discord bot. | String |
| `bot.token` | Your bot's unique token (obtained from the Discord Developer Portal). | String |
| `bot.description` | A brief description of your bot. | String |
| `bot.presence.activity` | The text displayed as your bot's activity status. | String |
| `bot.presence.status` | The online status of your bot (0: Online, 1: Idle, 2: Do Not Disturb, 3: Invisible). | Integer |
| `bot.ids.guild` | The ID of your Discord guild for testing commands. | Integer |
| `bot.design.thumbnail` | URL to an image to use as the bot's thumbnail. | String |
| `bot.design.image` | URL to an image to use in the bot's profile. | String |
| `bot.design.color` | The hexadecimal color code for embeds. | String |
| `bot.design.footer.text` | The text to display in the footer of embeds. | String |
| `bot.design.footer.icon` | URL to an icon to display in the footer of embeds. | String |
| `bot.design.footer.timestamp` | Whether to include a timestamp in the footer of embeds. | Boolean |
| `database.mongodb.uri` | The connection URI for your MongoDB database. | String |
| `database.mongodb.dbs` | A list of database names to connect to. | Array of strings |
| `logging.save` | Whether to save logs to a file. | Boolean |
| `logging.destination` | The directory where log files will be saved. | String |
