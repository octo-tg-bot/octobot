Catalogs
=================
Catalogs are a really cool feature of OctoBot. They provide catalog-like (hence the name) access to function. If sent in normal chat/PM, bot will reply with the first result + pagination buttons, and in inline mode there would be a choice of options.

Implementing catalog
--------------------
For :class:`CatalogHandler` to work with your function, your function must accept five arguments:

1. Query (:class:`str`)
2. Index, from which iteration should start in your function (:class:`str`)
3. Recommended amount of items to return. Notice that in inline mode you can't have more than 50 results at a time (:class:`int`)
4. Bot (:class:`octobot.OctoBot`)
5. Context (:class:`octobot.Context`)

In return, function should return :class:`octobot.Catalog`, with following arguments:

1. :class:`list` of :class:`CatalogKeyArticle` or :class:`CatalogKeyPhoto` items
2. Amount of items that your function has (:class:`int`)

Example handler:

.. code-block:: python3

    CATALOG_MAX = 50


    @CatalogHandler(command="catalogtest", description="Test CatalogHandler")
    def test_catalog(query, index, max_amount, bot, context):
        res = []
        index = int(index)
        if index < 0:
            raise CatalogCantGoBackwards
        if index >= CATALOG_MAX:
            raise CatalogCantGoDeeper
        if max_amount > CATALOG_MAX:
            max_amount = CATALOG_MAX
        for i in range(0, max_amount):
            res.append(CatalogKeyPhoto(text=f"<b>{query}</b> <i>{i + index}</i>",
                                       title=f"Title for {query}",
                                       description=f"Description for {query}",
                                       parse_mode="HTML",
                                       photo=[CatalogPhoto(url=f"https://picsum.photos/seed/{query}{i + index}/200/200",
                                                           width=200,
                                                           height=200)]))
        return Catalog(res, CATALOG_MAX, current_index=index+1, next_offset=index+max_amount, previous_offset=index-max_amount)


Classes documentation
---------------------

.. autoclass:: octobot.CatalogHandler
    :members:

.. automodule:: octobot.classes.catalog
    :members:

Exceptions:
___________

.. autoclass:: octobot.exceptions.CatalogCantGoDeeper
    :members:

.. autoclass:: octobot.exceptions.CatalogCantGoBackwards
    :members:

.. autoclass:: octobot.exceptions.CatalogNotFound
    :members:

