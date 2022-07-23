import utils.nhentai_parser as nhp
from utils.nhentai_parser import CachedNHentaiComic
from NHentai import NHentai
from NHentai.core.interfaces import Doujin
import interactions
import interactions.api.http.channel

NSFW_ICON = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/285/no-one-under-eighteen_1f51e.png'

nhentai = NHentai()


class BEComponents:
    """Container holding all component labels for the Browsable Embed in NHentaiCommand"""
    next = interactions.Button(
        style=interactions.ButtonStyle.SECONDARY,
        label="Next Page",
        custom_id="next_page",
        type=2
    )
    previous = interactions.Button(
        style=interactions.ButtonStyle.SECONDARY,
        label="Previous Page",
        custom_id="prev_page",
        type=2
    )


class BrowsableEmbedElements:
    def __init__(self, ctx: interactions.CommandContext):
        self.message = ctx.message
        self.embed = self.message.embeds[0]
        self.code = int(self.embed.fields[0].value)
        self.last_page = int(self.embed.fields[2].value)
        self.current_page = int(self.embed.footer.text[:self.embed.footer.text.index("/")])


class NHentaiCommand(interactions.Extension):
    def __init__(self, bot):
        self.bot: interactions.Client = bot
        self.lang_icon_links = {
            "English": "https://cdn.discordapp.com/attachments/717669518377222208/862934884128915456/english.png",
            "Chinese": "https://cdn.discordapp.com/attachments/717669518377222208/862934883231727636/china.png",
            "Japanese": "https://cdn.discordapp.com/attachments/717669518377222208/862934885546721330/japan.png"
        }

    def parse_tags(self, tags: list):
        if len(tags) > 15:
            cut_tags = tags[:15]
            cut_tags.append(f"*and {len(tags) - 15} more...*")
            return cut_tags
        return tags

    async def handle_nh(self, ctx: interactions.CommandContext, code: int):
        """nhentai command that sends a browsable comic embed"""

        print(f'Trying to grab comic with code {code}')

        if nhp.in_nhcache(code):
            print("Comic in cache, grabbing from there...")
            comic: CachedNHentaiComic = nhp.grab_comic(code)
            print("Successfully grabbed from cache")
        else:
            print("Comic not in cache... adding...")

            try:
                comic: Doujin = nhentai.get_doujin(doujin_id=code)
            except ValueError:
                await ctx.send("That comic does not exist :(")
                return

            nhp.add_nhcache(comic)
            print("Successfully added to cache")

        print('Success!')

        num_pages = comic.tags.pop()
        language = comic.tags.pop(-2)

        # Makes an embed with all the information of the comic
        nhentai_embed = interactions.Embed(
            title=comic.title,
            color=0x2F3136,
            footer=interactions.EmbedFooter(text=f'1/{comic.total_pages}'),
            thumbnail=interactions.EmbedImageStruct(url=self.lang_icon_links[language]),
            image=interactions.EmbedImageStruct(url=comic.images[0]),
            fields=[
                interactions.EmbedField(name='Code', value=f'{comic.id}', inline=True),
                interactions.EmbedField(name='Favorites', value=f'{comic.total_favorites}', inline=True),
                interactions.EmbedField(name='Pages', value=num_pages),
                interactions.EmbedField(name='Tags',
                                        value='> ' + ' '.join(self.parse_tags([f"`{tag}`" for tag in comic.tags[:-1]])),
                                        inline=False),
            ])

        # Grabs the comics rating
        if nhp.has_rating(code):
            comic_ratings = nhp.grab_ratings()[str(code)]
            footer = f"{sum(comic_ratings) / len(comic_ratings)}/10 ⭐"
        else:
            footer = 'No ratings yet.'

        nhentai_embed.add_field(name='Rating', value=footer)

        if comic.total_pages <= 25:
            select_pages = range(1, comic.total_pages + 1)
        else:
            select_pages = [x * comic.total_pages // 25 for x in range(1, 25)]
            select_pages.append(comic.total_pages)

            if 1 not in select_pages:
                select_pages[0] = 1

        select_menu = interactions.SelectMenu(
            options=[interactions.SelectOption(label=f"Page {page}", value=str(page)) for page in select_pages],
            custom_id="page_picker",
            placeholder="Skip to page..."
        )

        await ctx.send(embeds=nhentai_embed, components=[
            interactions.ActionRow(components=[select_menu]),
            interactions.ActionRow(components=[BEComponents.previous, BEComponents.next]),
        ])

    @interactions.extension_command(
        name="comic",
        description="Grabs an nHentai comic and sends a browsable embed of it! Usage: nh <code>.",
        scope=717669518377222204,
        options=[
            interactions.Option(
                name="comicid",
                min_length=4,
                max_length=8,
                description="The comic's 4-8 letter code",
                type=interactions.OptionType.INTEGER,
                required=True
            )
        ]
    )
    async def comic(self, ctx: interactions.CommandContext, comicid: int):
        await ctx.defer()
        await self.handle_nh(ctx, comicid)

    @interactions.extension_component("next_page")
    async def next_page_response(self, ctx: interactions.CommandContext):
        """Handles the component clicks on the browsable embed"""
        el = BrowsableEmbedElements(ctx)
        print(ctx.message.components)
        embed = el.embed
        if el.current_page == el.last_page:
            print(f"[nh:{el.code}] Already on last page")
            ctx.message.components[1]['disabled'] = True
            await ctx.message.edit(components=ctx.message.components)
            return

        embed.set_image(url=nhp.grab_comic(el.code).images[el.current_page])
        embed.set_footer(text=f'{el.current_page + 1}/{el.last_page}')

        await ctx.message.edit(embeds=embed)

        print(f"[nh:{el.code}] Moved to next page ({el.current_page + 1})")

        # label = button.component.label
        #
        # if label in ["Previous Page", "Next Page", "Skip to page"]:
        #     message = button.message
        #     embed = message.embeds[0]
        #     code = embed.fields[0].value
        #     last_page = int(embed.fields[2].value)
        #     current_page = int(embed.footer.text[:embed.footer.text.index("/")])
        #
        #     if label == "Previous Page":
        #         if (current_page - 1) == 0:
        #             print(f"[nh:{code}] Already on first page")
        #             await button.respond(type=6)
        #             return
        #
        #         embed.set_image(url=nhp.grab_comic(code).pages[current_page-2])
        #         embed.set_footer(text=f'{current_page - 1}/{last_page}')
        #         print(f"[nh:{code}] Moved to prev page ({current_page - 1})")
        #
        #     if label == "Next Page":
        #         if current_page == last_page:
        #             print(f"[nh:{code}] Already on last page")
        #             await button.respond(type=6)
        #             return
        #
        #         embed.set_image(url=nhp.grab_comic(code).pages[current_page])
        #         embed.set_footer(text=f'{current_page + 1}/{last_page}')
        #         print(f"[nh:{code}] Moved to next page ({current_page + 1})")
        #
        #     await message.edit(embed=embed)
        #     await button.respond(type=6)

    @interactions.extension_component("prev_page")
    async def prev_page_response(self, ctx: interactions.CommandContext):
        print('haha')

    # @commands.Cog.listener()
    # async def on_select_option(self, select: discord_components.interaction.Interaction):
    #     label = select.interacted_component[0].label
    #     value = select.interacted_component[0].value
    #     message = select.message
    #     embed = message.embeds[0]
    #
    #     # Info about comic
    #     code = embed.fields[0].value
    #     last_page = embed.fields[2].value
    #
    #     if label.startswith("Page"):
    #         embed.set_image(url=nhp.grab_comic(code).pages[int(value)-1])
    #         embed.set_footer(text=f'{int(value)}/{last_page}')
    #         print(f'[nh:{code}] Skipping to page {label}')
    #
    #         await message.edit(embed=embed)
    #         await select.respond(type=6)


def setup(bot):
    NHentaiCommand(bot)
