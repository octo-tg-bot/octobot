@echo off
pybabel extract plugins base_plugins -o locales/base.pot -k localize -k nlocalize
pybabel update -d locales -i locales/base.pot
pybabel compile -d locales