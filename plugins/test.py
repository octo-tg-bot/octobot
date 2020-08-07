from octobot.handlers import CommandHandler


@CommandHandler(command="test", description="Test")
def test(bot, context):
    context.reply("Hello world!")

@CommandHandler(command="imgtest", description="Test image handling")
def imgtest(bot, context):
    context.reply("Test!", photo_url="https://via.placeholder.com/150")

@CommandHandler(command="bigimg", description="Really big image")
def longimg(bot, context):
    context.reply("Test!", photo_url="https://picsum.photos/seed/picsum/6000/6000")

@CommandHandler(command="longimg", description="Really long image")
def longimg(bot, context):
    context.reply("Test!", photo_url="https://picsum.photos/seed/picsum/5000/50")

@CommandHandler(command="tallimg", description="Really tall image")
def longimg(bot, context):
    context.reply("Test!", photo_url="https://picsum.photos/seed/picsum/50/5000")
