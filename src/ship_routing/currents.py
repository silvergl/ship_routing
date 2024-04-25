import xarray as xr
import pandas as pd
import numpy as np

from pathlib import Path


def load_currents(
    data_file: Path = None,
    lon_name: str = "longitude",
    lat_name: str = "latitude",
    time_name: str = "time",
    uo_name: str = "uo",
    vo_name: str = "vo",
) -> xr.Dataset:
    ds = xr.open_dataset(data_file)
    ds = ds.rename(
        {
            lon_name: "lon",
            lat_name: "lat",
            time_name: "time",
            uo_name: "uo",
            vo_name: "vo",
        }
    )
    return ds


def load_currents_time_average(
    data_file: Path = None,
    lon_name: str = "longitude",
    lat_name: str = "latitude",
    time_name: str = "time",
    uo_name: str = "uo",
    vo_name: str = "vo",
) -> xr.Dataset:
    _ds = load_currents(
        data_file=data_file,
        lon_name=lon_name,
        lat_name=lat_name,
        time_name=time_name,
        uo_name=uo_name,
        vo_name=vo_name,
    )
    ds = _ds.mean("time")
    ds = ds.expand_dims("time").assign_coords(
        time=(
            ("time",),
            [
                _ds.time.mean().data[()],
            ],
        )
    )
    return ds


def select_currents_along_traj(
    ds: xr.Dataset = None, ship_positions: pd.DataFrame = None
):
    ship_pos_ds = ship_positions.to_xarray()
    return ds.sel(
        lon=ship_pos_ds.lon,
        lat=ship_pos_ds.lat,
        time=ship_pos_ds.time,
        method="nearest",
    )


def select_currents_for_leg(
    ds: xr.Dataset = None,
    lon_start=None,
    lon_end=None,
    lat_start=None,
    lat_end=None,
    time_start=None,
    time_end=None,
):
    # add indices to ds
    ds = ds.assign_coords(
        i=(("lon",), np.arange(ds.sizes["lon"])),
        j=(("lat",), np.arange(ds.sizes["lat"])),
        l=(("time",), np.arange(ds.sizes["time"])),
    )
    # select for first and last pos
    i_start = ds.i.sel(lon=lon_start, method="nearest").data[()]
    j_start = ds.j.sel(lat=lat_start, method="nearest").data[()]
    l_start = ds.l.sel(time=time_start, method="nearest").data[()]
    i_end = ds.i.sel(lon=lon_end, method="nearest").data[()]
    j_end = ds.j.sel(lat=lat_end, method="nearest").data[()]
    l_end = ds.l.sel(time=time_end, method="nearest").data[()]

    # determine num of points
    #
    # Note we only account for i and j here because we want spatial coverage.
    # This is OK as long as the time-variability of the currents is a lot longer
    # than the variability of ship positions. Which is almost always the case.
    n = max(abs(i_end - i_start), abs(j_start - j_end)) + 1

    # interpolate i and j
    i = xr.DataArray(
        np.round(np.linspace(i_start, i_end, n)).astype(int), name="i", dims=("along",)
    )
    j = xr.DataArray(
        np.round(np.linspace(j_start, j_end, n)).astype(int), name="j", dims=("along",)
    )
    l = xr.DataArray(
        np.round(np.linspace(l_start, l_end, n)).astype(int), name="l", dims=("along",)
    )

    # select and return
    return ds.isel(lon=i, lat=j, time=l)
