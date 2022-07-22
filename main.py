import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_components import DiscordComponents

bot = commands.Bot(command_prefix="fp.", intents=discord.Intents.all(), 
                   status=discord.Status.idle, 
                   activity=discord.Activity(type=discord.ActivityType.watching, name="nhentai doujins")
                   )

slash = SlashCommand(bot, sync_commands=True, )

COGS = ('nhc.nhentai', 
        'nhc.rate_comic')


@bot.event
async def on_ready():
    DiscordComponents(bot)
    print("Fuzzi Py (RW) online!")


@slash.slash(name="ping", 
             description="See bot latency")
# @bot.command(help="Pings the bot", name="ping")
async def _ping(ctx: SlashContext):
    await ctx.send(f"Pong! ({bot.latency*1000:.2f}ms)")

for cog in COGS:
    bot.load_extension(cog)

bot.run('')
