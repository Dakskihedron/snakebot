from discord.ext import commands
import logging


if str(logging.getLogger("discord").handlers) == "[<NullHandler (NOTSET)>]":
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")

    handler.setFormatter(
        logging.Formatter(
            '{"message": "%(message)s", "level": "%(levelname)s", "time": "%(asctime)s"}'
        )
    )

    logger.addHandler(handler)


class logger(commands.Cog):
    """For commands related to logging."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def loglevel(self, ctx, level):
        """Changes logging level.

        level: str
            The new logging level.
        """
        if level.upper == "DEBUG":
            logging.getLogger("discord").setLevel(logging.DEBUG)
        if level.upper == "INFO":
            logging.getLogger("discord").setLevel(logging.INFO)
        if level.upper == "WARNING":
            logging.getLogger("discord").setLevel(logging.WARNING)
        if level.upper == "ERROR":
            logging.getLogger("discord").setLevel(logging.ERROR)
        if level.upper == "CRITICAL":
            logging.getLogger("discord").setLevel(logging.CRITICAL)


def setup(bot: commands.Bot) -> None:
    """Starts logger cog."""
    bot.add_cog(logger(bot))
