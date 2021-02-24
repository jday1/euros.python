import pandas as pd
from dash import dash_table

from euros.flags import FLAG_UNICODE


def create_all_users(
    user_choices: pd.DataFrame, fixtures: pd.DataFrame
) -> dash_table.DataTable:
    """Create a table of all users and their token choices."""
    unplayed_fixtures = fixtures[fixtures["Result"] == ""]

    remaining_teams = pd.concat(
        [unplayed_fixtures["Home Team"], unplayed_fixtures["Away Team"]]
    ).drop_duplicates()

    remaining_points = user_choices[user_choices["team"].isin(remaining_teams)].sum()

    remaining_points["team"] = "Tokens Left"

    user_choices["team"] = user_choices["team"].apply(
        lambda x: x + " " + FLAG_UNICODE[x]
    )

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
