#!/usr/bin/env python3
import logging
import json
import os

from pymongo.errors import ConnectionFailure
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from dateutil import tz
# Database models
from models.UserModel import UserModel
from models.GuildModel import GuildModel
from models.HeatMapModel import HeatMapModel
from models.RawInfoModel import RawInfoModel
from models.GuildsRnDaoModel import GuildsRnDaoModel

# Activity hourly
from analysis.activity_hourly import activity_hourly
from dotenv import load_dotenv


class RnDaoAnalyzer:
    """
    RnDaoAnalyzer
    class that handles database connection and data analysis
    """

    def __init__(self):
        """
        Class initiation function
        """
        """ MongoDB client """
        self.db_client = None
        """ Database URL """
        self.db_url = ""
        self.db_host = ""
        self.db_port = ""
        """ Database user -- TODO: Safe implementation to extract user info from env?"""
        """ Use a function instead of the string"""
        self.db_user = ""
        """ Database user password -- TODO: Safe implementation to extract user info from env?"""
        self.db_password = ""
        """ Testing, prevents from data upload"""
        self.testing = False

    def set_database_info(self, db_host: str = "", db_url: str = "", db_user: str = "", db_password: str = "", db_port: str = ""):
        """
        Database information setter
        """
        self.db_url = db_url
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

    def database_connect(self):
        """
        Connect to the database
        """
        """ Connection String will be modified once the url is provided"""

        CONNECTION_STRING = f"mongodb://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}"
        self.db_client = MongoClient(CONNECTION_STRING,
                                     serverSelectionTimeoutMS=10000,
                                     connectTimeoutMS=200000)

    def database_connection_test(self):
        """ Test database connection """
        try:
            # The ping command is cheap and does not require auth.
            self.db_client.admin.command('ping')
        except ConnectionFailure:
            logging.error("Server not available")
            return

    def run_once(self):
        """ Run analysis once (Wrapper)"""
        guilds_c = GuildsRnDaoModel(self.db_client["RnDAO"])
        guilds = guilds_c.get_connected_guilds()
        logging.info(f"Creating heatmaps for {guilds}")
        for guild in guilds:
            self.analysis_heatmap(guild)

    def get_guilds(self):
        """Returns the list of all guilds"""
        logging.info(
            f"Listed guilds {rawinfo_c.database.list_collection_names()}")

    def analysis_heatmap(self, guild):
        """
        Based on the rawdata creates and stores the heatmap data
        """
        # activity_hourly()
        if not guild in self.db_client.list_database_names():
            logging.error(f"Database {guild} doesn't exist")
            logging.error(
                f"Existing databases: {self.db_client.list_database_names()}")
            logging.info("Continuing")
            return

        # Collections involved in analysis
        # guild parameter is the name of the database
        rawinfo_c = RawInfoModel(self.db_client[guild])
        heatmap_c = HeatMapModel(self.db_client[guild])

        # Testing if there are entries in the rawinfo collection
        if rawinfo_c.count() == 0:
            logging.warning(
                f"No entries in the collection 'rawinfos' in {guild} databse")
            return

        if not heatmap_c.collection_exists():
            raise Exception(
                f"Collection '{heatmap_c.collection_name}' does not exist")
        if not rawinfo_c.collection_exists():
            raise Exception(
                f"Collection '{rawinfo_c.collection_name}' does not exist")

        last_date = heatmap_c.get_last_date()
        if last_date == None:
            # If no heatmap was created, than tha last date is the first
            # rawdata entry
            last_date = rawinfo_c.get_first_date()
            last_date.replace(tzinfo=timezone.utc)

        # Generate heatmap for the days between the last_date and today
        # rawinfo_c.test_get()

        while last_date.astimezone() < datetime.now().astimezone() - timedelta(days=1):
            entries = rawinfo_c.get_day_entries(last_date)
            if len(entries) == 0:
                # analyze next day
                last_date = last_date + timedelta(days=1)
                continue

            prepared_list = []
            account_list = []

            for entry in entries:
                entry["user_mentions"] = entry["user_mentions"][0].split(",")

                prepared_list.append(
                    {
                        # .strftime('%Y-%m-%d %H:%M'),
                        "datetime": entry["datetime"],
                        "channel": entry["channel"],
                        "author": entry["author"],
                        "replied_user": entry["replied_user"],
                        "user_mentions": entry["user_mentions"],
                        "reactions": entry["reactions"],
                        "thread": entry["thread"],
                        "mess_type": entry["type"],
                    }
                )
                if not entry["author"] in account_list and entry["author"]:
                    account_list.append(entry["author"])

                if entry["user_mentions"] != None:
                    for account in entry["user_mentions"]:
                        if account not in account_list and account:
                            account_list.append(account)

            activity = activity_hourly(prepared_list, acc_names=account_list)
            warnings = activity[0]
            heatmap = activity[1][0]
            # Parsing the activity_hourly into the dictionary
            numberOfAccounts = len(account_list)

            for i in range(numberOfAccounts):
                account = account_list[i]
                heatmap_dict = {}
                heatmap_dict["date"] = heatmap["date"][0]
                heatmap_dict["channel"] = heatmap["channel"][0]
                heatmap_dict["thr_messages"] = heatmap["thr_messages"][i]
                heatmap_dict["lone_messages"] = heatmap["lone_messages"][i]
                heatmap_dict["replier"] = heatmap["replier"][i]
                heatmap_dict["replied"] = heatmap["replied"][i]
                heatmap_dict["mentioner"] = heatmap["mentioner"][i]
                heatmap_dict["mentioned"] = heatmap["mentioned"][i]
                heatmap_dict["reacter"] = heatmap["reacter"][i]
                heatmap_dict["reacted"] = heatmap["reacted"][i]
                heatmap_dict["account_name"] = account
                if not self.testing:
                    heatmap_c.insert_one(heatmap_dict)

            # analyze next day
            last_date = last_date + timedelta(days=1)


if __name__ == "__main__":
    load_dotenv()

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    analyzer = RnDaoAnalyzer()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    analyzer.set_database_info(
        db_url="",
        db_host=host,
        db_password=password,
        db_user=user,
        db_port=port
    )
    analyzer.database_connect()
    analyzer.run_once()
