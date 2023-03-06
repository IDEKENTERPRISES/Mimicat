# Discord bot that connects to the Eleven Labs API and generates TTS.

# Setup:
Make sure ffmpeg is in your PATH. It can be fetched here: [ffmpeg](https://www.gyan.dev/ffmpeg/builds/#git-master-builds)

Place your discord and elevenlabs token in a new file named .env and make two keys (eleven_api_key and discord_bot_key)

Python requirements are found in requirements.txt, simply do the following:
```
pip install -r requirements.txt
```

## Features:
*   Joins VC and plays TTS (_/vcmeow voice prompt similarity clarity_)
*   Queue system for TTS
*   Generates and sends TTS through chat (_/meow voice prompt similarity clarity_)
*   Autocompletes the voice parameter with whatever voices you have
*   (meow)

## Features I would like to add:
*   Connection to OpenAI's API to create a new /_(vc)mimic_ command
     * Would take the user's prompt and run it through OpenAI's ChatGPT API to then have the response read out.
