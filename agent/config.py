import os


class Config:
    """Application configuration pulled from environment variables.

    The Agent component uses config values to connect to Twitch, determine
    which chat keywords should be watched for, and where to send events via
    a websocket client.  Environment variables are documented in the
    README and may also be loaded via a .env file if the user prefers.
    """

    def __init__(self):
        # twitch IRC credentials
        self.twitch_oauth_token = os.getenv("TWITCH_OAUTH_TOKEN", "")
        self.twitch_nick = os.getenv("TWITCH_NICK", "")
        self.twitch_channel = os.getenv("TWITCH_CHANNEL", "")

        # comma-separated list of keywords to watch for in chat messages
        self.chat_keywords = [kw.strip() for kw in os.getenv("CHAT_KEYWORDS", "").split(",") if kw.strip()]

        # how many messages within the interval before a "chat_spam" event
        # is emitted (default 20 per minute)
        try:
            self.chat_frequency_threshold = int(os.getenv("CHAT_FREQ_THRESHOLD", "20"))
        except ValueError:
            self.chat_frequency_threshold = 20

        # websocket server url the listener should connect to
        self.websocket_url = os.getenv("WEBSOCKET_URL", "http://localhost:3001")

        # directory where OBS saves replay files (optional)
        self.clip_dir = os.getenv("CLIP_DIR", "")

        # audio detection settings
        # RMS threshold to trigger an "audio_spike" event (0.0-1.0)
        try:
            self.audio_threshold = float(os.getenv("AUDIO_THRESHOLD", "0.1"))
        except ValueError:
            self.audio_threshold = 0.1
        # sample rate and block size for the input stream
        try:
            self.audio_samplerate = int(os.getenv("AUDIO_SAMPLERATE", "44100"))
        except ValueError:
            self.audio_samplerate = 44100
        try:
            self.audio_blocksize = int(os.getenv("AUDIO_BLOCKSIZE", "1024"))
        except ValueError:
            self.audio_blocksize = 1024

    @classmethod
    def from_env(cls):
        """Convenience constructor for external modules."""
        return cls()
