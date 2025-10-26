import tomllib

from personal_finance.data import create_accounts


def main():
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    accounts = create_accounts(config["balance_table"])
    ...
