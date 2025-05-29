import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime

class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_prefix(self, guild_id):
        try:
            with open("Data/prefixes.json", "r") as f:
                prefixes = json.load(f)
            return prefixes.get(str(guild_id), "-")
        except (FileNotFoundError, json.JSONDecodeError):
            return "-"
        except Exception as e:
            print(f"Error loading prefixes: {e}")
            return "-"

    @commands.hybrid_command(name="ping", description="Check the bot's connection status and server prefix")
    async def ping(self, ctx):
        try:
            ws_latency = round(self.bot.latency * 1000)
            msg = await ctx.send("Pinging...")
            msg_latency = round((msg.created_at - ctx.message.created_at).total_seconds() * 1000)
            prefix = self.get_prefix(ctx.guild.id) if ctx.guild else "-"

            embed = discord.Embed(
                title="\U0001F3D3 Pong!",
                color=discord.Color.green() if ws_latency < 200 else discord.Color.orange()
            )
            embed.add_field(name="WebSocket Latency", value=f"```{ws_latency}ms```", inline=True)
            embed.add_field(name="Message Latency", value=f"```{msg_latency}ms```", inline=True)

            status = "Excellent" if ws_latency < 100 else "Good" if ws_latency < 200 else "Poor"
            color = "🟢" if ws_latency < 100 else "🟡" if ws_latency < 200 else "🔴"
            embed.add_field(name="Connection Status", value=f"{color} {status}", inline=False)

            embed.add_field(name="Server Prefix", value=f"`{prefix}`", inline=True)
            if ctx.guild:
                embed.add_field(name="Server", value=ctx.guild.name, inline=True)

            await msg.edit(content=None, embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while checking ping: {str(e)}",
                color=discord.Color.red()
            )
            if isinstance(ctx.interaction, discord.Interaction):
                if ctx.interaction.response.is_done():
                    await ctx.interaction.edit_original_response(embed=error_embed)
                else:
                    await ctx.interaction.response.send_message(embed=error_embed)
            else:
                await ctx.send(embed=error_embed)

    @commands.hybrid_command(name="userinfo", description="Get user info")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member}", color=discord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Displays server info")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title="Server Info", color=discord.Color.blue())
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description="Get user avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="banner", description="View user's banner")
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            embed = discord.Embed(title=f"{member.display_name}'s Banner", color=discord.Color.blue())
            embed.set_image(url=user.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This user has no banner.")

    @commands.hybrid_command(name="roles", description="List all roles")
    async def roles(self, ctx):
        roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
        await ctx.send("\n".join(roles))

    @commands.hybrid_command(name="emoji", description="List all emojis")
    async def emoji(self, ctx):
        emojis = [f"{emoji} - `{emoji.name}` (ID: {emoji.id})" for emoji in ctx.guild.emojis]
        await ctx.send("\n".join(emojis) if emojis else "No emojis found.")

    @commands.hybrid_command(name="invite", description="Get bot invite link")
    async def invite(self, ctx):
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions.all())
        await ctx.send(f"[Click here to invite me]({invite_url})")

    @commands.hybrid_command(name="botinfo", description="Show bot information")
    async def botinfo(self, ctx):
        embed = discord.Embed(title="Bot Info", color=discord.Color.purple())
        embed.add_field(name="Creator", value="ASKLORD", inline=True)
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="uptime", description="Show bot uptime")
    async def uptime(self, ctx):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.launch_time
        await ctx.send(f"Uptime: `{str(delta).split('.')[0]}`")

    @commands.hybrid_command(name="membercount", description="Show member count")
    async def membercount(self, ctx):
        await ctx.send(f"This server has `{ctx.guild.member_count}` members.")

    @commands.hybrid_command(name="roleinfo", description="Get info about a role")
    async def roleinfo(self, ctx, role: discord.Role):
        embed = discord.Embed(title=f"Role Info - {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="channelinfo", description="Get info about a channel")
    async def channelinfo(self, ctx, channel: discord.TextChannel):
        embed = discord.Embed(title=f"Channel Info - {channel.name}", color=discord.Color.orange())
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="Position", value=channel.position, inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    bot.launch_time = datetime.datetime.utcnow()
    await bot.add_cog(PingCog(bot))
