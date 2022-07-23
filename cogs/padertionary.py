import interactions
import logging
import json
from typing import List
from string import ascii_uppercase
from datetime import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot

db = firestore.client()
log = logging.getLogger("fpy")

BOOK_LOGO = "https://static.wikia.nocookie.net/minecraft_gamepedia/images/5/50/Book_JE2_BE2.png/revision/latest/scale-to-width-down/160?cb=20210427032255"


# We gotta cache it so we don't get charged by Firebase for over-reading
def get_cached_padertionary() -> dict:
    with open("./jsons/padertionary_cache.json", "r") as f:
        return {k: v for k, v in sorted(json.load(f).items(), key=lambda x: x[0].replace("\"", ""))}


def add_to_cache(key, value):
    with open("./jsons/padertionary_cache.json", "w") as f:
        _a = get_cached_padertionary()
        _a[key] = value
        json.dump(_a, f, indent=4)


class PadertionaryInteract(interactions.Extension):
    def __init__(self, bot: interactions.Client):
        self.bot = bot
        self.page_components = [
            interactions.ActionRow(
                components=[
                    interactions.SelectMenu(
                        placeholder="Select letter",
                        custom_id="select_letter",
                        options=[
                            interactions.SelectOption(label=a, value=a) for a in ascii_uppercase.replace("Y", "")
                        ]
                    )
                ]),
            interactions.ActionRow(components=[
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Prev Page",
                    custom_id="prv_page_pader"
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Next Page",
                    custom_id="nxt_pg_pader"
                )
            ])
        ]

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

        db_entry = {
            'date_added': datetime.now().strftime("%B %d at %I:%M %p"),
            'definitions': list(filter(None, [def_1, def_2, def_3])),
            'type': type
        }

        try:
            db.collection(u'padertionary').document(entry).set(db_entry)
            add_to_cache(entry, db_entry)
        except:
            log.critical("Firebase/local cache error.")
            await ctx.send("Something went wrong! Try again. ```Firebase/local cache error```", ephemeral=True)

        log.info("Successfully added new entry to database.")
        await ctx.send(f'Added **{entry}** to the Padertionary!', ephemeral=True)

    @padertionary_base.subcommand(
        name="browse",
        description="Browse the Padertionary."
    )
    async def padertionary_browse(self, ctx: interactions.CommandContext):
        log.info("padertionary_browse command issued")
        cache = get_cached_padertionary()
        embed = interactions.Embed(
            color=0x2F3136,
            fields=[
                interactions.EmbedField(
                    name=f"{entry} ({value['type'].replace('*', '')})",
                    value=f"```md" + "\n" + '\n'.join(
                        [f"{x + 1}. {n}" for x, n in enumerate(value['definitions'])]) + "```",
                    inline=False
                ) for entry, value in list(cache.items())[:5]
            ]
        )
        embed.set_author(name="The Padertionary", icon_url=BOOK_LOGO)
        embed.set_footer(text=f"1/{len(cache) // 5} | Powered by cum")
        await ctx.send(
            embeds=embed,
            components=self.page_components
        )

    @interactions.extension_component("nxt_pg_pader")
    async def padertionary_nxt(self, ctx: interactions.CommandContext):
        log.info('next page')
        embed: interactions.Embed = ctx.message.embeds[0]
        next_page = int(embed.footer.text.split("/")[0]) + 1
        last_page = int(embed.footer.text.split("/")[1])
        cache = get_cached_padertionary()
        embed.clear_fields()
        embed.set_footer(text=f"{next_page}/{len(cache)//5} | Powered by cum")

        for entry, value in list(cache.items())[next_page * 5:next_page * 10]:
            embed.add_field(
                name=f"{entry} ({value['type'].replace('*', '')})",
                value=f"```md" + "\n" + '\n'.join(
                    [f"{x + 1}. {n}" for x, n in enumerate(value['definitions'])]) + "```",
                inline=False
            )

        await ctx.edit(embeds=embed, components=[
            interactions.ActionRow(
                components=[
                    interactions.SelectMenu(
                        placeholder="Select letter",
                        custom_id="select_letter",
                        options=[
                            interactions.SelectOption(label=a, value=a) for a in ascii_uppercase.replace("Y", "")
                        ]
                    )
                ]),
            interactions.ActionRow(components=[
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Prev Page",
                    custom_id="prv_page_pader"
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Next Page",
                    custom_id="nxt_pg_pader",
                    disabled=False if next_page != last_page else True
                )
            ])
        ])


def setup(bot):
    PadertionaryInteract(bot)
