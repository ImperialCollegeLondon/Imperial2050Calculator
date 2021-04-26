import json
from collections import OrderedDict, namedtuple
from math import atan, pi, sin, sqrt
from pathlib import Path

import anvil.server
import i18n

from . import interface2050
from .model2050 import Model2050

model = Model2050(interface2050)

EARTH_RADIUS_KM = 6371


def arc_length_to_angle(length, radius):
    """Return the change in angle (in degrees) associated with a known arc length
    and radius.
    """
    return length / radius * (180 / pi)


def area_to_side_length(area, radius):
    """Return the side length for a square of known area on a spherical surface."""
    return 2 * radius * atan(sqrt(sin(area / (4 * radius ** 2))))


with open(Path(__file__).absolute().parent.parent / "web_outputs.json") as f:
    TABLE = json.load(f)


@anvil.server.callable
def inputs():
    return model.input_values_default()


@anvil.server.callable
def levers():
    return list(model.input_levers.keys())


@anvil.server.callable
def outputs():

    return list(model.outputs.keys())


@anvil.server.callable
def calculate(inputs):
    solution = model.calculate(inputs)
    solution["emissions_sector"] = solution["emissions_sector"][-4::-1]
    solution["x"] = list(range(2015, 2055, 5))
    return solution


i18n.set("filename_format", "{locale}.{format}")
i18n.set("enable_memoization", True)
i18n.load_path.append(Path(__file__).absolute().parent / "translations")


@anvil.server.callable
def translate(locale, text):
    i18n.set("locale", locale)
    return i18n.t(text)


GraphData = namedtuple("GraphData", ("title", "output", "plot_type"))


@anvil.server.callable
def layout():
    layout = OrderedDict()
    for tab, sub_tab, pos, title, named_ranges, plot_type in zip(
        TABLE["Webtool Page"],
        TABLE["Webtool Tab"],
        TABLE["Position"],
        TABLE["Title"],
        TABLE["Named Range"],
        TABLE["Graph Type"],
    ):
        if sub_tab.lower() == "not required":
            continue
        # may be multiple comma seperated named_ranges in string, we want to
        # remove the "output." prefix from all of them
        named_ranges = ",".join(
            r.removeprefix("output.") for r in named_ranges.split(",")
        ).replace(".", "_")

        sub_tabs = layout.setdefault(tab, OrderedDict())
        positions = sub_tabs.setdefault(sub_tab, OrderedDict())
        positions[pos] = GraphData(
            title,
            named_ranges,
            plot_type,
        )

    return layout


@anvil.server.callable
def map(data):
    import plotly.graph_objects as go

    fig = go.Figure()

    # the below will need to be configurable parameters
    start_draw_lat = 57.0
    start_draw_lon = -3.346
    padding = 0.20  # degrees
    map_center_lat = 55.3781
    map_center_lon = -3.436
    map_zoom = 4

    traces = []
    # draw areas starting with top-left corner at (start_draw_lat,start_draw_lon),
    # each subsequent box is placed to the south of the previous
    for name, area_km2 in data["area"]:
        length_km = area_to_side_length(area_km2, EARTH_RADIUS_KM)
        d_theta_deg = arc_length_to_angle(length_km, EARTH_RADIUS_KM)

        # box coordinates below are clockwise from top-left
        lats = [
            start_draw_lat,
            start_draw_lat,
            start_draw_lat - d_theta_deg,
            start_draw_lat - d_theta_deg,
        ]
        lons = [
            start_draw_lon,
            start_draw_lon + d_theta_deg,
            start_draw_lon + d_theta_deg,
            start_draw_lon,
        ]
        traces.append(
            go.Scattermapbox(fill="toself", lon=lons, lat=lats, name=name, mode="lines")
        )
        if area_km2:
            start_draw_lat -= d_theta_deg + padding

    # now draw lines for distance quantities in a similar fashion
    for name, distance_km in data["distance"]:
        d_theta_deg = arc_length_to_angle(distance_km, EARTH_RADIUS_KM)
        lats = [start_draw_lat, start_draw_lat]
        lons = [start_draw_lon, start_draw_lon + d_theta_deg]
        traces.append(
            go.Scattermapbox(lon=lons, lat=lats, name=name, mode="lines+markers")
        )
        if distance_km:
            start_draw_lat -= padding

    fig = go.Figure(
        traces,
        layout=dict(
            mapbox={
                "style": "stamen-terrain",
                "center": {"lat": map_center_lat, "lon": map_center_lon},
                "zoom": map_zoom,
            },
        ),
    )
    return fig
