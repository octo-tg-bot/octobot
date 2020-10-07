import threading
from queue import Queue, Empty

try:
    import preimport
except ModuleNotFoundError:
    pass
else:
    preimport.preimport()
import sys
import time

import telegram
import octobot
from settings import Settings
import logging

logger = logging.getLogger("Bot")


def update_loop(bot, queue, run_event):
    update_id = None
    bot.deleteWebhook()
    while run_event.is_set():
        try:
            for update in bot.getUpdates(update_id, timeout=2):
                update_id = update.update_id + 1
                queue.put((bot, update))
        except telegram.error.TimedOut:
            time.sleep(1)


def update_handler(upd_queue: Queue, run_event: threading.Event):
    while run_event.is_set():
        try:
            update = upd_queue.get_nowait()
        except Empty:
            time.sleep(0.2)
        else:
            bot, update = update
            try:
                bot.handle_update(bot, update)
            except octobot.Halt:
                run_event.clear()


STATES_EMOJIS = {
    octobot.PluginStates.unknown: "❓",
    octobot.PluginStates.error: "🐞",
    octobot.PluginStates.notfound: "🧐",
    octobot.PluginStates.loaded: "👌",
    octobot.PluginStates.skipped: "⏩"
}


def create_startup_msg(bot):
    msg = "OctoBotV4 loaded."
    for plugin in bot.plugins.values():
        msg += f"\n{STATES_EMOJIS[plugin['state']]} {plugin['name']}"
        if plugin['state'] in [octobot.PluginStates.error, octobot.PluginStates.skipped]:
            msg += f" - {plugin.get('exception', 'skipped')}"
    return msg


def create_threads():
    threads = []
    queue = Queue()
    run_event = threading.Event()
    run_event.set()
    for i in range(Settings.threads):
        thread = threading.Thread(target=update_handler, args=(queue, run_event))
        threads.append(thread)
        thread.start()
    return threads, queue, run_event


def main():
    bot = octobot.OctoBot(sys.argv[1:], Settings.telegram_token)

    bot.send_message(Settings.owner, create_startup_msg(bot))
    logger.info("Creating update handle threads...")
    threads, queue, run_event = create_threads()

    logger.info("Starting update loop.")
    try:
        update_loop(bot, queue, run_event)
    except (KeyboardInterrupt, octobot.Halt):
        logger.info("Stopping...")
        run_event.clear()
        for thread in threads:
            logger.debug("Joining thread %s", thread)
            thread.join()
        logger.info("Bye!")
        sys.exit()


if __name__ == '__main__':
    main()
