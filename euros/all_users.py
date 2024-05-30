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


def create_all_users(group: str, base_path: S3Path) -> dash_table.DataTable:
    user_choices_df = create_user_choices(group, base_path)

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