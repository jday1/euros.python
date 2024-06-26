import copy

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from cloudpathlib import S3Path
from dash import dash_table, dcc, html

from euros.all_users import create_user_choices
from euros.config import load_fixtures

STANDINGS_COLOR_PALETTE = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Yellow-green
    "#17becf",  # Cyan
    "#2f4f4f",  # Slate
    "#ffbb78",  # Light orange
]


def get_wdl(result: str) -> str:
    if "(" in result:
        home, away = result.split("(")[1][:-1].split("-")
    else:
        home, away = result.split("-")

    if home > away:
        return "W"
    elif home < away:
        return "L"
    else:
        return "D"


def allocate_points(row: pd.Series) -> float:
    if row["Round Number"] in [str(x) for x in [1, 2, 3]]:
        if row["WDL"] == "W":
            return 1
        elif row["WDL"] == "D":
            return 0.5
        else:
            return 0

    if row["Round Number"] == "Round of 16":
        if row["WDL"] == "W":
            return 2
        else:
            return 0

    if row["Round Number"] == "Quarter Finals":
        if row["WDL"] == "W":
            return 4
        else:
            return 0

    if row["Round Number"] == "Semi Finals":
        if row["WDL"] == "W":
            return 8
        else:
            return 0

    if row["Round Number"] == "Final":
        if row["WDL"] == "W":
            return 16
        else:
            return 0

    else:
        raise ValueError(f"Unknown round number: {row['Round Number']}")


def get_standings(user_choices: pd.DataFrame, base_path: S3Path) -> pd.DataFrame | None:

    fixtures = load_fixtures(base_path)
    fixtures["Date"] = pd.to_datetime(fixtures["Date"], dayfirst=True)

    fixtures = fixtures[fixtures["Result"].str.contains("-")]

    fixtures["Home WDL"] = fixtures["Result"].apply(get_wdl)
    fixtures["Away WDL"] = fixtures["Home WDL"].apply(lambda x: "W" if x == "L" else "L" if x == "W" else "D")

    fixtures_home = fixtures[["Match Number", "Round Number", "Date", "Home Team", "Home WDL"]].rename(
        columns={"Home Team": "team", "Home WDL": "WDL"}
    )
    fixtures_away = fixtures[["Match Number", "Round Number", "Date", "Away Team", "Away WDL"]].rename(
        columns={"Away Team": "team", "Away WDL": "WDL"}
    )

    results: pd.DataFrame = pd.concat([fixtures_home, fixtures_away])

    if results.empty:
        return None

    results["Points To Allocate"] = results.apply(allocate_points, axis=1)

    user_choices.set_index("team", inplace=True)

    user_choices_cleaned = (
        user_choices.div(user_choices["total"], axis=0)
        .fillna(0)
        .drop("total", axis=1)
        .reset_index()
        .melt(id_vars="team", var_name="user", value_name="ownership")
    )

    merged_results = pd.merge(results, user_choices_cleaned, on=["team"], how="left")

    merged_results["points_allocated"] = merged_results["Points To Allocate"] * merged_results["ownership"]

    merged_results = pd.merge(
        merged_results, fixtures[["Match Number", "Home Team", "Away Team", "Result"]], on="Match Number", how="inner"
    )

    return merged_results


def create_figure(standings: pd.DataFrame) -> go.Figure:

    res = (
        standings.groupby(["Round Number", "Date", "user", "Match Number", "Home Team", "Away Team", "Result"])["points_allocated"]
        .sum()
        .reset_index()
    )

    res["Date"] = pd.to_datetime(res["Date"], dayfirst=True)
    df = res.sort_values(by=["user", "Round Number", "Date", "Match Number"])
    df["cumulative_points"] = df.groupby("user")["points_allocated"].cumsum()

    df["points_allocated_shown"] = df["points_allocated"].round(3)
    df["cumulative_points_shown"] = df["cumulative_points"].round(3)

    # Create traces for each user
    data = []
    for num, (user, group) in enumerate(df.groupby("user")):

        trace = go.Scatter(
            x=group["Date"],
            y=group["cumulative_points"],
            mode="lines+markers",
            name=user,
            line=dict(color=STANDINGS_COLOR_PALETTE[num % len(STANDINGS_COLOR_PALETTE)]),
            customdata=group,
            hovertemplate="<b>%{customdata[4]} %{customdata[6]} %{customdata[5]}</b>"
            + "<br><b>Points Gained: %{customdata[9]}</b>"
            + "<br><b>Cumulative Total: %{customdata[10]}</b>"
            + "<extra></extra>",
        )
        data.append(trace)

    layout = go.Layout(
        xaxis=dict(title="Date", range=["2024-06-14", "2024-07-14"], tickformat="%Y-%m-%d", tickangle=-45),
        yaxis=dict(title="Total Dividend"),
        # width=800,
        height=800,
    )

    fig = go.Figure(data=data, layout=layout)

    return fig


def create_current_standings(standings: pd.DataFrame) -> dash_table.DataTable:

    standings_table: pd.DataFrame = standings.groupby(["user"])["points_allocated"].sum().sort_values(ascending=False)

    df = standings_table.reset_index().reset_index().rename(columns={"index": "position"})
    df["position"] = df["position"] + 1

    df["points_allocated"] = df["points_allocated"].round(3)

    return dash_table.DataTable(
        id="current-standings",
        data=df.to_dict("records"),
        columns=[
            {"name": "Pos.", "id": "position"},
            {"name": "Name", "id": "user"},
            {"name": "Total Dividend", "id": "points_allocated"},
        ],
        style_cell_conditional=[
            {"if": {"column_id": "position"}, "minWidth": "20px", "maxWidth": "20px"},
            {"if": {"column_id": "user"}, "minWidth": "75px", "maxWidth": "75px"},
            {"if": {"column_id": "points_allocated"}, "minWidth": "75px", "maxWidth": "75px"},
        ],
        style_cell={
            "minWidth": "50px",
            "maxWidth": "50px",
        },
    )


def create_standings(
    standings_table: dash_table.DataTable,
    standings_figure: go.Figure,
    table_width: int,
    graph_width: int,
    static_plot: bool,
) -> list:

    return [
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    standings_table,
                    width=table_width,
                ),
                dbc.Col(
                    html.Div(
                        dcc.Graph(
                            figure=standings_figure,
                            style={"minWidth": "400px", "width": "100%"},
                            config={"staticPlot": static_plot},
                        ),
                        style={"overflowX": "auto"},
                    ),
                    width=graph_width,
                ),
            ],
            align="center",
        ),
    ]


def create_standings_tab(user_choices: pd.DataFrame, base_path: S3Path) -> html.Div:

    standings: pd.DataFrame | None = get_standings(user_choices.copy(deep=True), base_path=base_path)

    if standings is None:
        return dbc.Col(
            children=[
                html.Br(),
                html.H4("Standings will appear here after the first fixture completes."),
            ]
        )
    else:

        standings_table = create_current_standings(standings)
        standings_figure = create_figure(standings)

        standings_figure_small = copy.deepcopy(standings_figure)
        standings_figure_small.update_xaxes(autorange=True)

        return [
            dbc.Col(children=create_standings(standings_table, standings_figure, 4, 8, static_plot=False), className="large-standings"),
            dbc.Col(
                children=create_standings(standings_table, standings_figure_small, 12, 12, static_plot=True), className="small-standings"
            ),
        ]
