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