Key-value database
==================

Accessing through the Context class
-----------------------------------

The :class:`octobot.Context` provides quick "shortcut" to per-user (:obj:`octobot.Context.user_db`) and
per-chat (:obj:`octobot.Context.chat_db`) databases

Accessing manually
------------------

The key-value database can be accessed manually, per chat_id:

.. code-block:: python3

    import octobot

    octobot.Database[777000]["key"] = "value"

    print(octobot.Database[777000]["key"])

Key-value database classes
__________________________

.. autoclass:: octobot.database.RedisData
    :members:

.. autoclass:: octobot.database._Database
    :members:
