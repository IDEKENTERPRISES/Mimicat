import os
from typing import List
import discord
import requests
import asyncio
import aiohttp
import aiofiles
import random
import dotenv

dotenv.load_dotenv()

voicesRequest = requests.get("https://api.elevenlabs.io/v1/voices", headers={"accept": "application/json", "xi-api-key": os.environ.get('eleven_api_key')}).json()
voices = {}
for voice in voicesRequest['voices']:
    name = voice['name']
    voice_id = voice['voice_id']
    voices[name] = voice_id

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
commands = discord.app_commands.CommandTree(client)

queue = asyncio.Queue()
voice_client = None
filenames = []

@commands.command(name="vcmeow", description="Joins vc and plays the TTS of your message in the given voice.")
async def vcmeow(interaction: discord.Interaction, voice:str, prompt:str, stability:float = 0.5, similarity:float = 0.5):
    global voice_client
    global filenames
    global voices
    
    
    if (interaction.user.voice == None):
        await interaction.response.send_message("Join a VC!", ephemeral=True)
        return

    if voice_client is None:
        voice_client = await interaction.user.voice.channel.connect()

    if voice not in voices.keys():
        await interaction.response.send_message("Voice doesn't exist!", ephemeral=True)
        return
    
    filename = "generated/" + interaction.user.name + interaction.user.discriminator + str(random.randint(0,1024)) + ".mp3"
                        
    await interaction.response.defer(ephemeral=True, thinking=True)
    await download_audio("https://api.elevenlabs.io/v1/text-to-speech/" + voices[voice] + "/stream",
                         prompt, 
                         stability, 
                         similarity, 
                         filename)
    
    audio_source = discord.FFmpegPCMAudio(filename)
    
    # Enqueue the new audio source
    await queue.put(audio_source)
    filenames.append(filename)
    # If the voice client is not already playing, start playing the next source in the queue
    if not voice_client.is_playing():
        next_source = await queue.get()
        voice_client.play(next_source, after=lambda e: on_complete(e, interaction))
        await interaction.followup.send("Started the queue", ephemeral=True)
    else:
        await interaction.followup.send("Added to queue. Position: #" + str(queue.qsize()), ephemeral=True)

@vcmeow.autocomplete('voice')
async def voices_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[discord.app_commands.Choice[str]]:
    global voices
    
    return [
        discord.app_commands.Choice(name=voice, value=voice)
        for voice in list(voices.keys())[::-1] if current.lower() in voice.lower()
    ]

@commands.command(name="meow", description="Sends the TTS of your message in the given voice.")
async def meow(interaction: discord.Interaction, voice:str, prompt:str, stability:float = 0.5, similarity:float = 0.5):
    
    global voices

    if voice not in voices.keys():
        await interaction.response.send_message("Voice doesn't exist!", ephemeral=True)
        return
    
    eleven_headers = {
        "xi-api-key": os.environ.get('eleven_api_key'),
        "Content-Type": "application/json"
    }
    
    eleven_data = {
        "text": prompt,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity
        }
    }
    
    filename = "generated/" + interaction.user.name + interaction.user.discriminator + str(random.randint(0,1024)) + ".mp3"
                        
    await interaction.response.defer(ephemeral=False, thinking=True)
    await download_audio("https://api.elevenlabs.io/v1/text-to-speech/" + voices[voice] + "/stream",
                         prompt, 
                         stability, 
                         similarity, 
                         filename)
    
    await interaction.followup.send("<@"+str(interaction.user.id)+"> just meowed: " + prompt,
                                      file=discord.File(filename))
    # check if the file exists before attempting to delete it
    if os.path.exists(filename):
        os.remove(filename)
        print("File deleted successfully.")
    else:
        print("File does not exist.")
    
    
    

@meow.autocomplete('voice')
async def voices_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[discord.app_commands.Choice[str]]:
    global voices
    
    return [
        discord.app_commands.Choice(name=voice, value=voice)
        for voice in list(voices.keys())[::-1] if current.lower() in voice.lower()
    ]

# Define the callback function to disconnect from the voice channel
def on_complete(error, interaction):
    global voice_client
    global filenames
    filename = filenames.pop(0)

    # check if the file exists before attempting to delete it
    if os.path.exists(filename):
        os.remove(filename)
        print("File deleted successfully.")
    else:
        print("File does not exist.")
    
    if queue.empty():
        voice_client.loop.create_task(voice_client.disconnect())
        voice_client = None
    else:
        next_source = queue.get_nowait()
        voice_client.play(next_source, after=lambda e: on_complete(e, interaction))

async def download_audio(url, prompt, stability, similarity, filename):
    eleven_headers = {
        "xi-api-key": os.environ.get('eleven_api_key'),
        "Content-Type": "application/json"
    }
    
    eleven_data = {
        "text": prompt,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=eleven_headers, json=eleven_data) as resp:
            async with aiofiles.open(filename, 'wb') as f:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    await f.write(chunk)

@client.event
async def on_ready():
    await commands.sync()
    print(f'We have logged in as {client.user}')

client.run(os.environ.get('discord_bot_key'))