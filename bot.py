# -*- coding: utf-8 -*-

import discord
from discord.ext import commands, voice_recv
import speech_recognition as sr  # For speech-to-text
import argparse
import asyncio
import os  # For checking if the MP3 file exists
import functools # For using partial to pass arguments to callback

# --- Configuration ---
TEXT_KEYWORD = "based" # Keyword for text channel replies
VOICE_KEYWORD = "based" # Keyword for voice channel detection
MP3_FILE_PATH = "based.mp3"  # Path to your MP3 file (e.g., in the same directory)

# For SpeechRecognition library:
# "sphinx" for CMU PocketSphinx (offline, install with: pip install pocketsphinx)
# "google" for Google Web Speech API (online, generally more accurate, no key needed for basic use)
RECOGNIZER_ENGINE = "google" # or "sphinx"

# --- Opus Loading (Essential for discord.py voice) ---
try:
    if not discord.opus.is_loaded():
        opus_libs = ['opus', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib', '/opt/homebrew/lib/libopus.dylib'] # Added common macOS M1 path
        loaded = False
        for lib in opus_libs:
            try:
                discord.opus.load_opus(lib)
                print(f"Opus library loaded successfully: {lib}")
                loaded = True
                break
            except OSError:
                continue
        if not loaded:
            print("----------------------------------------------------")
            print("Could not load the Opus library. Voice will not work.")
            print("Please ensure Opus is installed and accessible.")
            print("Common solutions:")
            print("- Windows: Download libopus-0.dll from opus-codec.org and place it in your bot's directory or System32.")
            print("- Linux (Debian/Ubuntu): sudo apt-get install libopus0")
            print("- Linux (Fedora): sudo dnf install opus")
            print("- macOS (Homebrew): brew install opus")
            print("----------------------------------------------------")
except AttributeError:
    print("discord.opus module not found. This suggests an issue with your discord.py installation or version.")
    print("Ensure you have a compatible version of discord.py that supports voice.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during Opus loading: {e}")
    exit()


# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # To read message content for commands AND text keyword.
intents.voice_states = True     # To track voice channel joins/leaves and states.
# intents.messages = True # Already implicitly covered by message_content for receiving, but good to be explicit if only for non-content parts.

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

# --- Speech Recognizer Setup ---
recognizer = sr.Recognizer()

class VoiceListenerCog(commands.Cog, name="VoiceListener"):
    """Cog for voice listening and keyword detection."""
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.active_sinks = {}

    async def _play_audio(self, voice_client, source_path, text_channel_for_error=None):
        """Plays an audio file in the given voice client. Internal helper."""
        if not os.path.exists(source_path):
            error_msg = f"Error: MP3 file not found at '{source_path}'"
            print(error_msg)
            if text_channel_for_error:
                try:
                    await text_channel_for_error.send(error_msg)
                except discord.Forbidden:
                    print(f"Missing permissions to send error message in {text_channel_for_error.name}")
            return

        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()

            try:
                audio_source = discord.FFmpegPCMAudio(source_path)
                voice_client.play(audio_source, after=lambda e: print(f'Finished playing: {e}' if e else 'Playback complete.'))
                print(f"Playing '{source_path}' in {voice_client.channel.name}...")
            except Exception as e:
                print(f"Error playing audio: {e}")
                if text_channel_for_error:
                    try:
                        await text_channel_for_error.send(f"An error occurred while trying to play the audio: {e}")
                    except discord.Forbidden:
                        pass
        else:
            print("Voice client not connected or available for playback.")


    def _audio_data_callback(self, user: discord.User, data: voice_recv.VoiceData, vc: voice_recv.VoiceRecvClient, text_channel: discord.TextChannel):
        """Callback for processing received audio data."""
        if not data.audio:
            return

        try:
            audio_segment = sr.AudioData(data.audio.read(), sample_rate=48000, sample_width=2)
            recognized_text = ""
            if RECOGNIZER_ENGINE == "sphinx":
                try:
                    recognized_text = recognizer.recognize_sphinx(audio_segment, language="en-US").lower()
                except sr.UnknownValueError: pass
                except sr.RequestError as e: print(f"PocketSphinx error for {user.name}: {e}")
            elif RECOGNIZER_ENGINE == "google":
                try:
                    recognized_text = recognizer.recognize_google(audio_segment, language="en-US").lower()
                except sr.UnknownValueError: pass
                except sr.RequestError as e: print(f"Google Web Speech API request error for {user.name}: {e}")
            else:
                print(f"Unsupported recognizer engine: {RECOGNIZER_ENGINE}")
                return

            if recognized_text:
                print(f"Recognized from {user.name} in {vc.channel.name}: '{recognized_text}'")

            if VOICE_KEYWORD in recognized_text:
                print(f"Voice Keyword '{VOICE_KEYWORD}' detected from {user.name} in {vc.channel.name}!")
                if vc and vc.is_connected():
                    asyncio.run_coroutine_threadsafe(
                        self._play_audio(vc, MP3_FILE_PATH, text_channel),
                        self.bot.loop
                    )
                else:
                    print(f"Keyword detected, but voice client for {vc.guild.name} is no longer valid or connected.")

        except Exception as e:
            print(f"Error processing audio data from {user.name}: {e}")
            import traceback
            traceback.print_exc()


    @commands.command(name="joinbased")
    async def joinbased(self, ctx: commands.Context):
        """Makes the bot join your current voice channel and listen for the keyword."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel to use this command.")
            return

        channel = ctx.author.voice.channel
        guild_id = ctx.guild.id

        if guild_id in self.active_sinks and self.active_sinks[guild_id].is_connected():
            if self.active_sinks[guild_id].channel == channel:
                await ctx.send(f"I'm already in {channel.name} and listening.")
                return
            else:
                try:
                    await self.active_sinks[guild_id].move_to(channel)
                    await ctx.send(f"Moved to {channel.name} and I'm listening.")
                    return
                except Exception as e:
                    await ctx.send(f"Error moving to your channel: {e}")
                    if guild_id in self.active_sinks:
                        await self.active_sinks[guild_id].disconnect(force=True)
                        del self.active_sinks[guild_id]

        try:
            vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
            self.active_sinks[guild_id] = vc
            bound_callback = functools.partial(self._audio_data_callback, vc=vc, text_channel=ctx.channel)
            vc.listen(voice_recv.BasicSink(bound_callback))
            await ctx.send(f"Joined {channel.name} and now listening for the voice keyword '{VOICE_KEYWORD}'.")
            print(f"Listening in {channel.name} on guild {ctx.guild.name}")

        except discord.ClientException as e:
            await ctx.send(f"Error connecting to voice channel: {e}")
            if guild_id in self.active_sinks: del self.active_sinks[guild_id]
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
            print(f"Error in joinbased command: {e}")
            import traceback; traceback.print_exc()
            if guild_id in self.active_sinks: del self.active_sinks[guild_id]

    @commands.command(name="leavebased")
    async def leavebased(self, ctx: commands.Context):
        """Makes the bot leave the voice channel and stop listening."""
        guild_id = ctx.guild.id
        if guild_id in self.active_sinks and self.active_sinks[guild_id].is_connected():
            vc = self.active_sinks[guild_id]
            await vc.disconnect(force=False)
            del self.active_sinks[guild_id]
            await ctx.send("Left the voice channel. No longer listening.")
            print(f"Disconnected from voice in guild {ctx.guild.name}")
        elif ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I'm not currently in a voice channel in this server.")

    @commands.command(name="stopplaying")
    async def stopplaying(self, ctx: commands.Context):
        """Stops any currently playing audio by the bot."""
        guild_id = ctx.guild.id
        vc = None
        if guild_id in self.active_sinks and self.active_sinks[guild_id].is_connected():
            vc = self.active_sinks[guild_id]
        elif ctx.voice_client:
            vc = ctx.voice_client

        if vc and vc.is_playing():
            vc.stop()
            await ctx.send("Stopped audio playback.")
        else:
            await ctx.send("I'm not playing any audio right now.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Listener to handle bot disconnecting if alone or on external disconnect."""
        if not member.id == self.bot.user.id:
            return

        guild_id = member.guild.id
        if before.channel and not after.channel: # Bot was disconnected
            if guild_id in self.active_sinks:
                print(f"Bot was disconnected from {before.channel.name}. Cleaning up sink for guild {guild_id}.")
                try:
                    if self.active_sinks[guild_id].is_connected(): # Check again before disconnecting
                         await self.active_sinks[guild_id].disconnect(force=True)
                except Exception as e:
                    print(f"Error during cleanup on_voice_state_update (external disconnect): {e}")
                finally:
                    # Ensure key is deleted even if disconnect fails (it might already be disconnected)
                    if guild_id in self.active_sinks:
                        del self.active_sinks[guild_id]

# --- Event Handlers ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f"Using Speech Recognition engine: {RECOGNIZER_ENGINE.capitalize()}")
    if not os.path.exists(MP3_FILE_PATH):
        print(f"WARNING: MP3 file '{MP3_FILE_PATH}' not found. Voice playback will fail.")
    else:
        print(f"MP3 file '{MP3_FILE_PATH}' found.")
    print(f"discord.py version: {discord.__version__}")
    if hasattr(voice_recv, '__version__'): # Check if __version__ exists
        print(f"discord-ext-voice-recv version: {voice_recv.__version__}")
    else:
        print(f"discord-ext-voice-recv version: (could not determine)") # Fallback
    print(f"SpeechRecognition version: {sr.__version__}")
    print(f"Bot is ready. Text keyword: '{TEXT_KEYWORD}'. Voice command: '!joinbased'.")
    print('------')

@bot.event
async def on_message(message: discord.Message):
    """
    Handles incoming messages for text-based keyword replies AND processes commands.
    """
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == bot.user:
        return

    # Convert message content to lowercase to make the check case-insensitive
    message_content_lower = message.content.lower()

    # --- Original Text-Based Reply Logic ---
    # Check if the text keyword is in the message content
    if TEXT_KEYWORD in message_content_lower:
        # Check if the message is a command invocation or part of one.
        # This is a simple check; more sophisticated checks might be needed if your prefix is common.
        is_command_attempt = False
        if bot.command_prefix: # Ensure command_prefix is not None
            prefixes = bot.command_prefix(bot, message) if callable(bot.command_prefix) else bot.command_prefix
            if isinstance(prefixes, str): # Single prefix
                if message.content.startswith(prefixes):
                    is_command_attempt = True
            elif isinstance(prefixes, (list, tuple)): # Multiple prefixes
                for pfx in prefixes:
                    if message.content.startswith(pfx):
                        is_command_attempt = True
                        break
        
        # Only reply if it's not primarily a command attempt that also happens to contain "based"
        # e.g., if "based" is part of a command name like "!basedcommand" and TEXT_KEYWORD is "based".
        # This logic can be adjusted based on how strictly you want to avoid replying to commands.
        # A simple heuristic: if the keyword isn't at the very start of what could be a command.
        if not is_command_attempt or (is_command_attempt and not message_content_lower.startswith(TEXT_KEYWORD, len(message.content.split(' ')[0]) - len(TEXT_KEYWORD) if message.content.split(' ') else 0 )):
            try:
                await message.reply(TEXT_KEYWORD) # Reply with the keyword itself
                print(f"Replied '{TEXT_KEYWORD}' to text message: '{message.content}' by {message.author.name} in #{message.channel.name}")
            except discord.Forbidden:
                print(f"Missing permissions to reply in channel: {message.channel.name} in server: {message.guild.name}")
            except Exception as e:
                print(f"An error occurred while trying to reply to text message: {e}")

    # --- Crucial for command processing ---
    # This line allows the bot to still process commands
    # after your custom on_message logic has run.
    await bot.process_commands(message)


async def main(token: str):
    """Main function to setup and run the bot."""
    async with bot:
        # Load cogs
        await bot.add_cog(VoiceListenerCog(bot))
        # Start the bot
        try:
            await bot.start(token)
        except discord.LoginFailure:
            print("----------------------------------------------------")
            print("Login Failed: Incorrect Bot Token.")
            print("Please ensure your BOT_TOKEN is correct and you have enabled necessary intents")
            print("in the Discord Developer Portal (Message Content, Voice States).")
            print("----------------------------------------------------")
        except Exception as e:
            print(f"An error occurred while trying to run the bot: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    # --- Command Line Argument Parsing ---
    parser = argparse.ArgumentParser(description="Discord bot that listens for 'based' in voice and text channels.")
    parser.add_argument("-t", "--token", required=True, help="The Discord bot token.")
    args = parser.parse_args()

    asyncio.run(main(args.token))
