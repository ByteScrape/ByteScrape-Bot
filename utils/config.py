import json


class Config:
    def __init__(self):
        self.config = json.load(open("./config.json", "r"))

        self.name = self.config["name"]

        self.token = self.config["bot"]["token"]
        self.description = self.config["bot"]["description"]
        self.subscription_delay = self.config["bot"]["subscription_delay"]

        self.activity = self.config["bot"]["presence"]["activity"]
        self.status = self.config["bot"]["presence"]["status"]

        self.guild_id = self.config["bot"]["ids"]["guild"]
        self.member_id = self.config["bot"]["ids"]["member"]
        self.welcome_id = self.config["bot"]["ids"]["welcome"]
        self.team_id = self.config["bot"]["ids"]["team"]
        self.subscriptions_id = self.config["bot"]["ids"]["subscriptions"]

        self.thumbnail = self.config["bot"]["design"]["thumbnail"]
        self.image = self.config["bot"]["design"]["image"]
        self.color = self.config["bot"]["design"]["color"]
        self.footer_text = self.config["bot"]["design"]["footer"]["text"]
        self.footer_icon = self.config["bot"]["design"]["footer"]["icon"]
        self.timestamp = self.config["bot"]["design"]["footer"]["timestamp"]

        self.mongodb_uri = self.config["database"]["mongodb"]["uri"]
        self.mongodb_dbs = self.config["database"]["mongodb"]["dbs"]

        self.github_organisation = self.config["github"]["organisation"]
        self.github_username = self.config["github"]["username"]
        self.github_token = self.config["github"]["token"]

        self.pterodactyl_token = self.config["pterodactyl"]["token"]
        self.pterodactyl_url = self.config["pterodactyl"]["url"]

        self.save_logs = self.config["logging"]["save"]
        self.destination_logs = self.config["logging"]["destination"]

        self.paypal = self.config["paypal"]
