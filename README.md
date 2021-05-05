# Python Bot to alert discord when specific levels have hit

# Getting Started
Make sure you have an [Alpaca](https://alpaca.markets/) API Key, that is how ths bot gathers data. THe bot is ran and tested on Python 3.8. To upgrade, please take a look at [this](https://tech.serhatteker.com/post/2020-09/how-to-install-python39-on-ubuntu/) guide.

## Setting environment variables

These variables MUST be set prior to running the bot

-   **CLIENT_SECRET** Discord Bot token


### If using alpaca
-   **APCA_API_KEY_ID** Alpaca client key
- 	**APCA_API_PRIVATE_KEY** Alpaca private key 

### If using TD Ameritrade
- **TDAMERITRADE_CLIENT_ID** Consumer key from [TDApps](https://developer.tdameritrade.com/user/me/apps)

- **TDAMERITRADE_ACCOUNT_ID** Can be just 1

- **TDAMERITRADE_REFRESH_TOKEN** Refresh token by invoking `get_td_auth` script

After setting all that, run `python3 bot.py` to start running the bot.

### How to install TA-Lib on Ubuntu 20
`$ curl -L http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz --output ta-lib-0.4.0-src.tar.gz`

`$ tar -xvf ta-lib-0.4.0-src.tar.gz`

`$ cd ta-lib/`

`$ sudo apt install build-essential`

`$ ./configure --prefix=/usr`

`$ make`

`$ sudo make install`

`$ sudo apt upgrade`

## Run the bot
Tested on Ubuntu 20.04 Google Cloud Server.

If you do not have pip installed, run

`$ sudo apt install python3-pip`

then,

`$ pip3 install -r requirements.txt`

`$ source init.sh`

^ Note: This is the shell script with your env variables

`$ python3 bot.py`