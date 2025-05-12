# BasedBot

A very stupid Discord bot that replies 'based' when the word is mentioned.

Almost entirely vibe coded. Use at your own risk.

Requires ffmpeg and the following Python deps:

```
pip install discord.py
pip install discord-ext-voice-recv
pip install SpeechRecognition
```

Took some tips from [here](https://www.reddit.com/r/Discord_Bots/comments/11n8hme/python_is_it_possible_to_retrieve_audio_source/) and [here](https://github.com/imayhaveborkedit/discord-ext-voice-recv/blob/main/examples/recv.py).

TODO: Make it actually work. Doesn't support the encryption protocol at the moment but based on [this](https://github.com/imayhaveborkedit/discord-ext-voice-recv/issues/26) and [this](https://github.com/imayhaveborkedit/discord-ext-voice-recv/issues/38) I just need to rebuild `discord-ext-voice-recv` from source.