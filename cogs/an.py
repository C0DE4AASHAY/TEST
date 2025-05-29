import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist = set()
        self.anti_nuke_enabled = True
        self.action_logs = {
            'channel_create': {},
            'channel_delete': {},
            'member_kick': {},
            'webhook_update': {},
        }
        self.thresholds = [0.01, 0.05, 0.1, 1.0, 2.0, 0.2, 0.4, 0.3, 0.02, 0.03, 0.04, 0.06]  # in seconds
        self.max_actions = 3

    def is_suspicious(self, user_id, action_type):
        now = time.time()
        logs = self.action_logs[action_type].setdefault(user_id, [])
        logs.append(now)
        self.action_logs[action_type][user_id] = [t for t in logs if now - t <= max(self.thresholds)]

        for threshold in self.thresholds:
            actions_within = [t for t in logs if now - t <= threshold]
            if len(actions_within) >= self.max_actions:
                return True
        return False

    async def take_action(self, guild, user_id):
        user = guild.get_member(user_id)
        if user and user.id not in self.whitelist:
            try:
                await guild.ban(user, reason="Anti-Nuke: Suspicious activity detected")
            except Exception as e:
                print(f"Failed to ban {user}: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not self.anti_nuke_enabled:
            return
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if self.is_suspicious(entry.user.id, 'channel_create'):
                await self.take_action(channel.guild, entry.user.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.anti_nuke_enabled:
            return
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if self.is_suspicious(entry.user.id, 'channel_delete'):
                await self.take_action(channel.guild, entry.user.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not self.anti_nuke_enabled:
            return
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and self.is_suspicious(entry.user.id, 'member_kick'):
                await self.take_action(member.guild, entry.user.id)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        if not self.anti_nuke_enabled:
            return
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            if self.is_suspicious(entry.user.id, 'webhook_update'):
                await self.take_action(channel.guild, entry.user.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            return
        if not member.public_flags.verified_bot:
            try:
                await member.ban(reason="Anti-Nuke: Unverified bot joined")
            except Exception as e:
                print(f"Failed to ban unverified bot {member.name}: {e}")

    # Whitelist Slash Command Group
    @app_commands.command(name="antinuke_toggle", description="Toggle anti-nuke protection")
    @app_commands.describe(state="Enable or disable anti-nuke system")
    async def antinuke_toggle(self, interaction: discord.Interaction, state: bool):
        self.anti_nuke_enabled = state
        await interaction.response.send_message(f"✅ Anti-nuke is now {'enabled' if state else 'disabled'}.", ephemeral=True)

    whitelist_group = app_commands.Group(name="whitelist", description="Manage anti-nuke whitelist")

    @whitelist_group.command(name="add")
    async def whitelist_add(self, interaction: discord.Interaction, member: discord.Member):
        self.whitelist.add(member.id)
        await interaction.response.send_message(f"✅ {member.mention} added to the whitelist.", ephemeral=True)

    @whitelist_group.command(name="remove")
    async def whitelist_remove(self, interaction: discord.Interaction, member: discord.Member):
        self.whitelist.discard(member.id)
        await interaction.response.send_message(f"✅ {member.mention} removed from the whitelist.", ephemeral=True)

    @whitelist_group.command(name="show")
    async def whitelist_show(self, interaction: discord.Interaction):
        if not self.whitelist:
            await interaction.response.send_message("📃 Whitelist is empty.", ephemeral=True)
        else:
            members = [f"<@{uid}>" for uid in self.whitelist]
            await interaction.response.send_message("📃 Whitelisted users: " + ", ".join(members), ephemeral=True)

    @whitelist_group.command(name="reset")
    async def whitelist_reset(self, interaction: discord.Interaction):
        self.whitelist.clear()
        await interaction.response.send_message("✅ Whitelist has been reset.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.tree.add_command(self.whitelist_group)
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
