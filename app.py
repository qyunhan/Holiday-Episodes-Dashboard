import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# ── Load & prep data ──────────────────────────────────────────────────────────
episodes = pd.read_csv("data/holiday_episodes.csv")
genres_df = pd.read_csv("data/holiday_genres.csv")

merged = (
    episodes
    .merge(genres_df, on="tconst", how="left")
    .rename(columns={"genres_x": "genre_combi", "genres_y": "main_genre"})
)

# ── App layout ────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="Holiday Episodes Dashboard",
)
server = app.server  # expose for gunicorn

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "14rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow-y": "auto",
}
CONTENT_STYLE = {
    "margin-left": "15rem",
    "margin-right": "1rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H5("🎄 Holiday Episodes", className="display-7 fw-bold text-success"),
        html.Hr(),
        html.P("Barplot Boys | DSA2101", className="text-muted small"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Overview", href="/", active="exact"),
                dbc.NavLink("Genre Vote Share", href="/plot1", active="exact"),
                dbc.NavLink("Runtime vs Rating", href="/plot2", active="exact"),
                dbc.NavLink("Data Table", href="/data", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div(
    [dcc.Location(id="url"), sidebar, content]
)

# ── Pages ─────────────────────────────────────────────────────────────────────

def overview_page():
    total_eps = len(episodes)
    avg_rating = episodes["average_rating"].mean()
    n_genres = genres_df["genres"].nunique()
    year_range = f"{int(episodes['year'].min())} – {int(episodes['year'].max())}"

    cards = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{total_eps:,}", className="card-title text-success"),
            html.P("Total Episodes", className="card-text text-muted"),
        ])], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{avg_rating:.2f} ⭐", className="card-title text-warning"),
            html.P("Avg IMDB Rating", className="card-text text-muted"),
        ])], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(str(n_genres), className="card-title text-info"),
            html.P("Unique Genres", className="card-text text-muted"),
        ])], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(year_range, className="card-title text-primary"),
            html.P("Year Range", className="card-text text-muted"),
        ])], className="shadow-sm"), width=3),
    ], className="mb-4 g-3")

    return html.Div([
        html.H2("Holiday Episodes Analysis", className="mb-1 fw-bold"),
        html.P(
            "Exploring how viewer preferences around genre, runtime and reception "
            "have changed across decades of holiday TV episodes.",
            className="text-muted mb-4",
        ),
        cards,
        dbc.Row([
            dbc.Col([
                html.H5("About This Dashboard", className="fw-bold"),
                html.P([
                    "This dataset comes from the ",
                    html.A("TidyTuesday Holiday Episodes",
                           href="https://github.com/rfordatascience/tidytuesday/tree/main/data/2023/2023-12-19",
                           target="_blank"),
                    " project. It contains IMDB data for TV episodes tagged as holiday-themed "
                    "(Christmas, Hanukkah, Kwanzaa, and general holiday).",
                ]),
                html.Hr(),
                html.H5("Key Questions", className="fw-bold"),
                html.Ul([
                    html.Li("How has genre popularity (by vote share) changed across decades?"),
                    html.Li("What runtime–rating combinations do different genres cluster around?"),
                    html.Li("Are there genre-specific 'sweet spots' in terms of runtime and rating?"),
                ]),
            ], width=8),
            dbc.Col([
                html.H5("Holiday Types", className="fw-bold"),
                dcc.Graph(figure=_holiday_pie(), config={"displayModeBar": False}),
            ], width=4),
        ]),
    ])


def _holiday_pie():
    cols = ["christmas", "hanukkah", "kwanzaa", "holiday"]
    counts = {c: int(episodes[c].sum()) for c in cols}
    labels = ["Christmas", "Hanukkah", "Kwanzaa", "Holiday (general)"]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=list(counts.values()),
        hole=0.45,
        marker_colors=["#c0392b", "#2980b9", "#27ae60", "#f39c12"],
    ))
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=True,
        legend=dict(font=dict(size=11)),
        height=220,
    )
    return fig


def plot1_page():
    return html.Div([
        html.H3("Genre Vote Share Over Time", className="fw-bold"),
        html.P(
            "Each decade's stacked bar shows the proportion of total weighted votes "
            "attributed to each genre. Votes are split proportionally across all genres "
            "tagged to an episode.",
            className="text-muted",
        ),
        dbc.Row([
            dbc.Col([
                html.Label("Highlight genres:", className="fw-bold small"),
                dcc.Dropdown(
                    id="genre-select",
                    options=[{"label": g, "value": g} for g in
                             ["Animation", "Comedy", "Family", "Drama",
                              "Sci-Fi", "Western", "Crime", "Adventure",
                              "Romance", "Action", "Documentary"]],
                    value=["Animation", "Comedy", "Family", "Drama", "Sci-Fi", "Western"],
                    multi=True,
                    clearable=False,
                ),
            ], width=8),
        ], className="mb-3"),
        dcc.Graph(id="bar-chart", style={"height": "520px"}),
        dbc.Alert([
            html.Strong("Insights: "),
            "Comedy and Family have historically dominated holiday episode viewership. "
            "Animation grew substantially from the 1980s onwards. Drama maintained a "
            "steady share while niche genres like Sci-Fi and Western declined."
        ], color="light", className="mt-2 small"),
    ])


def plot2_page():
    return html.Div([
        html.H3("Runtime vs. Rating Density (Top Genres)", className="fw-bold"),
        html.P(
            "2D kernel density estimation across runtime (minutes) and IMDB average rating "
            "for the top genres by average engagement. Bright areas indicate clusters of episodes. "
            "The green dot marks the peak density 'sweet spot'.",
            className="text-muted",
        ),
        dbc.Row([
            dbc.Col([
                html.Label("Number of top genres:", className="fw-bold small"),
                dcc.Slider(id="top-n", min=3, max=8, step=1, value=5,
                           marks={i: str(i) for i in range(3, 9)}),
            ], width=5),
            dbc.Col([
                html.Label("Color scale:", className="fw-bold small"),
                dcc.Dropdown(
                    id="colorscale",
                    options=[{"label": c, "value": c}
                             for c in ["Plasma", "Viridis", "Hot", "Inferno", "Magma"]],
                    value="Plasma", clearable=False,
                ),
            ], width=3),
        ], className="mb-3"),
        dcc.Graph(id="density-chart", style={"height": "680px"}),
        dbc.Alert([
            html.Strong("Insights: "),
            "Each genre has a distinct runtime sweet spot. Comedy episodes cluster around "
            "shorter runtimes with good ratings, while Drama episodes that do well tend to "
            "be longer. The sweet spot annotation highlights the peak density point per genre."
        ], color="light", className="mt-2 small"),
    ])


def data_page():
    df_show = (
        episodes[["primary_title", "year", "parent_primary_title",
                  "runtime_minutes", "average_rating", "num_votes",
                  "genres", "christmas", "hanukkah", "kwanzaa", "holiday"]]
        .dropna(subset=["average_rating"])
        .sort_values("num_votes", ascending=False)
        .head(500)
        .copy()
    )
    df_show["average_rating"] = df_show["average_rating"].round(1)
    df_show["christmas"] = df_show["christmas"].map({True: "✓", False: ""})
    df_show["hanukkah"] = df_show["hanukkah"].map({True: "✓", False: ""})
    df_show["holiday"] = df_show["holiday"].map({True: "✓", False: ""})

    return html.Div([
        html.H3("Data Table", className="fw-bold"),
        html.P("Top 500 episodes by vote count. Use the filter rows to search.", className="text-muted mb-3"),
        dash_table.DataTable(
            data=df_show.to_dict("records"),
            columns=[{"name": c.replace("_", " ").title(), "id": c, "deletable": False}
                     for c in df_show.columns],
            page_size=20,
            filter_action="native",
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "#2c3e50", "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
            ],
            style_cell={"fontSize": 12, "padding": "6px", "maxWidth": "180px",
                        "overflow": "hidden", "textOverflow": "ellipsis"},
        ),
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    if pathname == "/plot1":
        return plot1_page()
    elif pathname == "/plot2":
        return plot2_page()
    elif pathname == "/data":
        return data_page()
    else:
        return overview_page()


@app.callback(
    Output("bar-chart", "figure"),
    Input("genre-select", "value")
)
def update_bar(selected_genres):
    try:
        # -----------------------------
        # 0) Basic checks
        # -----------------------------
        if selected_genres is None or len(selected_genres) == 0:
            fig = go.Figure()
            fig.update_layout(title="No genres selected.")
            return fig

        # -----------------------------
        # 1) Start from episodes only
        # -----------------------------
        df = episodes.copy()

        # Debug: confirm expected columns exist
        required_cols = ["tconst", "genres", "num_votes", "year"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            fig = go.Figure()
            fig.update_layout(
                title=f"Missing columns in episodes: {missing_cols}"
            )
            return fig

        # -----------------------------
        # 2) Clean data
        # -----------------------------
        df = df.dropna(subset=["genres", "num_votes", "year"]).copy()

        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["num_votes"] = pd.to_numeric(df["num_votes"], errors="coerce")
        df = df.dropna(subset=["year", "num_votes"])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Data is empty after dropping NA and coercing year/num_votes.")
            return fig

        # -----------------------------
        # 3) Split genres into long format
        # -----------------------------
        # Handles cases like "Comedy,Family"
        df["main_genre"] = df["genres"].astype(str).str.split(",")

        df = df.explode("main_genre")
        df["main_genre"] = df["main_genre"].astype(str).str.strip()

        df = df[df["main_genre"].notna() & (df["main_genre"] != "")]

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="No rows left after exploding genres.")
            return fig

        # -----------------------------
        # 4) Create decade
        # -----------------------------
        df["decade_start"] = (df["year"] // 10 * 10).astype(int)
        df["decade"] = df["decade_start"].astype(str) + "-" + (df["decade_start"] + 9).astype(str)

        # -----------------------------
        # 5) Weight votes by number of genres per episode
        # -----------------------------
        df["n_genres"] = df.groupby("tconst")["main_genre"].transform("count")
        df = df[df["n_genres"] > 0]

        df["weighted_votes"] = df["num_votes"] / df["n_genres"]

        if df["weighted_votes"].isna().all():
            fig = go.Figure()
            fig.update_layout(title="weighted_votes is entirely NA.")
            return fig

        # -----------------------------
        # 6) Aggregate to decade x genre
        # -----------------------------
        votes_decade = (
            df.groupby(["decade", "main_genre"], as_index=False)["weighted_votes"]
            .sum()
        )

        if votes_decade.empty:
            fig = go.Figure()
            fig.update_layout(title="votes_decade is empty after grouping.")
            return fig

        votes_decade["decade_total"] = votes_decade.groupby("decade")["weighted_votes"].transform("sum")
        votes_decade = votes_decade[votes_decade["decade_total"] > 0]

        votes_decade["proportion"] = votes_decade["weighted_votes"] / votes_decade["decade_total"]

        if votes_decade.empty:
            fig = go.Figure()
            fig.update_layout(title="No rows left after computing proportions.")
            return fig

        # -----------------------------
        # 7) Collapse non-selected genres into Other
        # -----------------------------
        votes_decade["genre_label"] = np.where(
            votes_decade["main_genre"].isin(selected_genres),
            votes_decade["main_genre"],
            "Other"
        )

        agg = (
            votes_decade.groupby(["decade", "genre_label"], as_index=False)["proportion"]
            .sum()
        )

        if agg.empty:
            fig = go.Figure()
            fig.update_layout(title="agg is empty after collapsing into Other.")
            return fig

        # -----------------------------
        # 8) Order decades
        # -----------------------------
        decade_order = sorted(
            agg["decade"].unique(),
            key=lambda x: int(x.split("-")[0])
        )

        genre_order = [g for g in selected_genres if g in agg["genre_label"].unique()]
        if "Other" in agg["genre_label"].unique():
            genre_order += ["Other"]

        if len(genre_order) == 0:
            fig = go.Figure()
            fig.update_layout(
                title="No matching selected genres found in data.",
                annotations=[
                    dict(
                        text=f"Available genres sample: {sorted(df['main_genre'].dropna().unique())[:15]}",
                        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
                    )
                ]
            )
            return fig

        # -----------------------------
        # 9) Colors
        # -----------------------------
        color_map = {
            "Family": "#2a9d8f",
            "Drama": "#e76f51",
            "Comedy": "#457b9d",
            "Western": "#b08968",
            "Sci-Fi": "#6d597a",
            "Animation": "#f4a261",
            "Crime": "#8d99ae",
            "Adventure": "#90be6d",
            "Romance": "#f28482",
            "Action": "#577590",
            "Documentary": "#43aa8b",
            "Other": "#cfcfcf"
        }

        # -----------------------------
        # 10) Build figure
        # -----------------------------
        fig = go.Figure()

        for genre in genre_order:
            sub = (
                agg[agg["genre_label"] == genre]
                .set_index("decade")
                .reindex(decade_order, fill_value=0)
            )

            fig.add_trace(
                go.Bar(
                    x=decade_order,
                    y=sub["proportion"].values * 100,
                    name=genre,
                    marker_color=color_map.get(genre, "#999999"),
                    hovertemplate="<b>%{fullData.name}</b><br>Decade: %{x}<br>Share: %{y:.1f}%<extra></extra>"
                )
            )

        fig.update_layout(
            barmode="stack",
            title="Shifts in Holiday Episodes Genre Preferences by Decade",
            xaxis_title="Decade",
            yaxis_title="Proportion of total votes (%)",
            yaxis=dict(range=[0, 100], ticksuffix="%"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend_title="Genre",
            margin=dict(t=70, b=80, l=70, r=30),
        )

        fig.update_xaxes(showgrid=True, gridcolor="#e5e5e5")
        fig.update_yaxes(showgrid=True, gridcolor="#e5e5e5")

        return fig

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(
            title=f"Callback error: {type(e).__name__}: {str(e)}"
        )
        return fig


@app.callback(Output("density-chart", "figure"),
              [Input("top-n", "value"), Input("colorscale", "value")])
def update_density(top_n, colorscale):
    if not top_n:
        return go.Figure()
    df = merged.dropna(subset=["main_genre", "num_votes", "runtime_minutes", "average_rating"]).copy()

    # top genres by avg votes
    top_genres = (
        df.groupby("main_genre")["num_votes"].mean()
        .nlargest(top_n)
        .index.tolist()
    )

    dfp = df[df["main_genre"].isin(top_genres)].copy()
    dfp = dfp[dfp["runtime_minutes"].between(1, 250) & dfp["average_rating"].between(0, 10)]

    n_cols = min(3, top_n)
    n_rows = int(np.ceil(top_n / n_cols))

    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=top_genres,
        horizontal_spacing=0.08,
        vertical_spacing=0.15,
    )

    grid_x = np.linspace(0, 250, 80)
    grid_y = np.linspace(0, 10, 60)
    xx, yy = np.meshgrid(grid_x, grid_y)
    positions = np.vstack([xx.ravel(), yy.ravel()])

    showscale_done = False
    for idx, genre in enumerate(top_genres):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        sub = dfp[dfp["main_genre"] == genre][["runtime_minutes", "average_rating"]].dropna()

        if len(sub) < 10:
            continue

        try:
            kde = gaussian_kde(sub.values.T, bw_method=0.3)
            z = kde(positions).reshape(xx.shape)
            z_norm = z / z.max() if z.max() > 0 else z
        except Exception:
            continue

        peak_idx = np.unravel_index(z_norm.argmax(), z_norm.shape)
        sweet_x = float(grid_x[peak_idx[1]])
        sweet_y = float(grid_y[peak_idx[0]])

        fig.add_trace(
            go.Heatmap(
                x=grid_x, y=grid_y, z=z_norm,
                colorscale=colorscale,
                zmin=0, zmax=1,
                showscale=not showscale_done,
                colorbar=dict(title="Relative<br>Density", x=1.02) if not showscale_done else {},
                hovertemplate="Runtime: %{x:.0f} min<br>Rating: %{y:.1f}<br>Density: %{z:.2f}<extra></extra>",
            ),
            row=row, col=col,
        )
        showscale_done = True

        fig.add_trace(
            go.Scatter(
                x=[sweet_x], y=[sweet_y],
                mode="markers+text",
                marker=dict(color="lime", size=10, symbol="star",
                            line=dict(color="darkgreen", width=1.5)),
                text=[f"{int(sweet_x)}min / {sweet_y:.1f}★"],
                textposition="top right",
                textfont=dict(color="lime", size=10, family="Arial Black"),
                showlegend=False,
                hovertemplate=f"<b>Sweet Spot</b><br>{int(sweet_x)} min, {sweet_y:.1f} ⭐<extra></extra>",
            ),
            row=row, col=col,
        )

    fig.update_xaxes(title_text="Runtime (min)", range=[0, 250])
    fig.update_yaxes(title_text="IMDB Rating", range=[0, 10])
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="white",
        margin=dict(t=50, b=30, l=50, r=80),
        font=dict(size=11),
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)
