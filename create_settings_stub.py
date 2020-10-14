import pygenstub
import toml
import logging
logging.basicConfig(level=logging.DEBUG)

def create_stub_for_settings():
    with open("settings.base.toml") as f:
        settings = toml.load(f)
    with open("settings.py") as f:
        generator = pygenstub.StubGenerator(f.read(), True)
        for setting_name in settings:
            setting_type = type(settings[setting_name])
            generator.root.children[0].add_variable(pygenstub.VariableNode(setting_name, setting_type.__name__))
        generator.root.add_variable(pygenstub.VariableNode("Settings", "_Settings"))
        stub = generator.generate_stub()

    with open("settings.pyi", 'w') as f:
        print("Writing settings stub")
        f.write(stub)

if __name__ == '__main__':
    create_stub_for_settings()