from datetime import datetime
import sqlite3 as sqlite
import os
import json

from enumerators.DatabaseEventType import DatabaseEventType
from enumerators.PunishmentType import PunishmentType

import requests


class DatabaseHandler:
    def __init__(self, file: str = "database.sqlite"):
        self.file = file
        self.data = {}
        if '.json' in self.file:
            f = open(file, 'r')
            self.data = json.loads(f.read())
            f.close()
            self.sql = sqlite.connect(database=self.data['database'])
        else:
            self.sql = sqlite.connect(file)
        self.cur = self.sql.cursor()
        self.logging_guilds = []

    def refresh_sql_cnx(self):
        self.sql.commit()
        self.sql.close()
        if '.json' in self.file:
            self.sql = sqlite.connect(database=self.data['database'])
        else:
            self.sql = sqlite.connect(self.file)
        self.cur = self.sql.cursor()

    def convert_data_to_dict(headers: list, data: list):
        if len(headers) == len(data[0]):
            to_return = []
            for i in range(len(data)):
                to_return.append({})
                for j in range(len(headers)):
                    to_return[-1].update({headers[j]: data[i][j]})
            return to_return

    ####################################
    #         Message Logging          #
    ####################################

    def is_guild_logging(self, guild_id: str, force_renew: bool = False) -> bool:
        if guild_id in self.logging_guilds and not force_renew:
            return True
        self.refresh_sql_cnx()
        self.cur.execute(
            "SELECT DISTINCT guild_id FROM event_history WHERE event_type=9;")
        self.logging_guilds = [i[0] for i in self.cur.fetchall()]
        return guild_id in self.logging_guilds

    def get_guild_logging_channel(self, guild_id: str) -> list:
        self.refresh_sql_cnx()
        self.cur.execute(f"SELECT * FROM event_history WHERE event_type=9 AND guild_id=\"{guild_id}\" ORDER BY date DESC LIMIT 1")
        headers = [i[0] for i in self.cur.description]  # Fetch table column names
        idx = headers.index('channel_id')  # Get channel_id column
        resp = self.cur.fetchall()  # Get most recently set logging channel for guild_id
        if len(resp) > 0:
            return resp[0][idx]
        return []

    def set_guild_logging_channel(self, guild_id: str, channel_id: str, date: datetime):
        self.refresh_sql_cnx()
        self.logging_guilds.append(guild_id)
        self.cur.execute(f"DELETE FROM event_history WHERE guild_id=\"{guild_id}\" AND event_type={DatabaseEventType.enabled_logging_in_guild.value};")
        self.cur.execute(f"INSERT INTO event_view(name, guild_id) VALUES (\"enabled logging in guild\", \"{guild_id}\");")
        timestamp = date.strftime("%Y-%m-%d %H:%M:%S")
        self.cur.execute(f"INSERT INTO event_history(event_type, guild_id, channel_id, is_voice_channel, is_private_message, date) VALUES ({DatabaseEventType.enabled_logging_in_guild.value}, \"{guild_id}\", \"{channel_id}\", False, False, \"{timestamp}\")")
        self.sql.commit()

    def new_event(self, event_type: DatabaseEventType, guild_id: str, channel_id: str, is_voice_channel: bool, is_private_message: bool, date: datetime):
        self.refresh_sql_cnx()
        self.cur.execute(
            f"INSERT INTO event_history(event_type, guild_id, channel_id, is_voice_channel, is_private_message, date) VALUES ({event_type.value}, \"{guild_id}\",\"{channel_id}\",{1 if is_voice_channel else 0},{1 if is_private_message else 0},\"{date.strftime('%Y-%m-%d %H:%M:%S')}\")")
        self.sql.commit()

    def new_message(self, id: str, server_id: str, channel_id: str, author_id: str, created_at: datetime, mcontent: str):
        self.refresh_sql_cnx()
        self.cur.execute("INSERT INTO messages(id, guild_id, channel_id, author_id, created_at, content) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
            id, server_id, channel_id, author_id, created_at.strftime("%Y-%m-%d %H:%M:%S"), mcontent))
        self.sql.commit()

    def message_edit(self, id: str, new_content: str, edited_at: datetime):
        self.refresh_sql_cnx()
        self.cur.execute(f"SELECT * FROM messages WHERE id=\"{id}\" LIMIT 1")
        msg = self.cur.fetchone()
        self.cur.execute("INSERT INTO messages(id, guild_id, author_id, created_at, created_at, content) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" % (
            id, msg[1], msg[3], msg[4], edited_at.strftime("%Y-%m-%d %H:%M:%S"), new_content))
        self.cur.execute("INSERT INTO event_history(event_type, guild_id, channel_id, is_voice_channel, is_private_message, date) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" % (
            DatabaseEventType.message_edited, msg[1], msg[2], False, False, edited_at.strftime("%Y-%m-%d %H:%M:%S")))
        self.sql.commit()

    def get_message(self, id: str, guild_id: str):
        self.refresh_sql_cnx()
        self.cur.execute(
            f"SELECT * FROM messages WHERE id=\"{id}\" AND guild_id=\"{guild_id}\"")
        # Get headers to return dict for ease-of-use when/if responses update
        headers = [description[0] for description in self.cur.description]
        response = self.cur.fetchone()
        to_return = {}
        for i in range(len(headers)):
            to_return.update({headers[i]: response[i]})
        return to_return

    def delete_message(self, id: str, guild_id: str):
        self.refresh_sql_cnx()
        self.cur.execute(
            f"DELETE FROM messages WHERE id=\"{id}\" AND guild_id=\"{guild_id}\"")
        self.sql.commit()

    def delete_guild_messages(self, guild_id: str):
        self.refresh_sql_cnx()
        self.cur.execute(f"DELETE FROM messages WHERE guild_id=\"{guild_id}\"")
        self.sql.commit()

    def add_command_alias(self, guild_id: str, alias_name: str, response: str):
        self.refresh_sql_cnx()
        self.cur.execute("INSERT INTO aliases(id, guild_id, alias, response) VALUES (\"%s\", \"%s\", \"%s\", \"%s\")" % (
            "SELECT COUNT(*)+1 FROM aliases", guild_id, alias_name, response))
        self.sql.commit()

    ####################################
    #       Guild DB Management        #
    ####################################

    def add_server(self, id: str, owner_id: str, splash_url: str, banner_url: str, icon_url: str):
        self.refresh_sql_cnx()
        self.cur.execute("INSERT INTO server_info(id, owner_id, splash, banner, icon) VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");" % (
            id, owner_id, splash_url, banner_url, icon_url))
        self.sql.commit()

    def add_channel(self, id: str, server_info: str, name: str, position: int, created_at: datetime):
        self.refresh_sql_cnx()
        self.cur.execute("INSERT INTO channel_info(id, server_info, name, position, created_at) VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")" % (
            id, server_info, name, position, created_at.strftime("%Y-%m-%d %H:%M:%S")))
        self.sql.commit()

    ####################################
    #      Command DB Management       #
    ####################################

    def get_command_aliases(self, guild_id: str):
        self.refresh_sql_cnx()
        self.cur.execute(
            "SELECT alias FROM aliases WHERE guild_id=\"%s\"" % guild_id)
        resp = self.cur.fetchall()
        aliases = []
        for i in range(len(resp)):
            aliases.append(resp[i][0])
        return aliases

    def remove_command_alias(self, guild_id: str, alias_name: str):
        self.refresh_sql_cnx()
        self.cur.execute("DELETE FROM aliases WHERE guild_id=\"%s\" AND alias=\"%s\"" % (
            guild_id, alias_name))
        self.sql.commit()
        self.cur = self.sql.cursor()

    def get_command_alias_response(self, guild_id: str, alias_name: str):
        self.refresh_sql_cnx()
        self.cur.execute(
            f"SELECT response FROM aliases WHERE alias=\"{alias_name}\" LIMIT 1")
        return self.cur.fetchone()

    def add_activity_update(self, act_name: str, game_name: str = "", start: str = "", ref_url: str = ""):
        self.refresh_sql_cnx()
        self.cur.execute(
            f"INSERT INTO user_activity(activity_name, game_name, start, ref_url) VALUES (\"{act_name}\", \"{game_name}\", \"{start}\", \"{ref_url}\")")
        self.sql.commit()

    def get_alias(self, guild_id: str, alias_name: str) -> str:
        self.refresh_sql_cnx()
        self.cur.execute(
            f"SELECT response FROM aliases WHERE guild_id=\"{guild_id}\" and alias=\"{alias_name}\"")
        headers = [i[0] for i in self.cur.description]
        resp = self.cur.fetchall()

    def create_amazon_tag(self, guild_id: str, endian: str = ""):
        self.refresh_sql_cnx()
        self.cur.execute(
            "INSERT INTO AmazonLinks(guild_id, link_endian) VALUES (\"{guild_id}\",\"{endian}\")")
        self.sql.commit()

    def get_amazon_tag(self, guild_id: str) -> str:
        self.refresh_sql_cnx()
        self.cur.execute(
            f"SELECT link_endian FROM AmazonLinks WHERE guild_id=\"{guild_id}\" ORDER BY id desc LIMIT 1")
        resp = self.cur.fetchone()[0]
        self.sql.commit()
        return resp

    def get_amazon_chat_override(self, guild_id: str) -> bool:
        self.refresh_sql_cnx()
        self.cur.execute(
            f"SELECT override FROM AmazonLinks WHERE guild_id=\"{guild_id}\" ORDER BY id desc LIMIT 1")
        try:
            resp = self.cur.fetchone()[0]
            self.sql.commit()
            return resp == 1
        except:
            return False
