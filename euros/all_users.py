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


def create_all_users(user_choices: pd.DataFrame, fixtures: pd.DataFrame) -> dash_table.DataTable:

    unplayed_fixtures = fixtures[fixtures["Result"] == ""]

    remaining_teams = pd.concat([unplayed_fixtures["Home Team"], unplayed_fixtures["Away Team"]]).drop_duplicates()

    remaining_points = user_choices[user_choices["team"].isin(remaining_teams)].sum()

    remaining_points["team"] = "Tokens Left"

    user_choices["team"] = user_choices["team"].apply(lambda x: x + " " + FLAG_UNICODE[x])

    table_data = pd.concat(
        [user_choices, remaining_points.to_frame().T],
        ignore_index=True,
    ).to_dict("records")

    return dash_table.DataTable(
        id="all-users",
        data=table_data,
        style_table={"overflowX": "auto", "width": "100%"},
        style_data_conditional=[
            {
                "if": {"row_index": len(table_data) - 1},
                "fontWeight": "bold",
                "borderBottom": "3px solid black",
                "borderTop": "3px solid black",
            }
        ],
    )
