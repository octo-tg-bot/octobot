try:
    import octobot
    from plugins import test

except ModuleNotFoundError:
    import sys
    import os

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(SCRIPT_DIR))
    import octobot
    from plugins import test


def test_commandhanlder():
    assert isinstance(test.test, octobot.CommandHandler)
