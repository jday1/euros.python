from cloudpathlib import S3Path
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, html

from euros.config import load_fixtures
from euros.flags import FLAG_UNICODE


def get_points(home_score: str | int, away_score: str | int) -> pd.Series:
    if home_score == "-":
        return pd.Series([0, 0])

    assert isinstance(home_score, int) and isinstance(away_score, int)

    if home_score > away_score:
        return pd.Series([3, 0])
    elif home_score < away_score:
        return pd.Series([0, 3])
    else:
        return pd.Series([1, 1])


def order_table(group_standing: pd.DataFrame, custom_order_path: S3Path | None) -> pd.DataFrame:

    if custom_order_path is not None:
        custom_order = pd.read_csv(custom_order_path.fspath, header=None)[0].tolist()
        group_standing["team"] = pd.Categorical(group_standing["team"], categories=custom_order, ordered=True)
        group_standing.sort_values("team", inplace=True)
        group_standing.reset_index(drop=True, inplace=True)
    else:
        group_standing.sort_values(["points", "goals difference", "goals for"], ascending=[False, False, False], inplace=True)
        group_standing.reset_index(drop=True, inplace=True)

    group_standing.reset_index(inplace=True)
    group_standing.rename(columns={"index": "position"}, inplace=True)
    group_standing["position"] = group_standing["position"] + 1

    return group_standing


def create_table(group: str, fixtures: pd.DataFrame, custom_order_path: S3Path | None) -> pd.DataFrame:

    group_fixtures = fixtures[fixtures["Group"] == f"Group {group}"]

    group_fixtures.loc[:, ["Home Score"]] = group_fixtures["Result"].apply(lambda x: int(x.split("-")[0]) if isinstance(x, str) and x != "" else "-")
    group_fixtures.loc[:, ["Away Score"]] = group_fixtures["Result"].apply(lambda x: int(x.split("-")[1]) if isinstance(x, str) and x != "" else "-")

    group_fixtures.loc[:, ["Home Points", "Away Points"]] = group_fixtures.apply(
        lambda row: get_points(home_score=row["Home Score"], away_score=row["Away Score"]),
        axis=1,
    )

    home_points = group_fixtures[["Home Team", "Home Points"]].groupby("Home Team").sum()["Home Points"]
    away_points = group_fixtures[["Away Team", "Away Points"]].groupby("Away Team").sum()["Away Points"]

    team_points = home_points + away_points

    group_fixtures.loc[:, "Home Score"] = group_fixtures["Home Score"].apply(lambda x: 0 if x == "-" else x)
    group_fixtures.loc[:, "Away Score"] = group_fixtures["Away Score"].apply(lambda x: 0 if x == "-" else x)

    home_total_goals_for = group_fixtures[["Home Team", "Home Score"]].groupby("Home Team").sum()["Home Score"]
    away_total_goals_for = group_fixtures[["Away Team", "Away Score"]].groupby("Away Team").sum()["Away Score"]

    team_goals_for = home_total_goals_for + away_total_goals_for

    home_total_goals_against = group_fixtures[["Home Team", "Away Score"]].groupby("Home Team").sum()["Away Score"]
    away_total_goals_against = group_fixtures[["Away Team", "Home Score"]].groupby("Away Team").sum()["Home Score"]

    team_goals_against = home_total_goals_against + away_total_goals_against

    group_standing = pd.DataFrame([team_points, team_goals_for, team_goals_against])

    group_standing = group_standing.T.rename(columns={0: "points", 1: "goals for", 2: "goals against"})

    group_standing["goals difference"] = group_standing["goals for"] - group_standing["goals against"]

    group_standing = group_standing.reset_index().rename(columns={"Home Team": "team"})

    group_standing = order_table(group_standing, custom_order_path)

    group_standing["team"] = group_standing["team"].apply(lambda team: team + " " + FLAG_UNICODE[team])

    return group_standing


def make_table(group: str, fixtures: pd.DataFrame, custom_order_path: S3Path | None) -> dash_table.DataTable:
    return dash_table.DataTable(
        id=f"group-table-{group}",
        data=create_table(group, fixtures, custom_order_path).to_dict("records"),
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
    )


def create_groups_tab(base_path: S3Path) -> html.Div:

    fixtures = load_fixtures(base_path)

    custom_order_path: S3Path = base_path / "custom_ordering"

    paths: dict[str, S3Path] = {path.name.strip(".csv"): path for path in custom_order_path.glob("*.csv")}

    return html.Div(
        id="group-tab",
        children=[
            html.Br(),
            dbc.Row([dbc.Col(make_table(i, fixtures, paths.get(i))) for i in "AB"]),
            html.Br(),
            dbc.Row([dbc.Col(make_table(i, fixtures, paths.get(i))) for i in "CD"]),
            html.Br(),
            dbc.Row([dbc.Col(make_table(i, fixtures, paths.get(i))) for i in "EF"]),
        ],
    )
