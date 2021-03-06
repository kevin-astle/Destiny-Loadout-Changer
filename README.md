# Destiny-Loadout-Changer
Twitch chat integration for allowing chat users to change the player's weapons.

## Initial setup
There are a number of setup steps that need to be carefully followed:
* Copy config.json.sample to config.json. You will replace the values in this file with personalized values based on the next steps
* Create a new account for the bot, or log in to an existing account
* Get an oauth code from https://twitchapps.com/tmi and add it to your config.json file
* Register your bot with Twitch:
  + Go to https://dev.twitch.tv/console/apps/create and authorize
  + Choose a name for your bot, set the OAuth Redirect URL to http://localhost (it doesn't matter what it is, but you need to put something there), and select "Game Integration as the category
  + Copy the client_id into your config.json file
* Change "bot_nickname" in the config.json file to the name of the channel you registered your bot for
* Change "channel" in the config.json file to the name of the channel you want the bot to be chatting in
* Get access to the Bungie API:
  + Go to https://www.bungie.net/developer
  + Click "Create New App
  + Give it a name
  + Select "Confidential" for the OAuth Client Type
  + Set Redirect URL to https://localhost:<port>/oauth, replacing <port> with whatever port you want. For example, 4949.
  + Change "oauth_port" in the config.json file to the port you chose in the previous step, if other than 4949
  + Under scope, check the following boxes:
    - Read your Destiny 2 information (Vault, Inventory, and Vendors), as well as Destiny 1 Vault and Inventory data. 
    -	Move or equip Destiny gear and other items.
  + Check the box saying you agree to the terms of use, then click "Create New App"
  + Under the API Keys section, you will see several values. These need to be copied into your config.json:
    - Replace "bungie_api_key" with the API Key value
    - Replace "oauth_client_id" with the OAuth client_id value
    - Replace "oauth_client_secret" with the OAuth client_secret value

**Note:** in config.json, "bungie_membership_type" represents the platform the user plays on. This is 254 for Bungie.net/Steam, 1 for Playstation, and 2 for Xbox. This has only been tested for PC players, so the default value is 254. I have no idea what will happen if you try to use this for players on consoles, it might work or it might not. If you try it, you will likely need to change this value to either 1 or 2. I also don't know how cross-save factors into this, so it's possible that the bot will not work for players who started on one platform and them moved to another platform.

## Starting the bot
Before you can run the bot, you must first have installed Python 3.7+ (https://www.python.org/downloads), and install the required Python packages listed in requirements.txt. This can be accomplished by running ``pip install -r requirements.txt`` in the root of the repository.

After this is done, you should be able to start the bot by executing ``main.py`` with Python, e.g. `python main.py`.

At this point, you should see a message posted in the Twitch channel chat, with the following contents: "Bot is online. You should have been directed to the Bungie oauth approval page". 

When the script was started, it should have opened the Bungie oauth page in your default web browser. Click approve, after which you will likely see a warning from your web browser. This is because Bungie requires oauth redirects to go to an https site, but getting a signed SSL certificate is beyond the scope of what anyone using this bot would want to do, and so the flask webserver is started using a self-signed certificate. The result is that, while the webserver can accept https requests, to your browser it looks like you are being redirected to a page with an untrusted security certificate. There should be an option somewhere on the page to ignore the warning, click that and you will see a confirmation page saying that the bot has received the oauth code and is ready for use. The bot will also post in the Twitch channel saying that it is ready. At this point, you can now start using the commands described below.

**Note:** It seems like there should be a way to save the oauth code and reuse it in future sessions, but I found that I got an authorization error if I tried to use the same oauth code after restarting the script. Therefore, every time you start the bot, you will need to perform the authorization.

## Twitch chat commands
The following commands are available to use:

### !help
A short description of the available commands.

### !equip \<name\> \<slot\> \<type\>
Equip a weapon, either by name or by slot and/or type.

When matching by name, partial matches are accepted. If multiple matches are found, a random one will be selected and equipped.

When matching by slot/type, you may specify either the slot, the type, or neither. If neither are specified, then a random weapon will be equipped in a random slot. 

The bot inspects the command and tries to determine if it is a request to equip by name, or by weapon slot/type.

Caveats when equipping by name:
* There is no protection against equipping an exotic when there is already an exotic equipped in another slot. For example, if there is an exotic in the kinetic slot, and you type ``!equip cold`` to equip Cold Front (forgetting about the existence of Coldheart), and the bot chooses and tries to equip Coldheart, it will fail.

Caveats when equipping by slot/type:
* If weapon slot is not specified, and an exotic weapon is equipped, then exotic weapons will be ignored when selecting.
* If weapon slot is specified, but an exotic weapon is equipped in one of the other two slots, then exotic weapons will be ignored when selecting.

#### Example usage
``!equip the jade rabbit``: Will equip "The Jade Rabbit", because this is an exact match.

``!equip rabbit``: Will also equip "The Jade Rabbit", because that is the only weapon which contains "rabbit" in the name.

``!equip tool``: Will equip one of the MIDA Multi-Tool, MIDA Mini-Tool, or CALUS Mini-Tool. All matching weapons are given the same weighting, so if the player has 1 MIDA Multi-Tool, 1 MIDA Mini-Tool, and 10 CALUS Mini-Tools, then it is most likely that a CALUS Mini-Tool will be selected and equipped.

``!equip a``: Will equip a random weapon that contains the letter "A" anywhere in the name.

``!equip``: Equips a random weapon of any type in any slot.

``!equip energy``: Equips a random weapon in the energy slot.

``!equip bow``: Equips a random bow in any slot.

``!equip kinetic pulse``: Equips a random kinetic pulse rifle.


Valid values for the slot:
* kinetic
* energy
* power OR heavy

Valid values for the type:
* auto OR autorifle
* shotgun
* machinegun
* handcannon
* rocketlauncher
* fusion OR fusionrifle
* sniper OR sniperrifle
* pulse OR pulserifle
* scout OR scoutrifle
* sidearm
* sword
* linearfusion OR linearfusionrifle
* grenadelauncher
* smg OR submachinegun
* tracerifle
* bow

### !search	\<name\> \<slot\> \<type\>
Search for and display all weapons matching the given criteria. The format is exactly the same as for the !equip command. If the output is larger than 500 characters, it will be truncated.

#### Example usage

Output from ``!search jade rabbit``:

    Weapons with names matching "jade rabbit" (1 match): The Jade Rabbit

Output from ``!search tool``:

    Weapons with names matching "tool" (2 matches): CALUS Mini-Tool x9, MIDA Multi-Tool

Output from ``!search kinetic`` (note the truncation):

    Weapons of type Kinetic (55 matches): Atalanta-D XG1992, Austringer, Baligant XU7743, Better Devils, Bite of the Fox, Blast Furnace, BrayTech Werewolf, Bygones x2, Cold Front x2, Dire Promise, Dust Rock Blues, Escape Velocity, Ether Doctor, Exit Strategy, Foregone Conclusion, Ghost Primus, Go Figure x2, Halfdan-D, Hawthorne's Field-Forged Shotgun x4, Horror Story, Imperative, Imperial Decree x2, Khvostov 7G-02, Lonesome, Long Shadow x2, MIDA Multi-Tool, Nameless Midnight x2, Night Watch, Nigh...

## General Caveats
* Weapons cannot be equipped mid-activity. They will, however, be moved to the player's inventory.
* There's some weirdness in the Destiny API that seems to result in stale inventory data being returned on occasion. This causes errors where the bot tries to move a weapon to/from the vault that is no longer there. There is a retry mechanism in place which mostly fixes this, but sometimes equip operations will still fail.
* This should go without saying, but if a weapon is not in a player's inventory or vault (e.g. they never had it or it's been dismantled), it cannot be equipped. There is no way to pull from Collections using the API. 

If you find any bugs, please open a new issue.