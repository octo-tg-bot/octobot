import toml
import os, shutil
import unittest
import settings
import logging
import unittest
unittest.TestLoader.sortTestMethodsUsing = None

logging.basicConfig(level=logging.DEBUG)


def create_test_settings():
    os.makedirs("tests/testdata", exist_ok=True)
    for file in ["settings.toml", "settings.base.toml"]:
        with open(f"tests/testdata/{file}", 'w') as f:
            toml.dump({"file": file}, f)


class SettingsTest(unittest.TestCase):
    def test_envsettings(self):
        create_test_settings()
        os.environ["ob_file"] = '"environment"'
        settings_instance = settings._Settings("tests/testdata")
        self.assertEqual("environment", settings_instance.file)

    def test_filesettings(self):
        create_test_settings()
        if "ob_file" in os.environ:
            del os.environ["ob_file"]
        settings_instance = settings._Settings("tests/testdata")
        self.assertEqual("settings.toml", settings_instance.file)



if __name__ == '__main__':
    unittest.main()
