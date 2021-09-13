import logging

import requests

import threading
from queue import Queue, Empty

import octobot.enums

try:
    import preimport
except ModuleNotFoundError:
    logging.basicConfig(
        level=logging.DEBUG)  # We need SOME logging probably
import sys
import time

import telegram
import octobot
from settings import Settings
import logging

logger = logging.getLogger("Bot")


def update_loop(bot, queue):
    update_id = None
    bot.deleteWebhook()
    while True:
        try:
            logger.debug("Fetching updates...")
            for update in bot.getUpdates(update_id, timeout=15 if Settings.production else 1,
                                         allowed_updates=["message", "edited_message",
                                                          "inline_query", "callback_query",
                                                          "chosen_inline_result"]):
                update_id = update.update_id + 1
                logger.debug(update)
                queue.put((bot, update))
        except (telegram.error.TimedOut, telegram.error.NetworkError):
            time.sleep(1)
        except (telegram.error.RetryAfter) as e:
            time.sleep(e.retry_after + 1)
        except KeyboardInterrupt:
            logger.info("Update loop - stopping.")
            break


def update_handler(upd_queue: Queue, stop_event: threading.Event):
    stop_running = False
    while not stop_running:
        try:
            qupdate = upd_queue.get_nowait()
        except Empty:
            time.sleep(0.2)
        else:
            bot = qupdate[0]
            update: telegram.Update = qupdate[1]
            try:
                bot.handle_update(bot, update)
            except octobot.Halt:
                stop_event.set()
        stop_running = stop_event.is_set()
    logger.info("Stop event is set, exiting, exiting...")


STATES_EMOJIS = {
    octobot.enums.PluginStates.unknown: "❓",
    octobot.enums.PluginStates.error: "🐞",
    octobot.enums.PluginStates.notfound: "🧐",
    octobot.enums.PluginStates.loaded: "👌",
    octobot.enums.PluginStates.skipped: "⏩",
    octobot.enums.PluginStates.warning: "⚠️",
    octobot.enums.PluginStates.disabled: "🔽"
}


def create_startup_msg(bot):
    msg = "OctoBotV4 loaded."
    for plugin in bot.plugins.values():
        msg += f"\n{STATES_EMOJIS[plugin['state']]} {plugin['name']}"
        if plugin['state'] != octobot.enums.PluginStates.loaded:
            msg += f" - {plugin.state_description}"
    return msg


def create_threads():
    threads = []
    queue = Queue()
    stop_event = threading.Event()
    for i in range(Settings.threads):
        thread = threading.Thread(target=update_handler, args=(queue, stop_event), name=f"UpdateHandler{i}")
        threads.append(thread)
        thread.start()
    return threads, queue, stop_event


def main():
    if Settings.telegram_base_url != "https://api.telegram.org/bot":
        r = requests.get(f"https://api.telegram.org/bot{Settings.telegram_token}/logOut")
        logger.info("Using local bot API, logout result: %s", r.text)
    bot = octobot.OctoBot(sys.argv[1:], Settings.telegram_token, base_url=Settings.telegram_base_url,
                          base_file_url=Settings.telegram_base_file_url)
    bot.send_message(Settings.owner, create_startup_msg(bot))
    logger.info("Creating update handle threads...")
    if Settings.telegram_base_file_url_force:
        logger.warning("Forcefully overriding base url")
        bot.base_file_url = Settings.telegram_base_file_url
    threads, queue, stop_event = create_threads()
    logger.debug("API endpoint: %s", bot.base_url)
    logger.debug("API file endpoint: %s", bot.base_file_url)
    logger.info("Starting update loop.")
    update_loop(bot, queue)
    logger.info("Stopping...")
    stop_event.set()
    for thread in threads:
        logger.debug("Joining thread %s", thread)
        thread.join()
    logger.info("Bye!")
    sys.exit()


if __name__ == '__main__':
    main()
