import os
import tempfile
from functools import reduce
from pathlib import Path
import time
from typing import Any

import dash_auth
import dash_bootstrap_components as dbc
import diskcache
import pandas as pd
from clearml import Task
from cloudpathlib import S3Path
from dash import Dash, DiskcacheManager, Input, Output, State, dcc, html
from flask import request
from pydantic import BaseModel
from werkzeug.middleware.profiler import ProfilerMiddleware

from euros.config import load_fixtures, load_users
from euros.fixtures import create_fixtures_tab
from euros.groups import create_groups_tab
from euros.knockout import create_knockout_tab
from euros.play import create_play_tab
from euros.standings import create_standings_tab


PROF_DIR = "local/dash_profiler"


class Config(BaseModel):
    # Host config
    host: str
    port: int
    debug: bool
    app_name: str
    suppress_callback_exceptions: bool

    # ClearML
    clearml: bool

    # Run config
    user_group: str
    base_path: S3Path


def run(config: Config) -> None:

    tmpdir = Path(tempfile.mkdtemp())
    cache = diskcache.Cache(tmpdir)
    background_callback_manager = DiskcacheManager(cache)
    app_name = config.app_name
    app = Dash(
        name=app_name,
        external_stylesheets=[dbc.themes.LUX],
        background_callback_manager=background_callback_manager,
        suppress_callback_exceptions=config.suppress_callback_exceptions,
    )

    base_path = config.base_path

    user_group = config.user_group

    dash_auth.BasicAuth(
        app,
        load_users(user_group, base_path=base_path),
        secret_key="kIwjEmZ4fuv09Gwb+5R7IkI2Ftl8JVcA10ExyQ81",
    )

    fixtures = load_fixtures(base_path)[["Home Team", "Away Team"]]
    fixtures_formatted = pd.DataFrame(pd.concat([fixtures["Home Team"], fixtures["Away Team"]]).unique(), columns=["label"])
    fixtures_formatted["value"] = fixtures_formatted["label"]

    fixtures_filter_select = dcc.Dropdown(
        id="fixtures-filter-value",
        options=fixtures_formatted.to_dict("records"),
        persistence=True,
        persistence_type="memory",
        multi=True,
        placeholder="Filter fixtures by Team",
    )

    # Define the layout
    app.layout = dbc.Container(
        [
            dcc.Store(id="username"),
            dcc.Store(id="username-dummy-trigger"),
            dcc.Store(id="fixtures-filter-table", data=load_fixtures(base_path).to_dict("records")),
            html.H2("Euros"),
            dcc.Tabs(
                [
                    dcc.Tab(label="Play", id="play-tab", value="play-tab"),
                    dcc.Tab(label="Groups", id="groups-tab", value="groups-tab"),
                    dcc.Tab(label="Knockout", id="knockout-tab", value="knockout-tab"),
                    dcc.Tab(label="Fixtures", id="fixtures-tab", value="fixtures-tab"),
                    dcc.Tab(label="Standings", id="standings-tab", value="standings-tab"),
                ],
                id="tabs",
                value="play-tab",
            ),
            html.Div(id="tabs-content"),
        ],
        style={"width": "2000px", "margin-top": "50px", "margin-bottom": "50px"},
    )

    @app.callback(
        Output("fixtures-filter-table", "data"),
        Input("fixtures-filter-value", "value"),
    )
    def update_fixture_filter_table(value: list[dict] | None) -> list[dict]:

        fixtures: pd.DataFrame = load_fixtures(base_path)

        if value is None or len(value) == 0:
            filtered_fixtures = fixtures
        else:
            condition = reduce(
                lambda acc, col: acc | fixtures[col].isin(value), ["Home Team", "Away Team"], pd.Series([False] * len(fixtures))
            )

            filtered_fixtures = fixtures[condition]

        filtered_fixtures_table: list[dict] = filtered_fixtures.to_dict("records")

        return filtered_fixtures_table

    @app.callback(
        Output("tabs-content", "children"),
        Input("tabs", "value"),
        Input("username", "data"),
        Input("fixtures-filter-table", "data"),
        prevent_initial_call=True,
        background_callback_manager=background_callback_manager,
    )
    def render_content(tab: str, username: str, fixtures_filter_table: list[dict]) -> html.Div:

        if tab == "play-tab":
            return create_play_tab(username, user_group, base_path=base_path)
        elif tab == "groups-tab":
            return create_groups_tab(base_path=base_path)
        elif tab == "knockout-tab":
            return create_knockout_tab(base_path=base_path)
        elif tab == "fixtures-tab":
            return create_fixtures_tab(fixtures_filter_table, fixtures_filter_select, base_path=base_path)
        elif tab == "standings-tab":
            return create_standings_tab(group=user_group, base_path=base_path)

    @app.callback(
        Output(component_id="username", component_property="data"),
        Input(component_id="username-dummy-trigger", component_property="data"),
    )
    def get_username(username_dummy_trigger: Any) -> str | None:
        auth = request.authorization

        if auth is None:
            return None
        else:
            username: str | None = auth["username"]
            return username

    @app.callback(
        Output(
            component_id="warning-text",
            component_property="children",
        ),
        Input(component_id="update-button", component_property="n_clicks"),
        State(component_id="user-choices", component_property="data"),
        State(component_id="username", component_property="data"),
        prevent_initial_call=True,
    )
    def update_user_choices(n_clicks: int, data: list[dict], username: str) -> dbc.FormText:
        if n_clicks is None:
            return []

        df = pd.DataFrame(data)

        tokens = df["tokens"]

        if (tokens.astype(int) != tokens).all():
            return dbc.FormText("Please enter integers only", color="red")

        if not ((tokens >= 0) & (tokens <= 11)).all():
            return dbc.FormText("Please enter values between 0 and 11", color="red")

        if tokens.sum() != 12:
            return dbc.FormText("Token values must sum to 12", color="red")

        try:
            df["team"] = df["team"].apply(lambda x: " ".join(x.split(" ")[:-1]))

            df.to_csv("choices.csv", index=False)

            (base_path / user_group / f"{username}.csv").upload_from("choices.csv")

            return dbc.FormText("Updated selection successfully.", color="blue")
        except Exception as e:
            print(e)
            return dbc.FormText("Something went wrong", color="red")

    if config.debug:
        Path(PROF_DIR).mkdir(parents=True, exist_ok=True)
        app.server.wsgi_app = ProfilerMiddleware(
            app.server.wsgi_app, sort_by=("cumtime", "tottime"), restrictions=[50], stream=None, profile_dir=PROF_DIR
        )

    app.run(host=config.host, debug=config.debug, port=config.port)


def parse_config() -> Config:

    cfg = {
        "host": "0.0.0.0",
        "port": 8050,
        "debug": True,
        "app_name": "Euros",
        "suppress_callback_exceptions": True,
        "user_group": "synteny",
        "base_path": S3Path("s3://user-jday/euros2024"),
    }

    return Config(**cfg)


def main() -> None:
    config = parse_config()

    run(config)


if __name__ == "__main__":
    main()