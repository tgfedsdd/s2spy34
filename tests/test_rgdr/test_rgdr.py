"""Tests for the s2s.rgdr module."""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from s2spy import RGDR
from s2spy.rgdr import rgdr
from s2spy.rgdr import utils
from s2spy.time import AdventCalendar
from s2spy.time import resample


TEST_FILE_PATH = "./tests/test_rgdr/test_data"

"""Setting this matplotlib setting is required for running tests on windows. If this
option is not set, matplotlib tries to use an interactive backend, which will result in
a "_tkinter.TclError"."""
matplotlib.use("Agg")

# pylint: disable=protected-access


@pytest.fixture(autouse=True, scope="class")
def dummy_calendar():
    return AdventCalendar(anchor="8-2", freq="30d")


@pytest.fixture(autouse=True, scope="module")
def raw_target():
    return xr.open_dataset(f"{TEST_FILE_PATH}/tf5_nc5_dendo_80d77.nc").sel(cluster=3)


@pytest.fixture(autouse=True, scope="module")
def raw_field():
    return xr.open_dataset(
        f"{TEST_FILE_PATH}/sst_daily_1979-2018_5deg_Pacific_175_240E_25_50N.nc"
    )


@pytest.fixture(autouse=True, scope="class")
def example_field(raw_field, dummy_calendar):
    cal = dummy_calendar.map_to_data(raw_field)
    return resample(cal, raw_field).sst.sel(i_interval=-1)


@pytest.fixture(autouse=True, scope="class")
def example_field_multiple_lags(raw_field, dummy_calendar):
    cal = dummy_calendar.map_to_data(raw_field)
    return resample(cal, raw_field).sst.sel(i_interval=slice(-3, -1))


@pytest.fixture(autouse=True, scope="class")
def example_target(raw_target, raw_field, dummy_calendar):
    cal = dummy_calendar.map_to_data(raw_field)
    return resample(cal, raw_target).ts.sel(i_interval=1)


@pytest.fixture(scope="class")
def example_corr(example_target, example_field):
    return rgdr.correlation(example_field, example_target, corr_dim="anchor_year")


@pytest.fixture(autouse=True, scope="class")
def expected_labels():
    return np.array(
        [
            [0.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, -2.0, -2.0, -2.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.0, -2.0, -2.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.0, -2.0, -2.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.0, 0.0, 0.0],
            [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0],
        ]
    )


class TestUtils:
    """Validates the various utility functions used in RGDR"""

    testdata = [ # lat, dlat, dlon, area
        (-1, 2, 2, 49500),
        (45, 5, 5, 218500),
        (45, 5, 2.5, 109250)
    ]

    @pytest.mark.parametrize("lat,dlat,dlon,expected", testdata)
    def test_spherical_area(self, lat, dlat, dlon, expected):
        np.testing.assert_allclose(
            rgdr.spherical_area(lat, dlat, dlon), expected, rtol=0.05
            )


class TestCorrelation:
    """Validates that the correlation ufunc works, as well as the input checks."""

    @pytest.fixture(autouse=True)
    def dummy_dataarray(self):
        time = pd.date_range("20161001", "20211001", freq="60d")

        return xr.DataArray(
            np.tile(np.arange(len(time)), (2, 2, 1)),
            dims=["lat", "lon", "time"],
            coords={
                "time": time,
                "lat": np.arange(0, 2),
                "lon": np.arange(0, 2),
            },
        )

    @pytest.fixture(autouse=True)
    def dummy_timeseries(self, dummy_dataarray):
        return dummy_dataarray.isel(lat=0, lon=0).drop_vars(["lat", "lon"])

    def test_pearsonr(self):
        result = rgdr._pearsonr_nan([0, 0, 1], [0, 1, 1])
        expected = (0.5, 0.66666667)
        np.testing.assert_array_almost_equal(result, expected)

    def test_pearsonr_nan(self):
        result = rgdr._pearsonr_nan([np.nan, 0, 1], [0, 1, 1])
        expected = (np.nan, np.nan)
        np.testing.assert_array_almost_equal(result, expected)

    def test_correlation(self, dummy_dataarray, dummy_timeseries):
        c_val, p_val = rgdr.correlation(dummy_dataarray, dummy_timeseries)

        np.testing.assert_equal(c_val.values, 1)
        np.testing.assert_equal(p_val.values, 0)

    def test_correlation_dim_name(self, dummy_dataarray, dummy_timeseries):
        da = dummy_dataarray.rename({"time": "i_interval"})
        ts = dummy_timeseries.rename({"time": "i_interval"})
        c_val, p_val = rgdr.correlation(da, ts, corr_dim="i_interval")

        np.testing.assert_equal(c_val.values, 1)
        np.testing.assert_equal(p_val.values, 0)

    def test_correlation_wrong_target_dim_name(self, dummy_dataarray, dummy_timeseries):
        ts = dummy_timeseries.rename({"time": "dummy"})
        with pytest.raises(AssertionError):
            rgdr.correlation(dummy_dataarray, ts)

    def test_correlation_wrong_field_dim_name(self, dummy_dataarray, dummy_timeseries):
        da = dummy_dataarray.rename({"time": "dummy"})
        with pytest.raises(AssertionError):
            rgdr.correlation(da, dummy_timeseries)

    def test_correlation_wrong_target_dims(self, dummy_dataarray):
        ts = dummy_dataarray.rename({"lat": "latitude"})
        with pytest.raises(AssertionError):
            rgdr.correlation(dummy_dataarray, ts)

    def test_partial_correlation(self):
        with pytest.raises(NotImplementedError):
            rgdr.partial_correlation("field", "target", "z")

    def test_regression(self):
        with pytest.raises(NotImplementedError):
            rgdr.regression("field", "target")


class TestDBSCAN:
    """Separately validates that the DBSCAN-based clustering works as expected."""

    @pytest.fixture(autouse=True)
    def dummy_dbscan_params(self):
        return {"alpha": 0.05, "eps": 600, "min_area": None}

    def test_dbscan(
        self, example_corr, example_field, dummy_dbscan_params, expected_labels
    ):
        corr, p_val = example_corr

        clusters = rgdr.masked_spherical_dbscan(
            example_field, corr, p_val, dummy_dbscan_params
        )
        clusters = utils.cluster_labels_to_ints(clusters)

        np.testing.assert_array_equal(clusters["cluster_labels"], expected_labels)

    def test_dbscan_min_area(
        self, example_corr, example_field, dummy_dbscan_params, expected_labels
    ):
        corr, p_val = example_corr
        dbscan_params = dummy_dbscan_params
        dbscan_params["min_area"] = 1000**2
        clusters = rgdr.masked_spherical_dbscan(
            example_field, corr, p_val, dbscan_params
        )
        clusters = utils.cluster_labels_to_ints(clusters)

        expected_labels[expected_labels == -1] = 0  # Small -1 cluster is missing

        np.testing.assert_array_equal(clusters["cluster_labels"], expected_labels)


class TestRGDR:
    """Test RGDR and its methods."""

    @pytest.fixture(autouse=True)
    def dummy_rgdr(self):
        return RGDR(eps_km=600, alpha=0.05, min_area_km2=1000**2)

    def test_init(self):
        rgdr = RGDR(eps_km=600, alpha=0.05, min_area_km2=1000**2)
        assert isinstance(rgdr, RGDR)

    def test_transform_before_fit(self, dummy_rgdr, example_field):
        "Should fail as RGDR first has to be fit to (training) data."
        with pytest.raises(ValueError):
            dummy_rgdr.transform(example_field)

    def test_fit(self, dummy_rgdr, example_field, example_target):
        dummy_rgdr.fit(example_field, example_target)
        assert dummy_rgdr._area is not None

    def test_transform(self, dummy_rgdr, example_field, example_target):
        dummy_rgdr.fit(example_field, example_target)
        clustered_data = dummy_rgdr.transform(example_field)
        clustered_data = utils.cluster_labels_to_ints(clustered_data)
        expected_labels = np.array([-2,  1])
        np.testing.assert_array_equal(clustered_data["cluster_labels"], expected_labels)

    def test_fit_transform_fits(self, example_field, example_target):
        # Ensures that after fit_transform, the rgdr object is fit.
        rgdr = RGDR(eps_km=600, alpha=0.05)
        _ = rgdr.fit_transform(example_field, example_target)
        assert rgdr._area is not None

    def test_fit_transform(self, example_field, example_target):
        rgdr = RGDR(eps_km=600, alpha=0.05, min_area_km2=1000**2)
        clustered_data = rgdr.fit_transform(example_field, example_target)
        expected_labels = np.array(
            ["i_interval:-1_cluster:-2", "i_interval:-1_cluster:1"]
        )
        np.testing.assert_array_equal(clustered_data["cluster_labels"], expected_labels)

    def test_fit_transform_multiple_lags(
        self, example_field_multiple_lags, example_target
    ):
        rgdr = RGDR(eps_km=600, alpha=0.05)
        clustered_data = rgdr.fit_transform(example_field_multiple_lags, example_target)
        expected_labels = np.array(
            [
                "i_interval:-1_cluster:-1", "i_interval:-1_cluster:-2",
                "i_interval:-1_cluster:1", "i_interval:-2_cluster:-1",
                "i_interval:-2_cluster:1", "i_interval:-3_cluster:-1",
                "i_interval:-3_cluster:1"
            ]
        )
        np.testing.assert_array_equal(clustered_data["cluster_labels"], expected_labels)

    def test_corr_preview(self, dummy_rgdr, example_field, example_target):
        dummy_rgdr.preview_correlation(example_field, example_target)

    def test_corr_preview_multiple_lags(
        self, dummy_rgdr, example_field_multiple_lags, example_target
        ):
        dummy_rgdr.preview_correlation(example_field_multiple_lags, example_target, i_interval=-1)

    def test_corr_preview_multiple_lags_fail(
        self, dummy_rgdr, example_field_multiple_lags, example_target
    ):
        with pytest.raises(ValueError):
            dummy_rgdr.preview_correlation(example_field_multiple_lags, example_target)

    def test_corr_plot_ax(self, dummy_rgdr, example_field, example_target):
        _, (ax1, ax2) = plt.subplots(ncols=2)
        dummy_rgdr.preview_correlation(example_field, example_target, ax1=ax1, ax2=ax2)

    def test_cluster_plot(self, dummy_rgdr, example_field, example_target):
        dummy_rgdr.preview_clusters(example_field, example_target)

    def test_cluster_preview_multiple_lags(
        self, dummy_rgdr, example_field_multiple_lags, example_target
        ):
        dummy_rgdr.preview_clusters(example_field_multiple_lags, example_target, i_interval=-1)

    def test_cluster_preview_multiple_lags_fail(
        self, dummy_rgdr, example_field_multiple_lags, example_target
    ):
        with pytest.raises(ValueError):
            dummy_rgdr.preview_clusters(example_field_multiple_lags, example_target)

    def test_cluster_plot_ax(self, dummy_rgdr, example_field, example_target):
        _, ax = plt.subplots()
        dummy_rgdr.preview_clusters(example_field, example_target, ax=ax)
