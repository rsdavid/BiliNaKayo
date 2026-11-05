"""Turns the voiceover text into an mp3. Tries edge-tts first, then gTTS, then gives up quietly."""
import asyncio
from pathlib import Path

import config


def _edge(text, out):
    import edge_tts

    async def go():
        comm = edge_tts.Communicate(text, config.TTS_VOICE, rate=config.TTS_RATE, pitch=config.TTS_PITCH)
        await comm.save(str(out))

    asyncio.run(go())


def _gtts(text, out):
    from gtts import gTTS

    try:
        gTTS(text, lang="tl").save(str(out))  # Filipino
    except ValueError:
        gTTS(text, lang="en").save(str(out))


def synthesize(text, out_path):
    """Return the mp3 path, or None if no voice engine worked (video is then made without voiceover)."""
    out = Path(out_path)
    for name, engine in (("edge-tts", _edge), ("gTTS", _gtts)):
        try:
            engine(text, out)
            if out.exists() and out.stat().st_size > 2000:
                print(f"[voice] made voiceover with {name}")
                return out
        except Exception as exc:
            print(f"[voice] {name} failed: {exc}")
    print("[voice] no voice engine worked - video will have no voiceover")
    return None
