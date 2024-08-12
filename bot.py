import discord
from discord.ext import commands, tasks
from mcstatus import MinecraftServer
import asyncio
import re
import config

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Helper function to remove Minecraft color codes
def clean_motd(motd):
    return re.sub(r'§[0-9a-fk-or]', '', motd)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    status_updater.start()  # Start the task loop when the bot is ready

@tasks.loop(seconds=config.UPDATE_INTERVAL)
async def status_updater():
    channel = bot.get_channel(config.CHANNEL_ID)
    if channel is not None:
        try:
            server = MinecraftServer.lookup(f"{config.SERVER_IP}:{config.DEFAULT_MC_PORT}")
            status = server.status()

            motd = status.description
            if isinstance(motd, dict):
                motd = motd.get('text', '')
            elif isinstance(motd, str):
                motd = motd
            
            motd_cleaned = clean_motd(motd)

            embed = discord.Embed(
                title=f"🟢 Minecraft Server Status for `{config.SERVER_IP}:{config.DEFAULT_MC_PORT}`",
                description=f"**MOTD:** {motd_cleaned}",
                color=discord.Color.green()
            )

            embed.add_field(name="🌍 Version", value=status.version.name, inline=True)
            embed.add_field(name="👥 Players Online", value=f"{status.players.online}/{status.players.max}", inline=True)
            embed.add_field(name="📶 Latency", value=f"{status.latency} ms", inline=True)
            embed.add_field(name="⏳ Next Update In", value=f"{config.UPDATE_INTERVAL} seconds", inline=False)
            embed.set_thumbnail(url=config.THUMBNAIL_URL)
            embed.set_image(url=config.BANNER_URL)
            embed.set_footer(text="Minecraft Server Status Bot", icon_url=config.FOOTER_ICON_URL)

            # Check if we have sent an initial message
            if not hasattr(bot, 'status_message'):
                # Send the initial embed and store the message object
                bot.status_message = await channel.send(embed=embed)
            else:
                # Update the existing message
                await bot.status_message.edit(embed=embed)

            # Countdown Timer Update
            for i in range(config.UPDATE_INTERVAL, 0, -1):
                countdown_embed = discord.Embed.from_dict(bot.status_message.embeds[0].to_dict())
                countdown_embed.set_field_at(
                    3,
                    name="⏳ Next Update In",
                    value=f"{i} seconds",
                    inline=False
                )
                await bot.status_message.edit(embed=countdown_embed)
                await asyncio.sleep(1)

        except Exception as e:
            error_embed = discord.Embed(
                title="⚠️ Error",
                description=f"Failed to retrieve server status:\n`{e}`",
                color=discord.Color.red()
            )
            await channel.send(embed=error_embed)
    else:
        print(f"Channel with ID {config.CHANNEL_ID} not found.")

bot.run(config.DISCORD_BOT_TOKEN)
