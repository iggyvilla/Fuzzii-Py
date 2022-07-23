import interactions
import logging
from datetime import datetime
from firebase_admin import firestore

db = firestore.client()
log = logging.getLogger("fpy")


class PadertionaryInteract(interactions.Extension):
    def __init__(self, bot: interactions.Client):
        self.bot = bot

    @interactions.extension_command(
        name="padertionary",
        description="Everything padertionary!"
    )
    async def padertionary_base(self, ctx: interactions.CommandContext):
        pass

    @padertionary_base.subcommand(
        name="add",
        description="Submit an entry into the Padertionary!",
    )
    async def padertionary_add(self, ctx: interactions.CommandContext):
        modal = interactions.Modal(
            title="New Padertionary Entry",
            custom_id="new_entry",
            components=[
                interactions.TextInput(
                    label="Entry name",
                    custom_id="entry",
                    placeholder="Enter entry here... Slowly onii-chan...",
                    style=interactions.TextStyleType.SHORT,
                    required=True
                ),
                interactions.TextInput(
                    label="Word type",
                    custom_id="type",
                    placeholder="A word? Verb? Noun? Action? Sus?",
                    style=interactions.TextStyleType.SHORT,
                    required=True
                ),
                interactions.TextInput(
                    label="Definition 1",
                    custom_id="def_1",
                    style=interactions.TextStyleType.PARAGRAPH,
                    placeholder="What does this new inside joke mean? (like any of them mean anything...)",
                    required=True
                ),
                interactions.TextInput(
                    label="Definition 2",
                    custom_id="def_2",
                    style=interactions.TextStyleType.PARAGRAPH,
                    placeholder="Put second definition if you're feeling wordy.",
                    required=False
                ),
                interactions.TextInput(
                    label="Definition 3",
                    custom_id="def_3",
                    style=interactions.TextStyleType.PARAGRAPH,
                    placeholder="A third definition? Seriously?",
                    required=False
                )
            ]
        )
        log.info("padertionary_add command issued")
        await ctx.popup(modal)

    @interactions.extension_modal("new_entry")
    async def modal_response(self, ctx, entry: str, type, def_1, def_2=None, def_3=None):
        log.info("Modal response received.")
        try:
            db.collection(u'padertionary').document(entry).set({
                'date_added': datetime.now().strftime("%B %d at %I:%M %p"),
                'definitions': list(filter(None, [def_1, def_2, def_3])),
                'type': type
            })
        except:
            log.critical("Firebase error.")
            await ctx.send("Something went wrong! Try again.", ephemeral=True)

        log.info("Successfully added new entry to database.")
        await ctx.send(f'Added **{entry}** to the Padertionary!', ephemeral=True)


def setup(bot):
    PadertionaryInteract(bot)
