import pygenstub
import toml
import logging

logging.basicConfig(level=logging.DEBUG)


def create_vnode(setting_name, setting_value, generator, children=None):
    setting_type = type(setting_value)
    isdict = False
    if setting_type == dict:
        isdict = True
        setting_type = f"dict_{setting_name}"
    else:
        setting_type = setting_type.__name__
    if children is None:
        children = generator.root.children[0]
    children.add_variable(pygenstub.VariableNode(setting_name, setting_type))
    if isdict:
        node = pygenstub.ClassNode(setting_type, bases=("dotdict",))
        for key, value in setting_value.items():
            create_vnode(key, value, generator, node)
        generator.root.add_child(node)


def create_stub_for_settings():
    with open("settings.base.toml") as f:
        settings = toml.load(f)
    with open("settings.py") as f:
        generator = pygenstub.StubGenerator(f.read(), True)
        for setting_name in settings:
            print("Creating node for", setting_name)
            create_vnode(setting_name, settings[setting_name], generator)
        generator.root.add_variable(pygenstub.VariableNode("Settings", "_Settings"))
        stub = generator.generate_stub()

    with open("settings.pyi", 'w') as f:
        print("Writing settings stub")
        f.write(stub)


if __name__ == '__main__':
    create_stub_for_settings()
