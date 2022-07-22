import discord
import json
from utils.nhentai_parser import grab_ratings, write_ratings
from discord_slash.utils.manage_commands import create_option
from discord_slash import cog_ext, SlashContext
from discord.ext import commands
from discord.ext.commands import bot

class NHentaiRateComic(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    async def ratecomic(self, ctx, code: str, rating: float):
        ratings = grab_ratings()
        
        if rating > 10:
            await ctx.send("The rating has to be out of 10, silly baka.")
            return
        
        if code in ratings:
            ratings[code].append(rating)
        else:
            ratings[code] = [rating]
        
        write_ratings(ratings)
        
        await ctx.send(f'{rating}/10 stars rating added for doujin {code}!')
    
    @commands.command(
        name="ratecomic",
        brief="Rate a comic!",
        help="Rate a comic! Usage is ratecomic <code> <rating out of 10>"
    )
    async def ratecomic_normal(self, ctx, code, rating):
        await self.ratecomic(ctx, code, rating)
    
    @cog_ext.cog_slash(
        name="ratecomic",
        description="Rate a nhentai comic out of 10!",
        options=[
            create_option(
                name="doujin_code",
                description="The code of the nhentai douijin 4-8 digits long",
                option_type=4,
                required=True
            ),
            create_option(
                name="rating",
                description="Your rating of the doujin out of 10",
                option_type=4,
                required=True
            )
        ]
    )
    async def ratecomic_slash(self, ctx, code, rating):
        await self.ratecomic(ctx, code, rating)
        
def setup(bot):
    bot.add_cog(NHentaiRateComic(bot))