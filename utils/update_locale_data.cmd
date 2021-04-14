pybabel extract plugins base_plugins octobot --no-default-keywords -o locales/base.pot -k localize -k nlocalize:1,2 -k localizable
pybabel update -d locales -i locales/base.pot -N
pybabel compile -d locales