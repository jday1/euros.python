import json
from datetime import datetime

from cloudpathlib import S3Path

BASE_PATH = S3Path("s3://user-jday/euros2024")
SYNTENY_PATH = BASE_PATH / "synteny"

FIXTURES_PATH = BASE_PATH / "fixtures.csv"
CUSTOM_ORDERING = BASE_PATH / "custom_ordering"


USER_CHOICES_STORE = SYNTENY_PATH / "choices"
USERS_PATH = SYNTENY_PATH / "users.json"

with open(USERS_PATH.fspath, 'r') as file:
    VALID_USERNAME_PASSWORD_PAIRS = json.load(file)

CUTOFF_TIME = datetime(2024, 5, 23, 18, 53)


def show_users() -> bool:
    return datetime.now() > CUTOFF_TIME

