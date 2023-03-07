import discord
import os
import json
import datetime
import asyncio
import requests #Playing both sides here hehe
import aiohttp
import functools 

from bs4 import BeautifulSoup
from pystreamable import StreamableApi

import moviepy.editor as mpe
from moviepy.video.io.ffmpeg_tools import *

from redbot.core import commands
from redbot.core.config import Config


class Redditparser(commands.Cog):
    """The Reddit parser cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=718395193090375700, force_registration=True)
        posthistory=[]

        default_guild = {
            "state": True,
            "ignoreusers": False,
            "ignorebots": True,
            "channels": [],
        }

        default_global = {
            "mail": "",
            "password": ""     
        }

        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def upload_media(self, media, title):
        
        mail = await self.config.mail()
        password = await self.config.password()

        api = StreamableApi(mail, password)

        try:
            vid = await asyncio.to_thread(api.upload_video, media, title)
            vid = dict(vid)
            await asyncio.sleep(60)
            os.remove(media)
            return vid["shortcode"]
        except:
            os.remove(media)     
            return None
       

    def message_parser(self, message):
        redditlinks = []
        words = message.split()
        for word in words:
            if "reddit.com/r/" in word:
                link = "https://www.reddit.com/r/" + word.split("reddit.com/r/", maxsplit=2)[1] # this is to prevent old.reddit links or other links from breaking the bot
                redditlinks.append(link)
            else:
                pass
            
        redditlinks = list(set(redditlinks)) # filters duplicates

        if redditlinks == []:
            return None
        else: 
            return redditlinks

    async def get_image(self, ctx: commands.Context, json_data, post_id):   

        image = json_data['posts']['models'][post_id]['media']['content']
        title = json_data['posts']['models'][post_id]['title']
        author = json_data['posts']['models'][post_id]['author']
        subbreddit = json_data['posts']['models'][post_id]['subreddit']['name']
        spoiler = json_data['posts']['models'][post_id]['isSpoiler']
        permalink = json_data['posts']['models'][post_id]['permalink']


        embed=discord.Embed(description=f"**[{title}]({permalink})**",color=discord.Color.random())        
        embed.add_field(name=f"Author:", value=f"u/{author}", inline=True)
        embed.add_field(name=f"Subreddit:", value=f"r/{subbreddit}", inline=True)
        embed.set_image(url=image)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

        if spoiler == True:
            content = f"|| <{image}> ||"
        else:
            content = f"<{image}>"

        await ctx.send(content=content, embed=embed)

    async def get_text(self, ctx: commands.Context, json_data, post_id):
        document = json_data['posts']['models'][post_id]['media']['richtextContent']['document'][0]

        title = json_data['posts']['models'][post_id]['title']
        author = json_data['posts']['models'][post_id]['author']
        subbreddit = json_data['posts']['models'][post_id]['subreddit']['name']
        permalink = json_data['posts']['models'][post_id]['permalink']
        text=document['c'][0]['t']

        embed=discord.Embed(description=f"**[{title}]({permalink})**\n{text[0:4000] }",color=discord.Color.random())        
        embed.add_field(name=f"Author:", value=f"u/{author}", inline=True)
        embed.add_field(name=f"Subreddit:", value=f"r/{subbreddit}", inline=True)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    async def get_video(self, ctx: commands.Context, json_data, post_id):
        global path
        path = f"C:\\Users\\{os.getlogin()}\\Downloads\\"
        headers = {'User-Agent':'Mozilla/5.0'}

        type = json_data['posts']['models'][post_id]['media']['type']

        title = json_data['posts']['models'][post_id]['title']
        author = json_data['posts']['models'][post_id]['author']
        subbreddit = json_data['posts']['models'][post_id]['subreddit']['name']
        spoiler = json_data['posts']['models'][post_id]['isSpoiler']
        permalink = json_data['posts']['models'][post_id]['permalink']

        embed=discord.Embed(description=f"**[{title}]({permalink})**",color=discord.Color.random())        
        embed.add_field(name=f"Author:", value=f"u/{author}", inline=True)
        embed.add_field(name=f"Subreddit:", value=f"r/{subbreddit}", inline=True)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    
        
        if type == "video":
            dash_url = json_data['posts']['models'][post_id]['media']['dashUrl']
            height  = json_data['posts']['models'][post_id]['media']['height']
            dash_url = dash_url[:int(dash_url.find('DASH')) + 4]
            video_url = f'{dash_url}_{height}.mp4'
            audio_url = f'{dash_url}_audio.mp4'

            with open(path + 'video.mp4','wb') as file:
                response = requests.get(video_url,headers=headers)
                if(response.status_code == 200):
                    file.write(response.content)
                    file.close()
                else:
                    file.close()

            with open(path + 'audio.mp3','wb') as file:
                response = requests.get(audio_url,headers=headers)
                if(response.status_code == 200):
                    file.write(response.content)
                    file.close()
                else:
                    file.close()

            def combine_audio(vidname, audname, outname):
                ffmpeg_merge_video_audio(vidname, audname, outname, vcodec='copy', acodec='copy', ffmpeg_output=False, logger=None)

            try:
                combine_audio(path + 'video.mp4', path + 'audio.mp3', path + 'final_video.mp4')
                assert os.path.isfile(path + 'video.mp4')
                assert os.path.isfile(path + 'audio.mp3')
                os.remove(path + 'video.mp4')
                os.remove(path + "audio.mp3")
            except:
                os.rename(path + "video.mp4", path+"final_video.mp4")
                assert os.path.isfile(path + 'audio.mp3')
                os.remove(path + "audio.mp3")

        elif type == "gifvideo":
            gif_url = json_data['posts']['models'][post_id]['media']['content']
            with open(path + 'final_video.mp4','wb') as file:
                response = requests.get(gif_url,headers=headers)
                if(response.status_code == 200):
                   file.write(response.content)
                   file.close()
                else:
                   file.close()

        if os.stat(path + 'final_video.mp4').st_size < 8000000:
            file=discord.File(path + 'final_video.mp4', spoiler=spoiler)
            await ctx.send(embed=embed,file=file)
            os.remove(path + 'final_video.mp4')


        else:
            await ctx.message.add_reaction("🔃")
            await asyncio.sleep(5) # To fix weird permission errors with windows
            newname = f"streamable_{datetime.datetime.now().timestamp()}.mp4"
            os.rename(path + 'final_video.mp4', path + newname)
            code = await self.upload_media(path + newname, title)

            if code != None:
                await ctx.send(content=f"https://streamable.com/{code}")
                await ctx.send(embed=embed)
            else:
                code = "Streamable could not process this video"
                await ctx.send(content=code,embed=embed)

    async def get_url(self, ctx: commands.Context, json_data, post_id):
        
        source = json_data['posts']['models'][post_id]['source']['url']

        title = json_data['posts']['models'][post_id]['title']
        author = json_data['posts']['models'][post_id]['author']
        subbreddit = json_data['posts']['models'][post_id]['subreddit']['name']
        spoiler = json_data['posts']['models'][post_id]['isSpoiler']
        permalink = json_data['posts']['models'][post_id]['permalink']

        embed=discord.Embed(description=f"**[{title}]({permalink})**",color=discord.Color.random())        
        embed.add_field(name=f"Author:", value=f"u/{author}", inline=True)
        embed.add_field(name=f"Subreddit:", value=f"r/{subbreddit}", inline=True)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

        if source != None:
            content=source

        if spoiler == True:
            context = f"|| {context} ||"

        await ctx.send(content=content)
        await ctx.send(embed=embed)

    async def get_post(self, ctx: commands.Context, url):
        headers = {'User-Agent':'Mozilla/5.0'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                text= await resp.text()

                post_id = url[url.find('comments/') + 9:]
                post_id = f"t3_{post_id[:post_id.find('/')]}"
                

                soup = BeautifulSoup(text,'lxml')
                required_js = soup.find('script',id='data')
                json_data = json.loads(required_js.text.replace('window.___r = ','')[:-1])

                nsfw = json_data['posts']['models'][post_id]['isNSFW']
                try:
                    type = json_data['posts']['models'][post_id]['media']['type']
                except:
                    type = url
                
                if json_data['posts']['models'][post_id]["crosspostParentId"] != None:
                    post_id = json_data['posts']['models'][post_id]["crosspostParentId"]
                    permalink = json_data['posts']['models'][post_id]['permalink']

                    await self.get_post(ctx, permalink)
                
                if ctx.channel.is_nsfw() or not nsfw: 
                    if type == "image":
                        await self.get_image(ctx, json_data, post_id)
                    if type in ["video","gifvideo"]:
                        await self.get_video(ctx, json_data, post_id)
                    if type == "rtjson":
                        print("RTJSON")
                        await self.get_text(ctx, json_data, post_id)
                    if type in ["url","embed"]:
                        await self.get_url(ctx, json_data, post_id)
                        
                    await ctx.message.delete()
                else:    
                    await ctx.send("This post is NSFW, please use this command in a NSFW channel.")

        await session.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        
        if message.guild is None:
            return

        channels = await self.config.guild(ctx.guild).channels()
                
        if message.author == self.bot.user:
            return

        if message.channel.id not in channels:
            return

        if "reddit.com/r/" not in message.content:
            return

        else:
            links = self.message_parser(message.content)
        
            if links is not None:
                for link in links:
                    await self.get_post(ctx, link)


    #SETTINGS
    @commands.is_owner()
    @commands.group()
    async def rpsettings(self, ctx):
        """
        This settings for the redditparser cog
        """
        pass

    @commands.is_owner()
    @rpsettings.command()
    async def state(self, ctx, state:bool):
        """
        This command enables or disables the redditparser cog
        """
        await self.config.guild(ctx.guild).state.set(state)
        await ctx.send("State set to {}".format(state))

    @commands.is_owner()
    @rpsettings.command()
    async def ignoreusers(self, ctx, state:bool):
        """
        This command enables or disables link parsing for users
        """
        await self.config.guild(ctx.guild).ignoreusers.set(state)
        await ctx.send("Ignoreusers set to {}".format(state))

    @commands.is_owner()
    @rpsettings.command()
    async def ignorebots(self, ctx, state:bool):
        """
        This command enables or disables link parsing for bots
        """
        await self.config.guild(ctx.guild).ignorebots.set(state)
        await ctx.send("Ignorebots set to {}".format(state))    

    @commands.is_owner()
    @rpsettings.command()
    async def addchannel(self, ctx, *, channelID:int):
        """
        This command adds a channel to the list of channels to parse
        """
        guild_group = self.config.guild(ctx.guild)
        async with guild_group.channels() as channels:
            if channelID in channels:
                await ctx.send("Channel already in list")
            else:
                channels.append(channelID)
                await ctx.send(f"Reddit links will now be parsed in <#{channelID}>")

    @commands.is_owner()
    @rpsettings.command()
    async def removechannel(self, ctx, *, channelID:int):
        """
        This command adds a channel to the list of channels to parse
        """
        guild_group = self.config.guild(ctx.guild)
        async with guild_group.channels() as channels:
            if channelID not in channels:
                await ctx.send("Channel not in list")
            else:
                channels.remove(channelID)
                await ctx.send(f"Reddit links will no longer be parsed in <#{channelID}>")

    @commands.is_owner()
    @commands.dm_only()
    @rpsettings.command()
    async def mail(self, ctx, *, ID:str):
        """
        Add your streamable mail
        """
        await self.config.mail.set(ID)
        await ctx.send("Streamable Mail set")

    @commands.is_owner()
    @commands.dm_only()
    @rpsettings.command()
    async def password(self, ctx, *, secret:str):
        """
        Add your streamable password
        """
        await self.config.password.set(secret)
        await ctx.send("Streamable Password set")

    @commands.is_owner()
    @rpsettings.command()
    async def nukeconfig(self, ctx):
        """
        This command nukes the config
        """
        await self.config.clear_all()
        await ctx.send("Config cleared")
            
