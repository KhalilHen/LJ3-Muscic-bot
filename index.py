import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

# Set FFmpeg path explicitly in code
os.environ["FFMPEG_EXECUTABLE"] = r"C:\ffmpeg\bin\ffmpeg.exe"

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent (required for reading messages)
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def play(ctx, *, song_url):
    await play_music(ctx, song_url)

async def play_music(ctx, song_url):
    # Ensure bot connects only if not already in the channel
    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client

    # Updated yt-dlp options to select an audio-only format
    ydl_opts = {
        'format': 'bestaudio[ext=webm]/bestaudio',  # Forces best audio format
        'noplaylist': True,
    }

    audio_url = None
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_url, download=False)
            audio_url = info['url']  # Direct audio URL
            print("Audio URL extracted:", audio_url)  # For debugging
    except Exception as e:
        await ctx.send(f"Error extracting audio: {e}")
        await voice_client.disconnect()
        return

    if audio_url:
        # Configure FFmpeg options
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -loglevel debug',
            'options': '-vn'
        }

        try:
            # Play the audio stream
            source = discord.FFmpegPCMAudio(audio_url, executable=os.environ["FFMPEG_EXECUTABLE"], **ffmpeg_options)
            voice_client.play(source)

            # Wait until the song finishes playing
            while voice_client.is_playing():
                await asyncio.sleep(1)
        except Exception as e:
            await ctx.send(f"Error playing audio: {e}")
        finally:
            # Disconnect after the song ends
            await voice_client.disconnect()
    else:
        await ctx.send("Could not retrieve audio stream.")
        await voice_client.disconnect()



