import octobot as ob

import logging


if __name__ == '__main__':
    host = "127.0.0.1" if ob.settings.webhook.ngrok else "0.0.0.0"
    if ob.settings.production:
        # gunicorn here
        pass
    else:
        import uvicorn
        from uvicorn.config import LOGGING_CONFIG
        LOGGING_CONFIG["loggers"] = {"": {"handlers": [
            "default"], "level": ob.settings.log_level}}
        LOGGING_CONFIG["formatters"]["default"]["()"] = "octobot.logger.CustomFormatter"
        del LOGGING_CONFIG["formatters"]["default"]["use_colors"]
        uvicorn.run("octobot.web:app", host=host,
                    port=ob.settings.webhook.internal_port, log_level=ob.settings.log_level, reload=True)
