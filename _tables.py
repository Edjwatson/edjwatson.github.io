import htmltools as ht
import pandas as pd
from mizani.palettes import gradient_n_pal
from reactable import Reactable, Theme, Column, CellInfo, to_widget

DEF_THEME = Theme(
    header_style="hsl(233, 9%, 19%) !important",
    border_color="hsl(233, 9%, 22%) !important",
    highlight_color="hsl(233, 9%, 87%)",
    select_style={"background-color": "hsl(233, 9%, 25%)"},
)

DEF_COL = Column(align = 'left')

CARD_CLASS = "table-card"  # applies the PPFormula font, see styles.scss

TEAM_ABBREVIATIONS = {
    'Adelaide': 'ADE', 'Brisbane Lions': 'BRI', 'Carlton': 'CAR', 'Collingwood': 'COL',
    'Essendon': 'ESS', 'Fremantle': 'FRE', 'Geelong': 'GEE', 'Gold Coast': 'GC',
    'Greater Western Sydney': 'GWS', 'Hawthorn': 'HAW', 'Melbourne': 'MEL',
    'North Melbourne': 'NM', 'Port Adelaide': 'PORT', 'Richmond': 'RIC',
    'St Kilda': 'STK', 'Sydney': 'SYD', 'West Coast': 'WCE', 'Western Bulldogs': 'WB',
}

def team_cell(df = None, home_col = "Home", away_col = "Away", margin_col = "Margin"):
    """Cell renderer for any column of team names: club icon + abbreviated name.

    Pass `df` (with home/away/margin columns) to also highlight the team in a
    bubble when it won that row's match; omit it for a plain team cell.
    """
    def _cell(ci: CellInfo):
        team = ci.value
        abbreviated_team = TEAM_ABBREVIATIONS.get(team, team)

        image = ht.img(
            src=f"assets/clubicons/{team}-40.png",
            style="height: 24px; vertical-align: middle;",
            alt=abbreviated_team,
        )
        text_span = ht.span(abbreviated_team, style="position: relative; top: 2px;")

        is_winner = False
        if df is not None:
            row = df.iloc[ci.row_index]
            is_winner = (
                (row[home_col] == team and row[margin_col] > 0) or
                (row[away_col] == team and row[margin_col] < 0)
            )

        bubble_style = (
            "display: inline-block; margin-left: 6px; padding: 2px 6px; "
            "border-radius: 6px; line-height: 1.2; vertical-align: middle; "
            "background-color: #e8f3c3;"
        ) if is_winner else (
            "display: inline-block; margin-left: 6px; line-height: 1.2;"
        )
        name_div = ht.div(text_span, style=bubble_style)

        return ht.TagList(
            ht.div([image, name_div], style="display: flex; align-items: center; gap: 4px;")
        )
    return _cell

def blank_if_zero(digits = 2, suffix = ""):
    """Cell renderer that blanks out zero/NaN values, otherwise formats to
    `digits` decimals with an optional `suffix` (e.g. "%")."""
    def _cell(ci: CellInfo):
        if pd.isna(ci.value) or ci.value == 0:
            return ""
        return f"{ci.value:.{digits}f}{suffix}"
    return _cell

def gradient_fill(df, palette = ('#ffffff', '#66a558'), extra = None):
    """Cell style function: background colour scaled by the cell's position
    within its column's min/max range, optionally merged with static `extra`
    CSS (e.g. a border to mark a column-group edge)."""
    pal = gradient_n_pal(list(palette))
    def _style(ci: CellInfo):
        base = dict(extra) if extra else {}
        if not isinstance(ci.value, (int, float)) or pd.isna(ci.value):
            return base
        col_vals = df[ci.column_name]
        lo, hi = col_vals.min(), col_vals.max()
        if hi == lo:
            return base
        normalized = (ci.value - lo) / (hi - lo)
        return {**base, "background": pal(normalized)}
    return _style

def table_card(df, title = None, subtitle = None, columns = None, style = None, class_ = None, as_widget = True, extra = None, **kwargs):
    """Build a styled card wrapping a Reactable table.

    `extra` is inserted between the title/subtitle header and the table itself
    (e.g. a row of view-switch buttons).

    Set `as_widget=False` to get back the raw htmltools tag tree instead of a
    finalized widget, so it can be composed inside a larger layout (nested in
    other `ht.div(...)` content) before calling `to_widget()` once at the end.
    """
    tbl = Reactable(
        df,
        theme = DEF_THEME,
        default_col_def = DEF_COL,
        columns = columns,
        searchable = False,
        wrap = False,
        highlight = True,
        **kwargs
    )

    if class_ is None:
        card_class = CARD_CLASS
    elif isinstance(class_, str):
        card_class = f"{CARD_CLASS} {class_}"
    else:
        card_class = [CARD_CLASS, *class_]

    subtitle_el = ht.p(
        subtitle,
        style = ht.css(color = "#888888", margin_top = "-6px", margin_bottom = "0", **(style or {})),
    ) if subtitle else None

    header_el = ht.div(
        ht.h2(title, style = ht.css(**style) if style else None),
        subtitle_el,
        style = "padding: 10px 16px 2px 16px;",
    ) if (title or subtitle) else None

    card = ht.div(
        header_el,
        extra,
        tbl,
        class_ = card_class,
    )

    return to_widget(card) if as_widget else card