# Python Bot to alert discord when specific levels have hit

# Getting Started

Make sure the machine has [TA-Lib](https://stackoverflow.com/questions/45406213/unable-to-install-ta-lib-on-ubuntu) installed. The bot uses this package in order to calculate EMA, RSA, etc. Also, make sure you have a [Polygon](https://polygon.io/) API Key, that's what the bot uses for market data.

## Setting environment variables

These variables MUST be set prior to running the bot

-   **CLIENT_SECRET** is the Discord Bot token
-   **APCA_API_KEY_ID** is the Polygon API key you are using
-   **WEBHOOK_URL** is where you would send the alerts to

After setting all that, run `python3 bot.py` to start running the bot.
