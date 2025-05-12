import discord

BOT_TOKEN = 'FAKE_TOKEN'

# Define the intents your bot needs
# discord.py 2.0+ requires explicit intent declaration
intents = discord.Intents.default()
intents.messages = True  # To receive message events
# intents.message_content = True # To read message content (MUST be enabled in Developer Portal)

# Create a Discord client with the specified intents
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """
    This function is called when the bot has successfully connected to Discord.
    """
    print(f'Logged in as {client.user.name} (ID: {client.user.id})')
    print('Bot is ready to reply "based"!')
    print('------')

@client.event
async def on_message(message):
    """
    This function is called every time a message is sent in a channel the bot can see.
    """
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == client.user:
        return

    # Convert message content to lowercase to make the check case-insensitive
    message_content_lower = message.content.lower()

    # Check if the word "based" is in the message content
    if 'based' in message_content_lower:
        try:
            # Reply to the message
            await message.reply('based')
            print(f"Replied 'based' to message: '{message.content}' by {message.author.name}")
        except discord.Forbidden:
            print(f"Missing permissions to reply in channel: {message.channel.name} in server: {message.guild.name}")
        except Exception as e:
            print(f"An error occurred while trying to reply: {e}")

# Run the bot
if __name__ == '__main__':
    try:
        client.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("Login Failed: Make sure your bot token is correct and you have enabled necessary intents in the Discord Developer Portal.")
    except Exception as e:
        print(f"An error occurred while running the bot: {e}")
