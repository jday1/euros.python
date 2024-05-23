from pathlib import Path
import time
from cloudpathlib import S3Path
from dash import Dash, DiskcacheManager, Input, Output, State, dash_table, dcc, html
import pandas as pd

from euros.config import USER_CHOICES_STORE
from euros.flags import FLAG_UNICODE
from euros.config import VALID_USERNAME_PASSWORD_PAIRS


def create_user_choices() -> dash_table.DataTable:
    user_choices = []

    for user in VALID_USERNAME_PASSWORD_PAIRS.keys():
        path: S3Path = USER_CHOICES_STORE / f"{user}.csv"

        if path.exists():
            df = pd.read_csv(path.fspath)
        else:
            df = pd.DataFrame([{"team": k, "tokens": 0} for k, v in FLAG_UNICODE.items()])

        df["user"] = user.capitalize()
        user_choices.append(df)

    user_choices_df = pd.concat(user_choices).pivot(index="team", columns="user", values="tokens")

    user_choices_df["total"] = user_choices_df.sum(axis=1)

    user_choices_df = user_choices_df.reset_index()

    return user_choices_df


def create_all_users() -> dash_table.DataTable:
    user_choices_df = create_user_choices()

    user_choices_df["team"] = user_choices_df["team"].apply(lambda x: x + " " + FLAG_UNICODE[x])

    return dash_table.DataTable(
        id="all-users",
        data=user_choices_df.to_dict("records"),
        style_cell_conditional=[
            {
                "if": {"column_id": "team"},
                "minWidth": "100px",
                "maxWidth": "100px",
            },
        ],
        style_cell={
            "minWidth": "50px",
            "maxWidth": "50px",
        },
    )
