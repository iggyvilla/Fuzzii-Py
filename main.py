import interactions
import logging
from os import environ
import firebase_admin
from firebase_admin import credentials

log = logging.getLogger("fpy")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s:%(funcName)s] %(message)s"))
log.addHandler(handler)
log.setLevel("DEBUG")

# For connection to the Padertionary Firestore
cred = credentials.Certificate('fuzzibot-py-firebase-adminsdk-4v3ju-0c82b6f0b1.json')
firebase_admin.initialize_app(cred)

bot = interactions.Client(
    # intents=interactions.Intents.ALL,
    token=environ['TOKEN'],
)


@bot.command(name="ping",
             description="See bot latency")
async def ping(ctx: interactions.CommandContext):
    await ctx.send(f"Pong! ({bot.latency:.2f}ms)")


@bot.event
async def on_ready():
    log.info("Bot online.")
    await bot.change_presence(presence=interactions.ClientPresence(
        status=interactions.StatusType.IDLE,
        activities=[interactions.PresenceActivity(name="nHentai doujins", type=interactions.PresenceActivityType.WATCHING)],
        afk=False
        )
    )

COGS = ('nhc.nhentai', 'cogs.padertionary')

for cog in COGS:
    bot.load(cog)

bot.start()
