from typing import Callable

import dash_bootstrap_components as dbc
import pandas as pd
from cloudpathlib import S3Path
from dash import dash_table, dcc, html

from euros.all_users import create_all_users
from euros.flags import FLAG_UNICODE


def load_user_choices(username: str, group: str, base_path: S3Path) -> list[dict]:

    user_choices_store = base_path / group / "choices"

    path: S3Path = user_choices_store / f"{username}.csv"

    if path.exists():
        df = pd.read_csv(path.fspath)
    else:
        df = pd.DataFrame([{"team": k, "tokens": 0} for k, _ in FLAG_UNICODE.items()])

    df["team"] = df["team"].apply(lambda x: x + " " + FLAG_UNICODE[x])

    records: list[dict] = df.to_dict("records")

    return records


def create_play_tab(username: str, group: str, base_path: S3Path, show_users: Callable, cutoff: str, user_choices: pd.DataFrame, fixtures: pd.DataFrame) -> dcc.Tab:

    do_show_users = show_users()

    choices_tab = [
        dash_table.DataTable(
            id="user-choices",
            data=load_user_choices(username, group, base_path),
            sort_action="native",
            sort_mode="multi",
            style_cell_conditional=[
                {
                    "if": {"column_id": "team"},
                    # "minWidth": "120px",
                    # "maxWidth": "120px",
                },
                {
                    "if": {"column_id": "tokens"},
                    # "minWidth": "50px",
                    # "maxWidth": "50px",
                },
            ],
            columns=[
                {"name": "team", "id": "team", "editable": False},
                {"name": "tokens", "id": "tokens", "type": "numeric"},
            ],
            editable=not do_show_users,
        ),
    ]

    if not do_show_users:
        choices_tab += [
            html.Br(),
            dbc.Button("Update Selection", id="update-button", color="primary"),
            html.Div(id="warning-text"),
        ]

    return dbc.Col(
        id="play-tab",
        children=[
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        children=[
                            html.H2(
                                f"Welcome {username}",
                            ),
                            html.H3("How to play"),
                            html.Ul(
                                [
                                    html.Br(),
                                    html.Li(
                                        f"Before the start of the first game ({cutoff}), "
                                        "you distribute 12 tokens across the 24 countries in the "
                                        "competition. The only restriction is that you cannot "
                                        "put all 12 tokens on a single country "
                                        "(i.e. minimum two countries, e.g. 11 votes on France and 1 vote "
                                        " England). You are now a shareholder in all the countries you've picked."
                                    ),
                                    html.Br(),
                                    html.Li(
                                        "Each time a country wins or draws a match, "
                                        "the country pays out a points dividend which is divided "
                                        "amongst all the shareholders in proportion to the number of shares they own, i.e. your points "
                                        "allocation = (Number of Shares Owned * dividend) / (Total Shares Owned)."
                                    ),
                                    html.Br(),
                                    html.Li(
                                        [
                                            "The point dividends are as follows:",
                                            html.Ul(
                                                [
                                                    html.Li("Group stage: Win = 1 point, Draw = 0.5, Loss = 0"),
                                                    html.Li("Round of 16: Win = 2 points, Loss = 0"),
                                                    html.Li("Quarter Finals: Win = 4 points, Loss = 0"),
                                                    html.Li("Semi-Finals: Win = 8 points, Loss = 0"),
                                                    html.Li("Final: Win = 16 points, Loss = 0"),
                                                ]
                                            ),
                                        ]
                                    ),
                                    html.Br(),
                                    html.Li(
                                        "The winner is the person with the most points at the end. No tie breaks. Glory can be shared."
                                    ),
                                ]
                            ),
                        ],
                        # width=7,
                    ),
                    dbc.Col(
                        children=choices_tab,
                        # width=5,
                    ),
                ],
            ),
            html.Br(),
            dbc.Row(
                (
                    create_all_users(user_choices.copy(deep=True), fixtures)
                    if do_show_users
                    else html.H3("Once they are finalised, everyone's choices will appear here.")
                ),
            ),
        ],
    )
