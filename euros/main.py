import copy
import tempfile
from pathlib import Path
from typing import Any

import dash_auth
import dash_bootstrap_components as dbc
import diskcache
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, DiskcacheManager, Input, Output, State, dcc, html
from flask import Flask, request

from euros.fixtures import create_fixtures_tab
from euros.groups import create_groups_tab
from euros.knockout import create_knockout_tab
from euros.load import Loader, create_loader, create_parser
from euros.play import create_play_tab
from euros.standings import create_figure, create_standings_tab, get_standings


def create_app(filepath: str) -> Dash:
    """Create the Dash app."""
    load: Loader = create_loader(Path(filepath))
    tmpdir = Path(tempfile.mkdtemp())
    cache = diskcache.Cache(tmpdir)
    background_callback_manager = DiskcacheManager(cache)
    app = Dash(
        name=load.app_name,
        external_stylesheets=[dbc.themes.LUX],
        background_callback_manager=background_callback_manager,
        suppress_callback_exceptions=load.suppress_callback_exceptions,
        title="Euros 2024",
        assets_folder=Path(__file__).parent / "assets",
    )

    dash_auth.BasicAuth(
        app,
        load.load_users(),
        secret_key="kIwjEmZ4fuv09Gwb+5R7IkI2Ftl8JVcA10ExyQ81",
    )

    fixtures_df = pd.DataFrame(load.load_fixtures())

    teams = [
        {
            "value": f"Team:{team}",  # noqa: E231
            "label": html.Span(team, style={"color": "blue"}),
        }
        for team in pd.concat([fixtures_df["Home Team"], fixtures_df["Away Team"]])
        .unique()
        .tolist()
    ]
    rounds = [
        {
            "value": f"Round Number:{match_round}",  # noqa: E231
            "label": html.Span(match_round, style={"color": "navy"}),
        }
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

    def create_layout() -> dbc.Container:
        return dbc.Container(
            [
                dcc.Store(id="show-users", data=load.show_users()),
                dcc.Store(id="username"),
                dcc.Store(id="username-dummy-trigger"),
                dcc.Store(
                    id="fixtures-filter-table",
                    data=load.load_fixtures(),
                ),
                dcc.Store(
                    id="fixtures-table",
                    data=load.load_fixtures(),
                ),
                dcc.Store(
                    id="user-choices",
                    data=load.create_user_choices().to_dict("records"),
                ),
                html.H2("Euros"),
                dcc.Tabs(
                    [
                        dcc.Tab(label="Play", id="play-tab", value="play-tab"),
                        dcc.Tab(label="Groups", id="groups-tab", value="groups-tab"),
                        dcc.Tab(
                            label="Knockout", id="knockout-tab", value="knockout-tab"
                        ),
                        dcc.Tab(
                            label="Fixtures", id="fixtures-tab", value="fixtures-tab"
                        ),
                        dcc.Tab(
                            label="Standings", id="standings-tab", value="standings-tab"
                        ),
                    ],
                    id="tabs",
                    value="play-tab",
                ),
                dbc.Row(id="tabs-content", justify="center"),
            ],
            style={"maxWidth": "1500px", "margin-top": "50px", "margin-bottom": "50px"},
            fluid=True,
        )

    @app.callback(
        Output("tabs-content", "children"),
        Input("tabs", "value"),
        Input("username", "data"),
        Input("fixtures-filter-table", "data"),
        Input("fixtures-table", "data"),
        Input("show-users", "data"),
        State("user-choices", "data"),
        prevent_initial_call=True,
        background_callback_manager=background_callback_manager,
    )
    def render_content(
        tab: str,
        username: str,
        fixtures_filter_table: list[dict],
        fixtures_table: list[dict],
        show_users: bool,
        user_choices: list[dict],
    ) -> html.Div:
        fixtures: pd.DataFrame = pd.DataFrame(fixtures_table)

        user_choices = pd.DataFrame(user_choices)

        if tab == "play-tab":
            return create_play_tab(
                username,
                load.user_group,
                base_path=load.base_path,  # TODO
                show_users=show_users,
                cutoff=load.cutoff_time,
                user_choices=user_choices,
                fixtures=fixtures,
            )
        elif tab == "groups-tab":
            return create_groups_tab(
                fixtures=fixtures, custom_orderings=load.custom_orderings()
            )
        elif tab == "knockout-tab":
            return create_knockout_tab(fixtures=fixtures)
        elif tab == "fixtures-tab":
            fixtures_filtered = pd.DataFrame(fixtures_filter_table)

            return create_fixtures_tab(
                fixtures_filtered,
                fixtures_filter_select,
                user_choices=user_choices,
                show_users=show_users,
            )
        elif tab == "standings-tab":
            return create_standings_tab(
                user_choices=user_choices,
                fixtures=fixtures,
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
    def update_user_choices(
        n_clicks: int, data: list[dict], username: str
    ) -> dbc.FormText:
        if n_clicks is None:
            return html.Br()

        df = pd.DataFrame(data)

        tokens = df["tokens"]

        font_size = "14px"

        if (tokens.astype(int) != tokens).all():
            return dbc.FormText(
                "Please enter integers only", color="red", style={"fontSize": font_size}
            )

        if not ((tokens >= 0) & (tokens <= 11)).all():
            return dbc.FormText(
                "Please enter values between 0 and 11",
                color="red",
                style={"fontSize": font_size},
            )

        if tokens.sum() != 12:
            return dbc.FormText(
                "Token values must sum to 12",
                color="red",
                style={"fontSize": font_size},
            )

        try:
            df["team"] = df["team"].apply(lambda x: " ".join(x.split(" ")[:-1]))

            user_choices_filepath = load.choices_path(username)

            df.to_csv(user_choices_filepath, index=False)

            return dbc.FormText(
                "Updated selection successfully.",
                color="blue",
                style={"fontSize": font_size},
            )
        except Exception as e:
            print(e)
            return dbc.FormText(
                "Something went wrong", color="red", style={"fontSize": font_size}
            )

    # if config.debug:
    #     PROF_DIR = "local/dash_profiler"
    #     Path(PROF_DIR).mkdir(parents=True, exist_ok=True)
    #     app.server.wsgi_app = ProfilerMiddleware(
    #         app.server.wsgi_app,
    #         sort_by=("cumtime", "tottime"),
    #         restrictions=[50],
    #         stream=None,
    #         profile_dir=PROF_DIR,
    #     )

    @app.callback(
        Output("standings-graph", "figure"),
        Output("standings-graph-static", "figure"),
        Input("standings-x-axis", "value"),
        Input("standings-y-axis", "value"),
        Input("user-choices", "data"),
        prevent_initial_call=True,
    )
    def update_standing_figure(
        x_axis: str, y_axis: str, user_choices: list[dict]
    ) -> tuple[go.Figure, go.Figure]:
        standings: pd.DataFrame | None = get_standings(
            pd.DataFrame(user_choices).copy(deep=True), fixtures=fixtures_df
        )

        standings_figure = create_figure(standings, x_axis, y_axis)

        standings_figure_small = copy.deepcopy(standings_figure)
        standings_figure_small.update_xaxes(autorange=True)

        return standings_figure, standings_figure_small

    @app.callback(
        Output("fixtures-filter-table", "data"),
        Input("fixtures-filter-value", "value"),
        State("fixtures-table", "data"),
    )
    def update_fixture_filter_table(
        values: list[str] | None, fixtures_table: list[dict]
    ) -> list[dict]:
        fixtures: pd.DataFrame = fixtures_df

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
                filtered_fixtures = fixtures[
                    (fixtures["Home Team"].isin(team_values))
                    | (fixtures["Away Team"].isin(team_values))
                ]
            else:
                filtered_fixtures = fixtures

            if round_values:
                filtered_fixtures = filtered_fixtures[
                    filtered_fixtures["Round Number"].isin(round_values)
                ]
            else:
                filtered_fixtures = filtered_fixtures

        filtered_fixtures_table: list[dict] = filtered_fixtures.to_dict("records")

        return filtered_fixtures_table

        # Define the layout

    app.layout = create_layout

    return app, load


def server(filepath) -> Flask:
    """Function for running the app on a server with gunicorn."""
    app: Dash
    config: Loader
    app, config = create_app(filepath)
    server: Flask = app.server
    return server


def main() -> None:
    """Function for running the app locally."""
    args = create_parser().parse_args()
    app: Dash
    config: Loader
    app, config = create_app(args.filepath)
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
