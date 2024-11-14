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

# Store the current voice client and source for pausing/resuming
current_source = None
voice_client = None
paused = asyncio.Event()  # Event to control pause/resume state

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def play(ctx, *, song_url):
    await play_music(ctx, song_url)

@bot.command()
async def pause(ctx):
    """Pause the currently playing audio."""
    global paused, voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        paused.set()  # Mark as paused
        await ctx.send("Playback paused.")
    else:
        await ctx.send("No audio is currently playing.")

@bot.command()
async def resume(ctx):
    """Resume paused audio."""
    global paused, voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        paused.clear()  # Clear pause state
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("Audio is not paused or nothing is playing.")

@bot.command()
async def stop(ctx):
    """Stop the audio and disconnect the bot."""
    global paused, voice_client
    if voice_client and voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        paused.clear()  # Clear pause state
        await ctx.send("Playback stopped and disconnected.")
    else:
        await ctx.send("Bot is not connected to any voice channel.")

async def play_music(ctx, song_url):
    global current_source, voice_client, paused

    # Ensure bot connects only if not already in the channel
    if not ctx.voice_client:
        if ctx.author.voice:  # Check if the user is connected to a voice channel
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            await ctx.send("You must join a voice channel first.")
            return
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
        return

    if audio_url:
        # Configure FFmpeg options
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -loglevel debug',
            'options': '-vn'
        }

        try:
            # Play the audio stream
            current_source = discord.FFmpegPCMAudio(audio_url, executable=os.environ["FFMPEG_EXECUTABLE"], **ffmpeg_options)
            voice_client.play(current_source)

            # Wait until the song finishes playing or the bot is paused
            while voice_client.is_playing():
                await asyncio.sleep(1)
                if paused.is_set():  # If paused, stop playing and wait for resume
                    await asyncio.sleep(1)  # Wait until resume
        except Exception as e:
            await ctx.send(f"Error playing audio: {e}")
        finally:
            # Check if the bot should disconnect only when no audio is playing and no one is in the channel
            if not voice_client.is_playing() and len(voice_client.channel.members) == 1:  # Only the bot remains
                await voice_client.disconnect()
    else:
        await ctx.send("Could not retrieve audio stream.")  




