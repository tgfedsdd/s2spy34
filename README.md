<img width="300" alt="Logo" src="https://raw.githubusercontent.com/AI4S2S/s2spy/main/docs/assets/images/ai4s2s_logo.png">

# s2spy

[![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](https://github.com/AI4S2S/ai4s2s)
[![github license badge](https://img.shields.io/github/license/AI4S2S/s2spy)](https://github.com/AI4S2S/s2spy)
[![fair-software badge](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu)
[![Documentation Status](https://readthedocs.org/projects/ai4s2s/badge/?version=latest)](https://ai4s2s.readthedocs.io/en/latest/?badge=latest)
[![build](https://github.com/AI4S2S/s2spy/actions/workflows/build.yml/badge.svg)](https://github.com/AI4S2S/s2spy/actions/workflows/build.yml)
[![sonarcloud](https://github.com/AI4S2S/s2spy/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/AI4S2S/s2spy/actions/workflows/sonarcloud.yml)
[![workflow scc badge](https://sonarcloud.io/api/project_badges/measure?project=AI4S2S_ai4s2s&metric=coverage)](https://sonarcloud.io/dashboard?id=AI4S2S_ai4s2s)

A high-level python package integrating expert knowledge and artificial intelligence to boost (sub) seasonal forecasting.

## Why s2spy?
Producing reliable sub-seasonal to seasonal (S2S) forecasts with machine learning techniques remains a challenge. Currently, these data-driven S2S forecasts generally suffer from a lack of trust because of:
- Intransparent data processing and poorly reproducible scientific outcomes
- Technical pitfalls related to machine learning-based predictability (e.g. overfitting)
- Black-box methods without sufficient explanation

To tackle these challenges, we build `s2spy` which is an open-source, high-level python package. It provides an interface between artificial intelligence and expert knowledge, to boost predictability and physical understanding of S2S processes. By implementing optimal data-handling and parallel-computing packages, it can efficiently run across different Big Climate Data platforms. Key components will be explainable AI and causal discovery, which will support the classical scientific interplay between theory, hypothesis-generation and data-driven hypothesis-testing, enabling knowledge-mining from data.

Developing this tool will be a community effort. It helps us achieve trustworthy data-driven forecasts by providing:
- Transparent and reproducible analyses
- Best practices in model verifications
- Understanding the sources of predictability

## Installation
[![workflow pypi badge](https://img.shields.io/pypi/v/s2spy.svg?colorB=blue)](https://pypi.python.org/project/s2spy/)
[![supported python versions](https://img.shields.io/pypi/pyversions/s2spy)](https://pypi.python.org/project/s2spy/)

To install the latest release of s2spy, do:
```console
python3 -m pip install s2spy
```

To install the in-development version from the GitHub repository, do:

```console
python3 -m pip install git+https://github.com/AI4S2S/s2spy.git
```

### Configure the package for development and testing
The testing framework used here is [pytest](https://pytest.org). Before running the test, we get a local copy of the source code and install `s2spy` via the command:

```py
git clone https://github.com/AI4S2S/s2spy.git
cd s2spy
python3 -m pip install -e .
```

Then, run tests:
```py
python3 -m pytest
```

## Getting started
`s2spy` provides end-to-end solutions for machine learning (ML) based S2S forecasting.

![workflow](https://raw.githubusercontent.com/AI4S2S/s2spy/main/docs/assets/images/workflow.png)

### Datetime operations & Data processing
In a typical ML-based S2S project, the first step is always data processing.  A calendar-based datetime module `time` is implemented for time operations. For instance, a user is looking for predictors for winter climate at seasonal timescales (~180 days). First, a `calendar` object is created using `AdventCalendar`:

```py
>>> calendar = s2spy.time.AdventCalendar(anchor="11-30", freq='180d')
>>> calendar = calendar.map_years(2020, 2021)
>>> calendar.show()
i_interval                         -1                         1
anchor_year
2021         [2021-06-03, 2021-11-30)  [2021-11-30, 2022-05-29)
2020         [2020-06-03, 2020-11-30)  [2020-11-30, 2021-05-29)
```

Now, the user can load the data `input_data` (e.g. `pandas` `DataFrame`) and resample it to the desired timescales configured in the calendar:

```py
>>> calendar = calendar.map_to_data(input_data)
>>> bins = s2spy.time.resample(calendar, input_data)
>>> bins
  anchor_year  i_interval                  interval  mean_data  target
0        2020          -1  [2020-06-03, 2020-11-30)      275.5    True
1        2020           1  [2020-11-30, 2021-05-29)       95.5   False
2        2021          -1  [2021-06-03, 2021-11-30)      640.5    True
3        2021           1  [2021-11-30, 2022-05-29)      460.5   False
```

Depending on data preparations, we can choose different types of calendars e.g. [`MonthlyCalendar`](https://ai4s2s.readthedocs.io/en/latest/autoapi/s2spy/time/index.html#s2spy.time.MonthlyCalendar) and [`WeeklyCalendar`](https://ai4s2s.readthedocs.io/en/latest/autoapi/s2spy/time/index.html#s2spy.time.WeeklyCalendar).

### Cross-validation
Using `s2spy`, we can generate train/test splits and perform cross-validation. To do that, a splitter is called from `sklearn.model_selection` e.g. `ShuffleSplit` and used to split the resampled data:

```py
from sklearn.model_selection import ShuffleSplit
splitter = ShuffleSplit(n_splits=3)
s2spy.traintest.split_groups(splitter, bins)
```

All splitter classes from `scikit-learn` are supported, a list is available [here](https://scikit-learn.org/stable/modules/classes.html#splitter-classes). Users should follow `scikit-learn` documentation on how to use a different splitter class.

### Dimensionality reduction
In `s2spy`, we can perform dimensionality reduction on data. For instance, to perform the [Response Guided Dimensionality Reduction (RGDR)](https://www.nature.com/articles/s41612-022-00237-7), we configure the RGDR operator and fit it to a precursor field. Then, this cluster can be used to transform the data into the reduced clusters:
```py
rgdr = RGDR(eps_km=600, alpha=0.05, min_area_km2=3000**2)
rgdr.fit(precursor_field, target_timeseries)
clustered_data = rgdr.transform(precursor_field)
_ = rgdr.plot_clusters(precursor_field, target_timeseries, lag=1)
```
![clusters](https://raw.githubusercontent.com/AI4S2S/s2spy/main/docs/assets/images/rgdr_clusters.png)

(for more information about `precursor_field` and `target_timeseries`, check the complete example in [this notebook](https://github.com/AI4S2S/s2spy/blob/main/notebooks/tutorial_RGDR.ipynb).)

Currently, `s2spy` supports [dimensionality reduction approaches](https://scikit-learn.org/stable/modules/classes.html#module-sklearn.cluster) from `scikit-learn`.

### Train a model
More information will follow soon.

### eXplainable AI (XAI) analysis
More information will follow soon.

## Tutorials
`s2spy` supports operations that are common in a machine learning pipeline of sub-seasonal to seasonal forecasting research. Tutorials covering supported methods and functionalities are listed in [notebooks](https://github.com/AI4S2S/s2spy/tree/main/notebooks). To check these notebooks, users need to install [`Jupyter lab`](https://jupyter.org/). More details about each method can be found in this [API reference documentation](https://ai4s2s.readthedocs.io/en/latest/autoapi/index.html).

## Documentation
[![Documentation Status](https://readthedocs.org/projects/ai4s2s/badge/?version=latest)](https://ai4s2s.readthedocs.io/en/latest/?badge=latest)

For detailed information on using `s2spy` package, visit the [documentation page](https://ai4s2s.readthedocs.io/en/latest/) hosted at Readthedocs.

## Contributing

If you want to contribute to the development of s2spy,
have a look at the [contribution guidelines](docs/CONTRIBUTING.md).

## How to cite us
[![RSD](https://img.shields.io/badge/rsd-s2spy-00a3e3.svg)](https://research-software-directory.org/software/s2spy)
<!-- [![DOI](https://zenodo.org/badge/DOI/<replace-with-created-DOI>.svg)](https://doi.org/<replace-with-created-DOI>) -->

<!--TODO: add links to zenodo and rsd. -->
More information will follow soon.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
