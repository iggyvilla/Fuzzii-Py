import discord
import re
from discord.ext import commands
from discord_components import Button, Select, SelectOption
import discord_components
from soupsieve import select
import utils.nhentai_parser as nhp


NSFW_ICON = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/285/no-one-under-eighteen_1f51e.png'

class BEComponents:
    """Container holding all component labels for the Browsable Embed in NHentaiCommand"""
    next = "Next Page"
    previous = "Previous Page"
        

class NHentaiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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


    async def handle_nh(self, ctx, code: int):
        """nhentai command that sends a browsable comic embed"""
        # Checks if the given code has a proper amount of digits
        if 8 >= len(str(code)) >= 4:
            async with ctx.typing():
                print(f'Trying to grab comic with code {code}')
                
                if nhp.in_nhcache(code):
                    print("Comic in cache, grabbing from there...")
                    comic = nhp.grab_comic(code)
                    print("Successfully grabbed from cache")
                else:
                    print("Comic not in cache... adding...")
                    
                    try:
                        comic = nhp.NHentaiComic(code)
                    except ValueError:
                        await ctx.send("That comic does not exist :(")
                        return
                    
                    nhp.add_nhcache(comic)
                    print("Successfully added to cache")
                
                print('Success!')
            
            num_pages = comic.tags.pop()
            language = comic.tags.pop(-2)
            
            # Makes an embed with all the information of the comic
            nhentai_embed = discord.Embed(title=comic.title, color=0x2F3136)                                                           \
                .add_field(name='Code', value=f'{comic.code}', inline=True)                                                            \
                .add_field(name='Favorites', value=f'{comic.favorites}', inline=True)                                                  \
                .add_field(name='Pages', value=num_pages)                                                                              \
                .add_field(name='Tags', value='> ' + ' '.join(self.parse_tags([f"`{tag}`" for tag in comic.tags[:-1]])), inline=False) \
                .set_footer(text=f'1/{len(comic.pages)}')                                                                              \
                .set_thumbnail(url=self.lang_icon_links[language])                                                                     \
                .set_image(url=comic.pages[0])
            
            # Grabs the comics rating
            if nhp.has_rating(code):
                comic_ratings = nhp.grab_ratings()[str(code)]
                footer = f"{sum(comic_ratings)/len(comic_ratings)}/10 ⭐"
            else:
                footer = 'No ratings yet.'
                
            nhentai_embed.add_field(name='Rating', value=footer)
            
            if len(comic.pages) <= 25:
                select_pages = range(1, len(comic.pages) + 1)
            else:
                select_pages = [x * len(comic.pages)//25 for x in range(1, 25)]
                select_pages.append(len(comic.pages))
                
                if 1 not in select_pages:
                    select_pages[0] = 1
            
            select_options = [SelectOption(label="Page " + str(page), value=str(page)) for page in select_pages]
            
            await ctx.send(embed=nhentai_embed, components=[
                [Select(placeholder="Select a page", options=select_options)],
                [Button(label=BEComponents.previous), Button(label=BEComponents.next)]
            ])
        else:
            # If the code was invalid
            await ctx.send('You need a code between 4-8 digits! ex. `177013`')
            return
    
    @commands.command(
        name="nh",
        help="Grabs a nhentai comic and sends a browsable embed of it! Usage: nh <code>.",
        brief="Grabs the given nhentai comic and sends it!",
        aliases=["comic"]
    )
    @commands.is_nsfw()
    async def nh(self, ctx, code):
        await self.handle_nh(ctx, code)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        content = message.content
        ctx = self.bot.get_channel(message.channel.id)
        if content.startswith("["):
            # Regex match for [<4-6 ints>]
            match = re.findall("^\[\d{4,6}\]$", content)
            if 2 > len(match) > 0:
                code = int(content[1:-1])
                await self.handle_nh(ctx, code)
                return
            
            # Helper replies if code is too long
            match = re.findall("^\[.*\]$", content)
            if match:
                await ctx.send('Your code is either too short, or too long! (only 4-6 digits)')
                return
    
    @nh.error
    async def nh_error(self, ctx, error):
        if isinstance(error, ValueError):
            await ctx.send('That comic does not exist!')
            return
        
        if isinstance(error, commands.errors.NSFWChannelRequired):
            await ctx.send('You need to use this command in a NSFW channel!')
            return
        
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('You need to provide a 4-8 digit code! ex. `fp.nh 177013` or [177013]')
            return
        
        await ctx.send(f'An unknown error occured <@312917646695989248>... ```{error}```')
    
    @commands.Cog.listener()
    async def on_button_click(self, button):
        """Handles the component clicks on the browsable embed"""
        label = button.component.label
        
        if label in ["Previous Page", "Next Page", "Skip to page"]:
            message = button.message
            embed = message.embeds[0]
            code = embed.fields[0].value
            last_page = int(embed.fields[2].value)
            current_page = int(embed.footer.text[:embed.footer.text.index("/")])
        
            if label == "Previous Page":
                if ((current_page - 1) == 0):
                    print(f"[nh:{code}] Already on first page")
                    await button.respond(type=6)
                    return
                
                embed.set_image(url=nhp.grab_comic(code).pages[current_page-2])
                embed.set_footer(text=f'{current_page - 1}/{last_page}')
                print(f"[nh:{code}] Moved to prev page ({current_page - 1})")
                
            if label == "Next Page":
                if (current_page == last_page):
                    print(f"[nh:{code}] Already on last page")
                    await button.respond(type=6)
                    return
                
                embed.set_image(url=nhp.grab_comic(code).pages[current_page])
                embed.set_footer(text=f'{current_page + 1}/{last_page}')
                print(f"[nh:{code}] Moved to next page ({current_page + 1})")

            await message.edit(embed=embed)
            await button.respond(type=6)
            
    @commands.Cog.listener()
    async def on_select_option(self, select: discord_components.interaction.Interaction):
        label = select.interacted_component[0].label
        value = select.interacted_component[0].value
        message = select.message
        embed = message.embeds[0]
        
        # Info about comic
        code = embed.fields[0].value
        last_page = embed.fields[2].value
        
        if label.startswith("Page"):
            embed.set_image(url=nhp.grab_comic(code).pages[int(value)-1])
            embed.set_footer(text=f'{int(value)}/{last_page}')
            print(f'[nh:{code}] Skipping to page {label}')
            
            await message.edit(embed=embed)
            await select.respond(type=6)
            
        
def setup(bot):
    bot.add_cog(NHentaiCommand(bot))
