import json



class Config:
    def __init__(self):
        config = json.load(open("./config.json", "r"))

        self.name = config["name"]

        self.token = config["bot"]["token"]
        self.description = config["bot"]["description"]

        self.activity = config["bot"]["presence"]["activity"]
        self.status = config["bot"]["presence"]["status"]

        self.guild_id = config["bot"]["ids"]["guild"]

        self.thumbnail = config["bot"]["design"]["thumbnail"]
        self.image = config["bot"]["design"]["image"]
        self.color = config["bot"]["design"]["color"]
        self.footer_text = config["bot"]["design"]["footer"]["text"]
        self.footer_icon = config["bot"]["design"]["footer"]["icon"]
        self.timestamp = config["bot"]["design"]["footer"]["timestamp"]

        self.mongodb_uri = config["database"]["mongodb"]["uri"]
        self.mongodb_dbs = config["database"]["mongodb"]["dbs"]

        self.save_logs = config["logging"]["save"]
        self.destination_logs = config["logging"]["destination"]

        self.paypal = config["paypal"]