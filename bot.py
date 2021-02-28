import discord
from discord.ext import commands
import os
import config

# Connects to discord, Sets command prefix, Removes default help command
# Sets discord intents to enable certain gateway features that are necessary

intents = discord.Intents.all()
intents.invites = False
intents.dm_typing = False
intents.webhooks = False
intents.integrations = False

bot = commands.Bot(
    intents=intents,
    command_prefix=commands.when_mentioned_or("."),
    case_insensitive=True,
    owner_ids=(225708387558490112, 204807103704072194, 198892706087436288),
    activity=discord.Game(name="Tax Evasion Simulator"),
)

if __name__ == "__main__":
    for extension in [
        f.name.replace(".py", "")
        for f in os.scandir("cogs")
        if f.is_file()
    ]:
        try:
            bot.load_extension(f"cogs.{extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}.\n{e} \n")

bot.run(config.token)
