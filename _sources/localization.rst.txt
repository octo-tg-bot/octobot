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

There are two ways to add your locale:

- The easy way, using POEditor
- The hard way, manually creating locale files

The easy way
____________

1. Ask in telegram chat or in github issues for developer to create locale for your language
2. Get translating at `POEditor <https://poeditor.com/join/project?hash=P2Yx5Sp1GA>`_!

.. note::
   If for some reason your language isn't available at POEditor, you can use hard way.

The hard way
____________

1. Generate .po template using `utils/update_locale_data.cmd`
2. Create a folder in `locales` folder with your locale name from `POEditor locale list <https://poeditor.com/docs/languages>`_. If your language isn't on POEditor list, name it following way: `language-territory`
3. Copy generated `base.pot` file to your `locale-territory/LC_MESSAGES/` folder and name it messages.po
4. Edit `messages.po` file. Be sure to edit first message string to include your locale name and feel free to credit yourself
5. `Submit a pull request to repository <https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests>`_
