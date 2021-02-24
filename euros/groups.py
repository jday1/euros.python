import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, html

from euros.flags import FLAG_UNICODE


def get_points(home_score: str | int, away_score: str | int) -> pd.Series:
    """Get the points for a match."""
    if home_score == "-":
        return pd.Series([0, 0], index=["Home Points", "Away Points"])

    assert isinstance(home_score, int) and isinstance(away_score, int)

    if home_score > away_score:
        return pd.Series([3, 0], index=["Home Points", "Away Points"])
    elif home_score < away_score:
        return pd.Series([0, 3], index=["Home Points", "Away Points"])
    else:
        return pd.Series([1, 1], index=["Home Points", "Away Points"])


def order_table(
    group_standing: pd.DataFrame, custom_ordering: list[str] | None
) -> pd.DataFrame:
    """Order the table based on the points, goals difference and goals for.

    If custom_ordering is provided, order the table based on that.
    """
    if custom_ordering:
        group_standing["team"] = pd.Categorical(
            group_standing["team"], categories=custom_ordering, ordered=True
        )
        group_standing.sort_values("team", inplace=True)
        group_standing.reset_index(drop=True, inplace=True)
    else:
        group_standing.sort_values(
            ["points", "goals difference", "goals for"],
            ascending=[False, False, False],
            inplace=True,
        )
        group_standing.reset_index(drop=True, inplace=True)

    group_standing.reset_index(inplace=True)
    group_standing.rename(columns={"index": "position"}, inplace=True)
    group_standing["position"] = group_standing["position"] + 1

    return group_standing


def create_table(
    group: str, fixtures: pd.DataFrame, custom_ordering: list[str] | None
) -> pd.DataFrame:
    """Create a dataframe of a group's standings."""
    group_fixtures = fixtures[fixtures["Group"] == f"Group {group}"]

    group_fixtures.loc[:, ["Home Score"]] = group_fixtures["Result"].apply(
        lambda x: int(x.split("-")[0]) if isinstance(x, str) and x != "" else "-"
    )
    group_fixtures.loc[:, ["Away Score"]] = group_fixtures["Result"].apply(
        lambda x: int(x.split("-")[1]) if isinstance(x, str) and x != "" else "-"
    )
    group_fixtures.loc[:, ["Home Points", "Away Points"]] = group_fixtures.apply(
        lambda row: get_points(
            home_score=row["Home Score"], away_score=row["Away Score"]
        ),
        axis=1,
    )

    home_points = (
        group_fixtures[["Home Team", "Home Points"]]
        .groupby("Home Team")
        .sum()["Home Points"]
    )
    away_points = (
        group_fixtures[["Away Team", "Away Points"]]
        .groupby("Away Team")
        .sum()["Away Points"]
    )

    team_points = home_points + away_points

    group_fixtures.loc[:, "Home Score"] = group_fixtures["Home Score"].apply(
        lambda x: 0 if x == "-" else x
    )
    group_fixtures.loc[:, "Away Score"] = group_fixtures["Away Score"].apply(
        lambda x: 0 if x == "-" else x
    )

    home_total_goals_for = (
        group_fixtures[["Home Team", "Home Score"]]
        .groupby("Home Team")
        .sum()["Home Score"]
    )
    away_total_goals_for = (
        group_fixtures[["Away Team", "Away Score"]]
        .groupby("Away Team")
        .sum()["Away Score"]
    )

    team_goals_for = home_total_goals_for + away_total_goals_for

    home_total_goals_against = (
        group_fixtures[["Home Team", "Away Score"]]
        .groupby("Home Team")
        .sum()["Away Score"]
    )
    away_total_goals_against = (
        group_fixtures[["Away Team", "Home Score"]]
        .groupby("Away Team")
        .sum()["Home Score"]
    )

    team_goals_against = home_total_goals_against + away_total_goals_against

    group_standing = pd.DataFrame([team_points, team_goals_for, team_goals_against])

    group_standing = group_standing.T.rename(
        columns={0: "points", 1: "goals for", 2: "goals against"}
    )

    group_standing["goals difference"] = (
        group_standing["goals for"] - group_standing["goals against"]
    )

    group_standing = group_standing.reset_index().rename(columns={"Home Team": "team"})

    group_standing = order_table(group_standing, custom_ordering)

    group_standing["team"] = group_standing["team"].apply(
        lambda team: team + " " + FLAG_UNICODE[team]
    )

    return group_standing


def make_table(
    group: str, fixtures: pd.DataFrame, custom_ordering: list[str] | None
) -> dash_table.DataTable:
    """Create a table of a group's standings."""
    return dash_table.DataTable(
        id=f"group-table-{group}",
        data=create_table(group, fixtures, custom_ordering).to_dict("records"),
        sort_action="native",
        sort_mode="multi",
        columns=[
            {"name": "pos.", "id": "position"},
            {"name": f"Group {group}", "id": "team"},
            {"name": "points", "id": "points"},
            {"name": "+/-G", "id": "goals difference"},
            {"name": "+G", "id": "goals for"},
        ],
        style_cell_conditional=[
            {"if": {"column_id": "position"}, "minWidth": "25px", "maxWidth": "25px"},
            {"if": {"column_id": "team"}, "minWidth": "120px", "maxWidth": "120px"},
            {"if": {"column_id": "points"}, "minWidth": "50px", "maxWidth": "50px"},
            {
                "if": {"column_id": "goals difference"},
                "minWidth": "50px",
                "maxWidth": "50px",
            },
            {"if": {"column_id": "goals for"}, "minWidth": "50px", "maxWidth": "50px"},
            {
                "if": {"column_id": "goals against"},
                "minWidth": "50px",
                "maxWidth": "50px",
            },
        ],
        style_table={"overflowX": "auto", "width": "100%"},
    )


def create_groups_tab(
    fixtures: pd.DataFrame, custom_orderings: dict[str, list[str]]
) -> dbc.Col:
    """Create the groups tab frontend."""
    return dbc.Col(
        children=[
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        children=[
                            make_table(i, fixtures, custom_orderings.get(i)),
                            html.Br(),
                        ]
                    )
                    for i in "AB"
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        children=[
                            make_table(i, fixtures, custom_orderings.get(i)),
                            html.Br(),
                        ]
                    )
                    for i in "CD"
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        children=[
                            make_table(i, fixtures, custom_orderings.get(i)),
                            html.Br(),
                        ]
                    )
                    for i in "EF"
                ]
            ),
        ],
    )
