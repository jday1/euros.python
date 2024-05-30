import json
from datetime import datetime

import pandas as pd
from cloudpathlib import S3Path


def show_users(cutoff_time: datetime) -> bool:
    return datetime.now() > cutoff_time


def load_fixtures(base_path: S3Path) -> pd.DataFrame:
    # TODO - pandera?
    fixtures_path = base_path / "fixtures.csv"
    df = pd.read_csv(fixtures_path.fspath, keep_default_na=False)
    return df


def load_users(group: str, base_path: S3Path) -> dict:
    with open((base_path / group / "users.json").fspath, "r") as file:
        valid_username_password_pairs: dict = json.load(file)

    return valid_username_password_pairs
