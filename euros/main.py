import copy
import tempfile
from argparse import ArgumentParser
from datetime import datetime
from functools import reduce
from pathlib import Path
from typing import Any

import dash
import dash_auth
import dash_bootstrap_components as dbc
import diskcache
import pandas as pd
import pytz
import yaml
from cloudpathlib import S3Client, S3Path
from dash import Dash, DiskcacheManager, Input, Output, State, dcc, html
from flask import Flask, request
from pydantic import BaseModel
from werkzeug.middleware.profiler import ProfilerMiddleware

from euros.all_users import create_user_choices
from euros.config import load_fixtures, load_users
from euros.fixtures import create_fixtures_tab
from euros.groups import create_groups_tab
from euros.knockout import create_knockout_tab
from euros.play import create_play_tab
from euros.standings import create_figure, create_standings_tab, get_standings


class Config(BaseModel):
    # Host config
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    app_name: str = "Euros"
    suppress_callback_exceptions: bool = True

    # Run config
    user_group: str
    base_path: str = "s3://user-jday/euros2024"
    profile: str
    cutoff_time: str = "2024-06-14 12:00:00"


def create_parser() -> ArgumentParser:
    """Parse cli for args."""
    parser = ArgumentParser(description="Euros 2024 Dash app.")
    parser.add_argument("--filepath", "-f", type=str, default="config filepath", help="host.")
    return parser


def create_config(filepath: str) -> Config:

    with open(filepath, "r") as f:
        data = yaml.safe_load(f)
        cfg = Config(**data)

    return cfg


def create_app(filepath: str) -> Dash:
    config = create_config(filepath)
    tmpdir = Path(tempfile.mkdtemp())
    cache = diskcache.Cache(tmpdir)
    background_callback_manager = DiskcacheManager(cache)
    app = Dash(
        name=config.app_name,
        external_stylesheets=[dbc.themes.LUX],
        background_callback_manager=background_callback_manager,
        suppress_callback_exceptions=config.suppress_callback_exceptions,
        title="Euros 2024",
        assets_folder=Path(__file__).parent / "assets",
    )

    base_path = S3Path(config.base_path, client=S3Client(profile_name=config.profile))

    user_choices = create_user_choices(group=config.user_group, base_path=base_path)

    cutoff_time = datetime.strptime(config.cutoff_time, "%Y-%m-%d %H:%M:%S").astimezone(pytz.timezone("Europe/London"))

    def show_users() -> bool:
        return datetime.now(pytz.timezone("Europe/London")) > cutoff_time

    dash_auth.BasicAuth(
        app,
        load_users(config.user_group, base_path=base_path),
        secret_key="kIwjEmZ4fuv09Gwb+5R7IkI2Ftl8JVcA10ExyQ81",
    )

    fixtures_df = load_fixtures(base_path)

    teams = [
        {"value": f"Team:{team}", "label": html.Span(team, style={"color": "blue"})}
        for team in pd.concat([fixtures_df["Home Team"], fixtures_df["Away Team"]]).unique().tolist()
    ]
    rounds = [
        {"value": f"Round Number:{match_round}", "label": html.Span(match_round, style={"color": "navy"})}
        for match_round in fixtures_df["Round Number"].unique().tolist()
    ]

    fixtures_filter_select = dcc.Dropdown(
        id="fixtures-filter-value",
        options=teams + rounds,
        persistence=True,
        persistence_type="memory",
        multi=True,
        placeholder="Filter fixtures by Team or Round",
    )
    fixtures_filter_button = dbc.Button(
        "Filter",
        id="fixtures-filter-button",
        color="primary",
    )

    def create_layout() -> dbc.Container:
        return dbc.Container(
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
                dbc.Row(id="tabs-content", justify="center"),
            ],
            style={"maxWidth": "1500px", "margin-top": "50px", "margin-bottom": "50px"},
            fluid=True,
        )

    # Define the layout
    app.layout = create_layout

    @app.callback(
        Output("fixtures-filter-table", "data"),
        Input("fixtures-filter-value", "value"),
        Input("fixtures-filter-button", "n_clicks"),
        State("fixtures-filter-table", "data"),
    )
    def update_fixture_filter_table(
        values: list[str] | None, fixtures_filter_button_n_clicks: int, previous_data: list[dict]
    ) -> list[dict]:

        # If the button exists, but is not clicked, return the current table - don't do anything!
        if (
            fixtures_filter_button_n_clicks is not None
            and fixtures_filter_button_n_clicks > 0
            and dash.callback_context.triggered[0]["prop_id"] == "fixtures-filter-value.value"
        ):
            return previous_data

        fixtures: pd.DataFrame = load_fixtures(base_path)

        if values is None or len(values) == 0:
            filtered_fixtures = fixtures
        else:

            values_split = [v.split(":") for v in values]

            team_values = []
            round_values = []

            for key, v in values_split:
                if key == "Team":
                    team_values.append(v)
                elif key == "Round Number":
                    round_values.append(v)
                else:
                    raise ValueError(f"Invalid key: {key}")

            if team_values:
                filtered_fixtures = fixtures[(fixtures["Home Team"].isin(team_values)) | (fixtures["Away Team"].isin(team_values))]
            else:
                filtered_fixtures = fixtures

            if round_values:
                filtered_fixtures = filtered_fixtures[filtered_fixtures["Round Number"].isin(round_values)]
            else:
                filtered_fixtures = filtered_fixtures

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
            return create_play_tab(
                username,
                config.user_group,
                base_path=base_path,
                show_users=show_users,
                cutoff=config.cutoff_time,
                user_choices=user_choices,
                fixtures=fixtures_df,
            )
        elif tab == "groups-tab":
            return create_groups_tab(base_path=base_path)
        elif tab == "knockout-tab":
            return create_knockout_tab(base_path=base_path)
        elif tab == "fixtures-tab":
            return create_fixtures_tab(
                fixtures_filter_table,
                fixtures_filter_select,
                fixtures_filter_button,
                user_choices=user_choices,
                show_users=show_users,
            )
        elif tab == "standings-tab":
            return create_standings_tab(
                user_choices=user_choices,
                base_path=base_path,
            )

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
    )
    def update_user_choices(n_clicks: int, data: list[dict], username: str) -> dbc.FormText:
        if n_clicks is None:
            return html.Br()

        df = pd.DataFrame(data)

        tokens = df["tokens"]

        font_size = "14px"

        if (tokens.astype(int) != tokens).all():
            return dbc.FormText("Please enter integers only", color="red", style={"fontSize": font_size})

        if not ((tokens >= 0) & (tokens <= 11)).all():
            return dbc.FormText("Please enter values between 0 and 11", color="red", style={"fontSize": font_size})

        if tokens.sum() != 12:
            return dbc.FormText("Token values must sum to 12", color="red", style={"fontSize": font_size})

        try:
            df["team"] = df["team"].apply(lambda x: " ".join(x.split(" ")[:-1]))

            tmpdir = Path(tempfile.mkdtemp())
            tmpfile = tmpdir / "choices.csv"
            df.to_csv(tmpfile, index=False)

            (base_path / config.user_group / "choices" / f"{username}.csv").upload_from(tmpfile, force_overwrite_to_cloud=True)

            return dbc.FormText("Updated selection successfully.", color="blue", style={"fontSize": font_size})
        except Exception as e:
            print(e)
            return dbc.FormText("Something went wrong", color="red", style={"fontSize": font_size})

    if config.debug:
        PROF_DIR = "local/dash_profiler"
        Path(PROF_DIR).mkdir(parents=True, exist_ok=True)
        app.server.wsgi_app = ProfilerMiddleware(
            app.server.wsgi_app, sort_by=("cumtime", "tottime"), restrictions=[50], stream=None, profile_dir=PROF_DIR
        )

    @app.callback(
        Output("standings-graph", "figure"),
        Output("standings-graph-static", "figure"),
        Input("standings-x-axis", "value"),
        Input("standings-y-axis", "value"),
        prevent_initial_call=True,
    )
    def update_standing_figure(x_axis: str, y_axis: str):
        standings: pd.DataFrame | None = get_standings(user_choices.copy(deep=True), base_path=base_path)

        standings_figure = create_figure(standings, x_axis, y_axis)

        standings_figure_small = copy.deepcopy(standings_figure)
        standings_figure_small.update_xaxes(autorange=True)

        return standings_figure, standings_figure_small

    return app, config


def server(filepath) -> Flask:
    app: Dash
    config: Config
    app, config = create_app(filepath)
    server: Flask = app.server
    return server


def main() -> None:
    args = create_parser().parse_args()
    app: Dash
    config: Config
    app, config = create_app(args.filepath)
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
