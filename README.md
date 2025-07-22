# Espresso

The Rivian Cafe (et al.) Discord bot..

⚠️ The following project code may be referred to as "Spaghetti Code". It is not currently cleaned, organized, or otherwise not OCD-twitch-provoking.

## Dependencies

- [Discord Developer's API](https://discord.com/developers/applications)
- [Discord.py](https://github.com/rapptz/discord.py)
- [requests](https://github.com/psf/requests)
- Python 3.13+

## Goals

- [ ] Discord reminders (/remindme or !remind)
    - [ ] Commands loaded from SQL/NoSQL DB
        - [ ] Custom commands added by mod/admin
        - [ ] Roles initially set by server owner
        - [ ] Generic-only commands available to all
            - server owner has all commands until further notice
            - after joining, permissions granted internal to bot
- [x] Amazon referal link automated messages
- [ ] Server TOS + Acknowledge button
- [ ] /muteme [time]
- [ ] /ref [reference_str] (references to another message using embeds and link)
    - [ ] /addref [message_id] [reference_str]
