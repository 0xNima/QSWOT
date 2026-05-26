# QSWOT

A QGIS 3 plugin to discover, download, visualize, and analyze
[SWOT](https://swot.jpl.nasa.gov/) (Surface Water and Ocean Topography)
hydrology data - river reaches and lakes - directly from
[NASA PO.DAAC's Hydrocron API](https://podaac.github.io/hydrocron/).

## Features

- **Search by river or lake name** - type "Rhine" or "Lake Michigan" and QSWOT
  resolves the matching SWORD reach IDs (rivers) or PLD lake IDs (lakes),
  then fetches their SWOT timeseries from Hydrocron.
- **Streaming layer creation** - features appear on the map as each reach /
  lake completes, so you see results building up instead of waiting for the
  whole batch to finish.
- **Per-field selection** - pick exactly which SWOT measurements you want
  (WSE, slope, width, area, discharge, etc.) via a tabbed checkbox UI.
- **Auto layer styling** - rivers as red linestrings, lakes as translucent
  blue polygons (with a separate point layer for sparse observations).
- **Statistics dialog** - compute Pearson / Spearman / Kendall correlations
  between any two numeric fields, or plot a time series of one field over
  time, with built-in mouse-wheel zoom and matplotlib navigation tools.
- **Country-wide zoom** - first features auto-fit the canvas to a regional
  overview so you see where the data is.
- **Cancellable** - every fetch runs as a non-blocking QGIS task with a
  Cancel button; closing QGIS mid-fetch shuts down cleanly.

## Requirements

- **QGIS 3.0 or newer.**
- **Python packages**: `numpy`, `matplotlib`, and `scipy`.
  - `numpy` and `matplotlib` ship with every standard QGIS distribution
    (Windows OSGeo4W, official macOS package, most Linux QGIS builds).
  - `scipy` is **optional**: it's needed for **Spearman** and **Kendall**
    correlations. Without it, only **Pearson** is available. If you need
    Spearman/Kendall and don't have scipy, install it into the QGIS Python
    environment:
    - Windows (OSGeo4W shell): `pip install scipy`
    - macOS (official QGIS): `/Applications/QGIS.app/Contents/MacOS/bin/pip3 install scipy`
    - Linux: `pip3 install --user scipy`
    - General guide for Windows:
      <https://landscapearchaeology.org/2018/installing-python-packages-in-qgis-3-for-windows/>
- **Network access** to:
  - `https://soto.podaac.earthdatacloud.nasa.gov` (Hydrocron timeseries)
  - `https://fts.podaac.earthdata.nasa.gov` (river reach ID lookup)
  - `https://lakes.swot-lake.workers.dev` (lake ID lookup)
  - Proxy / SSL settings configured in QGIS (Settings → Options → Network)
    are honored automatically.

## Geographic / data restrictions

- SWOT is a global mission, but only locations sampled by the satellite
  (i.e., not consistently every point) have data. Coverage varies by
  latitude and orbit phase.
- Hydrocron returns data starting from the SWOT operational era (late 2022
  onwards). Date ranges before that will return empty results.
- Some river reaches and lakes (especially very small ones) may have only a
  handful of observations per year due to SWOT's ~21-day repeat cycle.

## Installation

### From the QGIS Plugins repository (recommended once published)

1. In QGIS: **Plugins → Manage and Install Plugins**.
2. Search for **QSWOT** and click **Install**.

### From source (development)

1. Clone or download this repository.
2. Copy or symlink the `swot/` folder into your QGIS plugins directory:
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable the plugin via **Plugins → Manage and Install Plugins**.

## Usage

1. Launch QSWOT from the toolbar icon or **Web → &QSWOT**.
2. In the dialog:
   - Enter a **river name** (e.g. `Rhine`) and/or a **lake name**
     (e.g. `Constance`).
   - Pick a **date range**.
   - Open the **Query Attributes** tabs and check the fields you want
     returned for each feature type.
   - Optionally cap the number of reaches/lakes fetched.
3. Click **OK**. Reaches stream into a red linestring layer; lakes into a
   blue polygon layer (and a point layer when SWOT has only point
   observations for some lakes).
4. Click **River Statistic** or **Lake Statistic** to open the stats
   dialog, where you can plot time series or compute correlations.
5. **Lake stats require a selection first** - lake searches can return
   features from many physically distinct lakes (e.g. "caspian" returns
   Caspian Sea *and* Caspian Lake); select the rows for the lake of
   interest in the attribute table before opening the stats dialog.

## Issues and contributions

- Report bugs: <https://github.com/0xNima/QSWOT/issues>
- Source code: <https://github.com/0xNima/QSWOT>

## License

QSWOT is released under the GNU General Public License v3.0 or later
(GPL-3.0-or-later). See [`LICENSE`](LICENSE) for the full text.

## Acknowledgements

- The [SWOT mission](https://swot.jpl.nasa.gov/) is a joint program of
  NASA and CNES (Centre National d'Études Spatiales).
- Data and APIs courtesy of [NASA JPL PO.DAAC](https://podaac.jpl.nasa.gov/).
