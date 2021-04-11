Localization
============

Marking string to be "localizable"
----------------------------------

This can be used for command descriptions/long descriptions. Please use it only in there, all this function does is make the locale extractor extract the string.

.. automethod:: octobot.localization.localizable

Example:

.. code-block:: python3

    @CommandHandler(command="helloworld", description=localizable("Hello, World!"))
    def hello_world(bot, ctx):
        ctx.reply(ctx.localize("This is a test"))


Localizing strings
------------------

.. automethod:: octobot.Context.localize
    :noindex:

Generating localization files
_____________________________

To extract locale strings and/or compile .po files run the `utils/update_locale_data.cmd` file. Despite the fact it's .cmd, it only contains commands, so you are free to run it on macOS or Linux-based distros. Also notice that you need to run it every time you update locale strings or if it's first run of bot.

Creating your own locale
------------------------

To create your own locale you need:

1. Generate .po template using `utils/update_locale_data.cmd`
2. Create a folder in `locales` folder with your locale name according to this syntax: `locale_TERRITORY`. For example: `ru_RU`
3. Copy generated `base.pot` file to your `locale_TERRITORY/LC_MESSAGES/` folder and name it messages.po
4. Edit `messages.po` file. Be sure to edit first message string to include your locale name and feel free to credit yourself
5. To compile the strings in bot run `utils/update_locale_data.cmd`
