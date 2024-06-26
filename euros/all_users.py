import pandas as pd
from cloudpathlib import S3Path
from dash import dash_table

from euros.config import load_users
from euros.flags import FLAG_UNICODE


def create_user_choices(group: str, base_path: S3Path) -> pd.DataFrame:
    user_choices = []

    user_choices_store = base_path / group / "choices"

    for user in load_users(group, base_path).keys():
        path: S3Path = user_choices_store / f"{user}.csv"

        if path.exists():
            df = pd.read_csv(path.fspath)
        else:
            df = pd.DataFrame([{"team": k, "tokens": 0} for k, _ in FLAG_UNICODE.items()])

        df["user"] = user.capitalize()
        user_choices.append(df)

    user_choices_df = pd.concat(user_choices).pivot(index="team", columns="user", values="tokens")

    user_choices_df["total"] = user_choices_df.sum(axis=1)

    user_choices_df = user_choices_df.reset_index()

    return user_choices_df


def create_all_users(user_choices: pd.DataFrame) -> dash_table.DataTable:

    user_choices["team"] = user_choices["team"].apply(lambda x: x + " " + FLAG_UNICODE[x])

    return dash_table.DataTable(
        id="all-users",
        data=user_choices.to_dict("records"),
        style_table={"overflowX": "auto", "width": "100%"},
    )
