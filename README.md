# PyBrowser

![License](https://img.shields.io/github/license/EpicGamerCodes/PyBrowser) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/EpicGamerCodes/PyBrowser) ![Current Release](https://img.shields.io/github/v/release/EpicGamerCodes/PyBrowser) ![Total Downloads](https://img.shields.io/github/downloads/EpicGamerCodes/PyBrowser/total)

This is a custom PyQt5 browser created for bypassing restrictions that are placed on normal browsers.
This program is mainly designed to combat Smoothwall and AB Tutor.

This is done by having a custom API Server to return proxy's for the browser to connect to to bypass the Smoothwall. The App title and icon can be masked as well known apps to hide the application from AB Tutor.

This program can also have a whitelist of users who can use it, causing trouble for people who run it without having permission. This "trouble" is either instantly shutting down their device or slowing it down so much they would want to shut it down.
By creating your own API Server, you can also create your own list of users who are allowed to use the program.

## Features

- Nearly everything is configured using config.json
- Mask the app as another app
- Ad blocking
- Proxy server for requests
- Confusing not allowed users
- Light/dark mode

## Installation

Grab a compiled version of PyBrowser from the [Releases Page](https://github.com/epicgamercodes/pybrowser/releases) or use it from the stable source code:

```bash
git clone https://github.com/epicgamercodes/pybrowser
cd PyBrowser
py -m pip install -r requirements.txt
cd PyBrowser
py main.py
```

## Creating a custom configuration

As stated above, nearly everything can be changed using the config.json file, so you don't need to edit main.py and merge commits on new updates, just config.json.

For example, if you wanted to create a custom mask and make the new mask the default, you would do this:

1) Add the icons to images/icons
2) Open config.py and goto line 11
3) To now add the mask as a CLI option, under the "masks" key, add:

```json
"call-sign": [
    "App Name",
    "App Organisation",
    "App Domain",
    "64x64 Icon.png",
    "128x128 Icon.png"
]
```

4) To make this the default mask, change the "mask" value under the "default" key:

```json
"mask": "call-sign"
````

5) Run config.py and if asked, answer any prompts:

```bash
py config.py
```

Using config.py to create a new configuration is recommended as this helps to when updating your config and also signs your config with extra data to help the program detect any issues.

## CLI Arguments

- mask (str, optional): How to hide the browser. Defaults to value in config.json. Options in config.json.
- new_proxy (str, optional): Proxy to use. Defaults to API Server Provided.
- api (str, optional): What API Server to use. Defaults to value in config.json.
- connect (bool, optional): Enable connections to the API Server (will also disbale proxy changes). Defaults to value in config.json.
- theme (str, optional): Dark or Light theme to use for the app. Defaults to value in config.json.
- adblock (bool, optional): Enable or disable adblocking in the browser. Defaults to value in config.json.
- debug (bool, optional): Print debug logging. Defaults to False.
- qapp_flags (str, optional): Flags to pass to QApplication. Defaults to value in config.json.

## API Server

This is used by the program to check versions, provide downloads, verify users and to send proxy servers.

The source code for the API Server can be found at <https://github.com/epicgamercodes/pybrowser-api-server>.

## FAQ

### Are there ways to bypass the user whitelist?

Yes, by providing the '--connect False' CLI option, the app disables any connections to the API Server. If you do not like this, you can always change the config.json to ignore this option.

### Can I change the ad blocker?

Yes, the default is provided is [AdAway's hosts.txt](https://adaway.org/hosts.txt) but you can change this by editing [your custom API Server](https://github.com/epicgamercodes/pybrowser-api-server).

## License

[GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/)
