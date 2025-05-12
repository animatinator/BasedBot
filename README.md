# BasedBot

A very stupid Discord bot that replies 'based' when the word is mentioned.

Almost entirely vibe coded. Use at your own risk.

Requires ffmpeg and the following Python deps:

```
pip install discord.py
pip install discord-ext-voice-recv
pip install SpeechRecognition
```

TODO: Make it actually work. Doesn't support the encryption protocol at the moment but based on [this](https://github.com/imayhaveborkedit/discord-ext-voice-recv/issues/26) and [this](https://github.com/imayhaveborkedit/discord-ext-voice-recv/issues/38) I just need to rebuild `discord-ext-voice-recv` from source.