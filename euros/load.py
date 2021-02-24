import json
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytz
import yaml
from pydantic import BaseModel, field_validator

from euros.flags import FLAG_UNICODE


class Loader(BaseModel):
    """Config class for the Euros app."""

    # Host config
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    app_name: str = "Euros"
    suppress_callback_exceptions: bool = False

    # Run config
    user_group: str
    base_path: Path
    cutoff_time: datetime

    @field_validator("base_path")
    def check_base_path(cls, base_path: Path) -> Path:
        """Check that the base path exists."""
        if not base_path.exists():
            raise ValueError(f"Path {base_path} does not exist.")
        return base_path

    def show_users(self) -> bool:
        """Determines if all users tokens should be shown on the frontend."""
        return datetime.now(pytz.timezone("Europe/London")) > self.cutoff_time

    def load_fixtures(self) -> list[dict]:
        """Load the fixtures from the csv file and add basic columns used elsewhere."""
        fixtures_path = self.base_path / "fixtures.csv"

        df = pd.read_csv(fixtures_path, keep_default_na=False)

        df["Home Team Short"] = df["Home Team"].apply(self._get_short_team)
        df["Away Team Short"] = df["Away Team"].apply(self._get_short_team)
        df["Home Team Long"] = df["Home Team"].apply(self._get_long_team)
        df["Away Team Long"] = df["Away Team"].apply(self._get_long_team)

        # Convert the date column to datetime format
        df["datestamp"] = df["Date"].apply(lambda x: x.split(" ")[0])
        df["timestamp"] = df["Date"].apply(lambda x: x.split(" ")[1])
        df["datestamp"] = pd.to_datetime(df["datestamp"], dayfirst=True)

        table: list[dict] = df.to_dict("records")

        return table

    def _get_short_team(self, team: str) -> str:
        if "Winner Match" in team:
            return team.replace("Winner Match", "MW")
        elif FLAG_UNICODE.get(team) is not None:
            return team[:3] + " " + FLAG_UNICODE[team]
        else:
            return team

    def _get_long_team(self, team: str) -> str:
        if (flag := FLAG_UNICODE.get(team)) is not None:
            return team + " " + flag
        else:
            return team

    def create_user_choices(self) -> pd.DataFrame:
        """Create the user choices dataframe."""
        user_choices = []

        user_choices_store = self.base_path / self.user_group / "choices"

        for user in self.load_users().keys():
            path: Path = user_choices_store / f"{user}.csv"

            if path.exists():
                df = pd.read_csv(path)
            else:
                df = pd.DataFrame(
                    [{"team": k, "tokens": 0} for k, _ in FLAG_UNICODE.items()]
                )

            df["user"] = user.capitalize()
            user_choices.append(df)

        user_choices_df = pd.concat(user_choices)

        return user_choices_df

    def custom_orderings(self) -> dict[str, list[str]]:
        """Load the custom orderings from the csv files.

        Required if there is an unexpected ordering of the teams in the group tables.
        """
        custom_order_files = (self.base_path / "custom_orderings").glob(".csv")

        custom_orderings: dict[str, list[str]] = {
            path.name.strip(".csv"): pd.read_csv(path, header=None)[0].tolist()
            for path in custom_order_files
        }

        return custom_orderings

    def load_users(self) -> dict[str, str]:
        """Load the valid username password pairs from the users.json file."""
        with open(self.base_path / self.user_group / "users.json") as file:
            valid_username_password_pairs: dict = json.load(file)

        return valid_username_password_pairs

    def choices_path(self, username: str) -> Path:
        """Return the path to the user's choices csv file."""
        return self.base_path / self.user_group / "choices" / f"{username}.csv"


def create_parser() -> ArgumentParser:
    """Parse cli for args."""
    parser = ArgumentParser(description="Euros 2024 Dash app.")
    parser.add_argument(
        "--filepath", "-f", type=str, default="config filepath", help="host."
    )
    return parser


def create_loader(filepath: Path) -> Loader:
    """Create the loader object by parsing config from a yaml file."""
    with open(filepath) as f:
        data = yaml.safe_load(f)
        cfg = Loader(**data)

    return cfg
