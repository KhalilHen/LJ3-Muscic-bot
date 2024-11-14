import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

# Set the FFmpeg path manually
os.environ["FFMPEG_EXECUTABLE"] = r"C:\ffmpeg\bin\ffmpeg.exe"

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent (required for reading messages)

# Create the bot instance with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Define play command
@bot.command()
async def play(ctx, *, song_url):
    await play_music(ctx, song_url)

async def play_music(ctx, song_url):
    # Connect to the voice channel of the user
    channel = ctx.author.voice.channel
    voice_client = await channel.connect()

    # Set up yt-dlp options to extract audio from the URL (no post-process)
    ydl_opts = {
        'format': 'bestaudio/best',  # Best audio quality
        'noplaylist': True,          # Don't download playlists
    }

    # Use yt-dlp to extract audio info
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song_url, download=False)
        audio_url = info['formats'][0]['url']

    # Play the audio stream directly
    voice_client.play(discord.FFmpegPCMAudio(audio_url))

    # Wait until the song finishes playing
    while voice_client.is_playing():
        await asyncio.sleep(1)

    # Disconnect after the song ends
    await voice_client.disconnect()


