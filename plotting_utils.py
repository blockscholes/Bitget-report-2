from __future__ import annotations

import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

__all__ = ["PlotTheme", "DEFAULT_THEME", "add_watermark", "update_timeseries_layout", "tenors", "today_date"]

tenors = [7, 14, 30, 60, 90, 180]
today_date = str(pd.Timestamp.now().normalize() + pd.Timedelta(1, "d"))


@dataclass
class PlotTheme:
    """Reusable plot styling that can be applied across different figures."""

    background_color: str = "#101A2E"
    grid_color: str = "#293e68"
    font_color: str = "white"
    font_size: int = 20
    height: int = 650
    width: int = 1450
    legend_y: float = 1.1
    legend_orientation: str = "h"
    margin: dict = field(
        default_factory=lambda: {"l": 150, "r": 30, "b": 50, "t": 50, "pad": 4}
    )
    watermark_path: Optional[str] = "watermark/Block Scholes Full Logo cleaned.png"
    watermark_size: float = 0.4
    watermark_opacity: float = 0.5
    watermark_position: tuple[float, float] = (0.5, 0.5)
    show_legend: bool = True

    def apply_layout(self, fig: go.Figure) -> None:
        fig.update_layout(
            showlegend=self.show_legend,
            title="",
            height=self.height,
            width=self.width,
            font=dict(size=self.font_size, color=self.font_color),
            xaxis=dict(
                title="",
                automargin=True,
                tickangle=0,
                showgrid=True,
                gridwidth=1,
                gridcolor=self.grid_color,
                zeroline=False,
                ticklen=10,
                tickmode="array",
            ),
            yaxis=dict(gridcolor=self.grid_color),
            yaxis2=dict(gridcolor=self.grid_color),
            legend=dict(
                orientation=self.legend_orientation,
                yanchor="top",
                y=self.legend_y,
                xanchor="center",
                x=0.5,
            ),
            margin=self.margin,
            plot_bgcolor=self.background_color,
            paper_bgcolor=self.background_color,
        )
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=self.grid_color, zeroline=False)

    def add_watermark(
        self,
        fig: go.Figure,
        *,
        image_path: Optional[str] = None,
        opacity: Optional[float] = None,
        size: Optional[float] = None,
        position: Optional[tuple[float, float]] = None,
    ) -> None:
        path = Path(image_path or self.watermark_path or "")
        if not path.exists():
            return

        with path.open("rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        x, y = position or self.watermark_position
        fig.add_layout_image(
            dict(
                source="data:image/png;base64," + encoded_string,
                xref="paper",
                yref="paper",
                x=x,
                y=y,
                sizex=size or self.watermark_size,
                sizey=size or self.watermark_size,
                xanchor="center",
                yanchor="middle",
                opacity=opacity if opacity is not None else self.watermark_opacity,
            )
        )


DEFAULT_THEME = PlotTheme()


def add_watermark(fig: go.Figure, image_path: Optional[str] = None, *, theme: PlotTheme = DEFAULT_THEME, **kwargs) -> None:
    """Convenience wrapper to add a watermark to a figure using the provided theme."""
    theme.add_watermark(fig, image_path=image_path, **kwargs)


def update_timeseries_layout(fig: go.Figure, *, theme: PlotTheme = DEFAULT_THEME) -> None:
    """Apply the shared layout styling to a Plotly figure."""
    theme.apply_layout(fig)
