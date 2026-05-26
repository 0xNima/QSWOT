from qgis.PyQt.QtCore import QMetaType


RIVER_FIELDS = [
    ("Time & Orbit", [
        ("time", "Time (UTC)", True, None),
        ("time_tai", "Time (TAI)", True, None),
        ("time_str", "Time (String)", True, None),
        ("cycle_id", "Cycle ID", False, None),
        ("pass_id", "Pass ID", False, None),
        ("range_start_time", "Start Time", False, None),
        ("range_end_time", "End Time", False, None),
        ("ingest_time", "Ingest Time", False, None),
    ]),
    ("Hydrology & Measurements", [
        ("wse", "WSE", True, "Water Surface Elevation (WSE)"),
        ("wse_u", "WSE Uncert.", True, "Water Surface Elevation (WSE)"),
        ("wse_r_u", "WSE Rand. Uncert.", False, "Water Surface Elevation (WSE)"),
        ("wse_c", "WSE Constr.", False, "Water Surface Elevation (WSE)"),
        ("wse_c_u", "WSE Constr. Uncert.", False, "Water Surface Elevation (WSE)"),
        ("slope", "Slope", True, "River Slope"),
        ("slope_u", "Slope Uncert.", True, "River Slope"),
        ("slope_r_u", "Slope Rand. Uncert.", False, "River Slope"),
        ("slope2", "Slope (Alt)", False, "River Slope"),
        ("slope2_u", "Slope (Alt) Uncert.", False, "River Slope"),
        ("slope2_r_u", "Slope (Alt) Rand. Uncert.", False, "River Slope"),
        ("width", "Width", True, "River Width"),
        ("width_u", "Width Uncert.", True, "River Width"),
        ("width_c", "Width Constr.", False, "River Width"),
        ("width_c_u", "Width Constr. Uncert.", False, "River Width"),
        ("area_total", "Total Area", True, "River Area"),
        ("area_tot_u", "Total Area Uncert.", True, "River Area"),
        ("area_detct", "Detected Area", False, "River Area"),
        ("area_det_u", "Detected Area Uncert.", False, "River Area"),
        ("area_wse", "Area used for WSE", False, "River Area"),
        ("d_x_area", "Area Change", False, "River Area"),
        ("d_x_area_u", "Area Change Uncert.", False, "River Area"),
    ]),
    ("Geometry & Topology", [
        ("geometry", "Geometry Shape", False, None),
        ("p_lat", "Latitude (Prior)", False, None),
        ("p_lon", "Longitude (Prior)", False, None),
        ("node_dist", "Node Distance", False, None),
        ("loc_offset", "Location Offset", False, None),
        ("xtrk_dist", "Cross-Track Dist.", False, None),
        ("geoid_hght", "Geoid Height", False, None),
        ("geoid_slop", "Geoid Slope", False, None),
        ("n_reach_up", "Upstream Reach Count", False, None),
        ("n_reach_dn", "Downstream Reach Count", False, None),
        ("rch_id_up", "Upstream IDs", False, None),
        ("rch_id_dn", "Downstream IDs", False, None),
        ("p_n_nodes", "Prior Node Count", False, None),
        ("p_dist_out", "Dist. to Outlet", False, None),
        ("p_length", "Prior Length", False, None),
        ("p_n_ch_max", "Max River Channels", False, None),
        ("p_n_ch_mod", "Mode River Channels", False, None),
    ]),
    ("River Discharge", [
        ("dschg_c", "Consens. Flow", False, "Consensus Model"),
        ("dschg_c_u", "Consens. Flow Uncert.", False, "Consensus Model"),
        ("dschg_csf", "Consens. Flow Frac.", False, "Consensus Model"),
        ("dschg_c_q", "Consens. Flow Qual.", False, "Consensus Model"),
        ("dschg_gc", "Gage Consens. Flow", False, "Consensus Model"),
        ("dschg_gc_u", "Gage Consens. Uncert.", False, "Consensus Model"),
        ("dschg_gcsf", "Gage Consens. Frac.", False, "Consensus Model"),
        ("dschg_gc_q", "Gage Consens. Qual.", False, "Consensus Model"),
        ("dschg_m", "MetroMan Flow", False, "MetroMan Model"),
        ("dschg_m_u", "MetroMan Uncert.", False, "MetroMan Model"),
        ("dschg_msf", "MetroMan Frac.", False, "MetroMan Model"),
        ("dschg_m_q", "MetroMan Qual.", False, "MetroMan Model"),
        ("dschg_gm", "Gage MetroMan Flow", False, "MetroMan Model"),
        ("dschg_gm_u", "Gage MetroMan Uncert.", False, "MetroMan Model"),
        ("dschg_gmsf", "Gage MetroMan Frac.", False, "MetroMan Model"),
        ("dschg_gm_q", "Gage MetroMan Qual.", False, "MetroMan Model"),
        ("dschg_b", "BAM Flow", False, "BAM Model"),
        ("dschg_b_u", "BAM Uncert.", False, "BAM Model"),
        ("dschg_bsf", "BAM Frac.", False, "BAM Model"),
        ("dschg_b_q", "BAM Qual.", False, "BAM Model"),
        ("dschg_gb", "Gage BAM Flow", False, "BAM Model"),
        ("dschg_gb_u", "Gage BAM Uncert.", False, "BAM Model"),
        ("dschg_gbsf", "Gage BAM Frac.", False, "BAM Model"),
        ("dschg_gb_q", "Gage BAM Qual.", False, "BAM Model"),
        ("dschg_h", "HiVDI Flow", False, "HiVDI Model"),
        ("dschg_h_u", "HiVDI Uncert.", False, "HiVDI Model"),
        ("dschg_hsf", "HiVDI Frac.", False, "HiVDI Model"),
        ("dschg_h_q", "HiVDI Qual.", False, "HiVDI Model"),
        ("dschg_gh", "Gage HiVDI Flow", False, "HiVDI Model"),
        ("dschg_gh_u", "Gage HiVDI Uncert.", False, "HiVDI Model"),
        ("dschg_ghsf", "Gage HiVDI Frac.", False, "HiVDI Model"),
        ("dschg_gh_q", "Gage HiVDI Qual.", False, "HiVDI Model"),
        ("dschg_o", "MOMMA Flow", False, "MOMMA Model"),
        ("dschg_o_u", "MOMMA Uncert.", False, "MOMMA Model"),
        ("dschg_osf", "MOMMA Frac.", False, "MOMMA Model"),
        ("dschg_o_q", "MOMMA Qual.", False, "MOMMA Model"),
        ("dschg_go", "Gage MOMMA Flow", False, "MOMMA Model"),
        ("dschg_go_u", "Gage MOMMA Uncert.", False, "MOMMA Model"),
        ("dschg_gosf", "Gage MOMMA Frac.", False, "MOMMA Model"),
        ("dschg_go_q", "Gage MOMMA Qual.", False, "MOMMA Model"),
        ("dschg_s", "SADS Flow", False, "SADS Model"),
        ("dschg_s_u", "SADS Uncert.", False, "SADS Model"),
        ("dschg_ssf", "SADS Frac.", False, "SADS Model"),
        ("dschg_s_q", "SADS Qual.", False, "SADS Model"),
        ("dschg_gs", "Gage SADS Flow", False, "SADS Model"),
        ("dschg_gs_u", "Gage SADS Uncert.", False, "SADS Model"),
        ("dschg_gssf", "Gage SADS Frac.", False, "SADS Model"),
        ("dschg_gs_q", "Gage SADS Qual.", False, "SADS Model"),
        ("dschg_i", "SIC4DVar Flow", False, "SIC4DVar Model"),
        ("dschg_i_u", "SIC4DVar Uncert.", False, "SIC4DVar Model"),
        ("dschg_isf", "SIC4DVar Frac.", False, "SIC4DVar Model"),
        ("dschg_i_q", "SIC4DVar Qual.", False, "SIC4DVar Model"),
        ("dschg_gi", "Gage SIC4DVar Flow", False, "SIC4DVar Model"),
        ("dschg_gi_u", "Gage SIC4DVar Uncert.", False, "SIC4DVar Model"),
        ("dschg_gisf", "Gage SIC4DVar Frac.", False, "SIC4DVar Model"),
        ("dschg_gi_q", "Gage SIC4DVar Qual.", False, "SIC4DVar Model"),
        ("dschg_q_b", "Flow Qual. Bitflag", False, "Flow Quality & Prior"),
        ("dschg_gq_b", "Gage Flow Qual. Bitflag", False, "Flow Quality & Prior"),
        ("p_maf", "Mean Annual Flow", False, "Flow Quality & Prior"),
    ]),
    ("Radar Metrics & Corrections", [
        ("layovr_val", "Radar Layover Value", False, None),
        ("dark_frac", "Dark Water Frac.", False, None),
        ("ice_clim_f", "Clim. Ice Flag", False, None),
        ("ice_dyn_f", "Dynamic Ice Flag", False, None),
        ("partial_f", "Partial Obs. Flag", False, None),
        ("n_good_nod", "Good Node Count", False, None),
        ("obs_frac_n", "Observed Node Frac.", False, None),
        ("xovr_cal_q", "Crossover Correct. Qual.", False, None),
        ("solid_tide", "Solid Earth Tide", False, None),
        ("load_tidef", "Load Tide F", False, None),
        ("load_tideg", "Load Tide G", False, None),
        ("pole_tide", "Pole Tide", False, None),
        ("dry_trop_c", "Dry Tropo. Correct.", True, None),
        ("wet_trop_c", "Wet Tropo. Correct.", True, None),
        ("iono_c", "Ionosphere Correct.", True, None),
        ("xovr_cal_c", "Crossover Correct.", False, None),
    ]),
    ("Reach Metadata & SWORD Prior", [
        ("reach_id", "Reach ID", True, None),
        ("river_name", "River Name", True, None),
        ("reach_q", "Reach Quality", False, None),
        ("reach_q_b", "Reach Qual. Bitflag", False, None),
        ("p_wse", "Prior WSE", False, None),
        ("p_wse_var", "Prior WSE Variance", False, None),
        ("p_width", "Prior Width", False, None),
        ("p_wid_var", "Prior Width Variance", False, None),
        ("p_dam_id", "Dam ID", False, None),
        ("p_low_slp", "Low Slope Flag", False, None),
        ("continent_id", "Continent ID", False, None),
        ("crid", "CRID", False, None),
        ("sword_version", "SWORD Version", False, None),
        ("collection_shortname", "Collection Name", False, None),
        ("collection_version", "Collection Version", False, None),
        ("granuleUR", "Granule UR", False, None),
    ]),
]

LAKE_FIELDS = [
    ("Time & Orbit", [
        ("time", "Time (UTC)", True, None),
        ("time_tai", "Time (TAI)", True, None),
        ("time_str", "Time (String)", True, None),
        ("cycle_id", "Cycle ID", False, None),
        ("pass_id", "Pass ID", False, None),
        ("range_start_time", "Start Time", False, None),
        ("range_end_time", "End Time", False, None),
        ("ingest_time", "Ingest Time", False, None),
    ]),
    ("Hydrology & Storage", [
        ("wse", "WSE", True, "Water Surface Elevation (WSE)"),
        ("wse_u", "WSE Uncert.", True, "Water Surface Elevation (WSE)"),
        ("wse_r_u", "WSE Rand. Uncert.", False, "Water Surface Elevation (WSE)"),
        ("wse_std", "WSE Std. Dev.", False, "Water Surface Elevation (WSE)"),
        ("area_total", "Total Area", True, "Lake Area"),
        ("area_tot_u", "Total Area Uncert.", True, "Lake Area"),
        ("area_detct", "Detected Area", False, "Lake Area"),
        ("area_det_u", "Detected Area Uncert.", False, "Lake Area"),
        ("ds1_l", "Storage Change 1", False, "Storage Change (ds)"),
        ("ds1_l_u", "Storage Change 1 Uncert.", False, "Storage Change (ds)"),
        ("ds1_q", "Storage Change 1 Qual.", False, "Storage Change (ds)"),
        ("ds1_q_u", "Storage Change 1 Qual. Uncert.", False, "Storage Change (ds)"),
        ("ds2_l", "Storage Change 2", False, "Storage Change (ds)"),
        ("ds2_l_u", "Storage Change 2 Uncert.", False, "Storage Change (ds)"),
        ("ds2_q", "Storage Change 2 Qual.", False, "Storage Change (ds)"),
        ("ds2_q_u", "Storage Change 2 Qual. Uncert.", False, "Storage Change (ds)"),
    ]),
    ("Geometry & Identifiers", [
        ("reach_id", "Reach ID", True, None),
        ("obs_id", "Observation ID", False, None),
        ("geometry", "Geometry Shape", False, None),
        ("p_lat", "Latitude (Prior)", False, None),
        ("p_lon", "Longitude (Prior)", False, None),
        ("xtrk_dist", "Cross-Track Dist.", False, None),
        ("overlap", "Overlap Fraction", False, None),
        ("n_overlap", "Number of Overlaps", False, None),
    ]),
    ("Radar Metrics & Corrections", [
        ("quality_f", "Quality Flag", True, None),
        ("qual_f_b", "Quality Flag Bitflag", False, None),
        ("layovr_val", "Radar Layover Value", False, None),
        ("dark_frac", "Dark Water Frac.", False, None),
        ("ice_clim_f", "Clim. Ice Flag", False, None),
        ("ice_dyn_f", "Dynamic Ice Flag", False, None),
        ("partial_f", "Partial Obs. Flag", False, None),
        ("xovr_cal_q", "Crossover Correct. Qual.", False, None),
        ("xovr_cal_c", "Crossover Correct.", False, None),
        ("geoid_hght", "Geoid Height", False, None),
        ("solid_tide", "Solid Earth Tide", False, None),
        ("load_tidef", "Load Tide F", False, None),
        ("load_tideg", "Load Tide G", False, None),
        ("pole_tide", "Pole Tide", True, None),
        ("dry_trop_c", "Dry Tropo. Correct.", True, None),
        ("wet_trop_c", "Wet Tropo. Correct.", True, None),
        ("iono_c", "Ionosphere Correct.", True, None),
    ]),
    ("Metadata & PLD Prior", [
        ("lake_name", "Lake Name", True, None),
        ("p_res_id", "Prior Res. ID", False, None),
        ("p_ref_wse", "Prior Ref. WSE", False, None),
        ("p_ref_area", "Prior Ref. Area", False, None),
        ("p_date_t0", "Prior Date T0", False, None),
        ("p_ds_t0", "Prior Storage Change T0", False, None),
        ("p_storage", "Prior Storage", False, None),
        ("continent_id", "Continent ID", False, None),
        ("crid", "CRID", False, None),
        ("PLD_version", "PLD Version", False, None),
        ("collection_shortname", "Collection Name", False, None),
        ("collection_version", "Collection Version", False, None),
        ("granuleUR", "Granule UR", False, None),
    ]),
]


TYPES = {
    # Default for anything not listed below is QMetaType.Type.QString.
    # Large IDs (SWORD reach_id, PLD lake_id, granule_uR, etc.) are kept as
    # strings because they can exceed 32-bit integer range and we never do
    # arithmetic on them. Same goes for ISO timestamp strings (time_str,
    # range_start_time, …) — the numeric epoch versions are below.

    # ---- Time (epoch seconds) -------------------------------------------
    # Note: p_date_t0 is *not* here — it's an ISO datetime string, not epoch.
    'time':        QMetaType.Type.Double,
    'time_tai':    QMetaType.Type.Double,

    # ---- Orbit / pass --------------------------------------------------
    'cycle_id':    QMetaType.Type.Int,
    'pass_id':     QMetaType.Type.Int,

    # ---- WSE (reach & lake) --------------------------------------------
    'wse':         QMetaType.Type.Double,
    'wse_u':       QMetaType.Type.Double,
    'wse_r_u':     QMetaType.Type.Double,
    'wse_c':       QMetaType.Type.Double,
    'wse_c_u':     QMetaType.Type.Double,
    'wse_std':     QMetaType.Type.Double,

    # ---- River slope ----------------------------------------------------
    'slope':       QMetaType.Type.Double,
    'slope_u':     QMetaType.Type.Double,
    'slope_r_u':   QMetaType.Type.Double,
    'slope2':      QMetaType.Type.Double,
    'slope2_u':    QMetaType.Type.Double,
    'slope2_r_u':  QMetaType.Type.Double,

    # ---- River width ----------------------------------------------------
    'width':       QMetaType.Type.Double,
    'width_u':     QMetaType.Type.Double,
    'width_c':     QMetaType.Type.Double,
    'width_c_u':   QMetaType.Type.Double,

    # ---- Area (reach & lake) -------------------------------------------
    'area_total':  QMetaType.Type.Double,
    'area_tot_u':  QMetaType.Type.Double,
    'area_detct':  QMetaType.Type.Double,
    'area_det_u':  QMetaType.Type.Double,
    'area_wse':    QMetaType.Type.Double,
    'd_x_area':    QMetaType.Type.Double,
    'd_x_area_u':  QMetaType.Type.Double,

    # ---- Geometry / topology -------------------------------------------
    'p_lat':       QMetaType.Type.Double,
    'p_lon':       QMetaType.Type.Double,
    'node_dist':   QMetaType.Type.Double,
    'loc_offset':  QMetaType.Type.Double,
    'xtrk_dist':   QMetaType.Type.Double,
    'geoid_hght':  QMetaType.Type.Double,
    'geoid_slop':  QMetaType.Type.Double,
    'p_dist_out':  QMetaType.Type.Double,
    'p_length':    QMetaType.Type.Double,
    'n_reach_up':  QMetaType.Type.Int,
    'n_reach_dn':  QMetaType.Type.Int,
    'p_n_nodes':   QMetaType.Type.Int,
    'p_n_ch_max':  QMetaType.Type.Int,
    'p_n_ch_mod':  QMetaType.Type.Int,

    # ---- Lake-specific overlap / storage change ------------------------
    # `overlap` is intentionally absent — Hydrocron returns it as a String of
    # ';'-joined "<PLD_id>;<fraction>" pairs, not a single number.
    'n_overlap':   QMetaType.Type.Int,
    'ds1_l':       QMetaType.Type.Double,
    'ds1_l_u':     QMetaType.Type.Double,
    'ds1_q':       QMetaType.Type.Double,
    'ds1_q_u':     QMetaType.Type.Double,
    'ds2_l':       QMetaType.Type.Double,
    'ds2_l_u':     QMetaType.Type.Double,
    'ds2_q':       QMetaType.Type.Double,
    'ds2_q_u':     QMetaType.Type.Double,

    # ---- River discharge (per model: value, uncert., fraction, quality) -
    'dschg_c':     QMetaType.Type.Double, 'dschg_c_u':    QMetaType.Type.Double,
    'dschg_csf':   QMetaType.Type.Double, 'dschg_c_q':    QMetaType.Type.Int,
    'dschg_gc':    QMetaType.Type.Double, 'dschg_gc_u':   QMetaType.Type.Double,
    'dschg_gcsf':  QMetaType.Type.Double, 'dschg_gc_q':   QMetaType.Type.Int,
    'dschg_m':     QMetaType.Type.Double, 'dschg_m_u':    QMetaType.Type.Double,
    'dschg_msf':   QMetaType.Type.Double, 'dschg_m_q':    QMetaType.Type.Int,
    'dschg_gm':    QMetaType.Type.Double, 'dschg_gm_u':   QMetaType.Type.Double,
    'dschg_gmsf':  QMetaType.Type.Double, 'dschg_gm_q':   QMetaType.Type.Int,
    'dschg_b':     QMetaType.Type.Double, 'dschg_b_u':    QMetaType.Type.Double,
    'dschg_bsf':   QMetaType.Type.Double, 'dschg_b_q':    QMetaType.Type.Int,
    'dschg_gb':    QMetaType.Type.Double, 'dschg_gb_u':   QMetaType.Type.Double,
    'dschg_gbsf':  QMetaType.Type.Double, 'dschg_gb_q':   QMetaType.Type.Int,
    'dschg_h':     QMetaType.Type.Double, 'dschg_h_u':    QMetaType.Type.Double,
    'dschg_hsf':   QMetaType.Type.Double, 'dschg_h_q':    QMetaType.Type.Int,
    'dschg_gh':    QMetaType.Type.Double, 'dschg_gh_u':   QMetaType.Type.Double,
    'dschg_ghsf':  QMetaType.Type.Double, 'dschg_gh_q':   QMetaType.Type.Int,
    'dschg_o':     QMetaType.Type.Double, 'dschg_o_u':    QMetaType.Type.Double,
    'dschg_osf':   QMetaType.Type.Double, 'dschg_o_q':    QMetaType.Type.Int,
    'dschg_go':    QMetaType.Type.Double, 'dschg_go_u':   QMetaType.Type.Double,
    'dschg_gosf':  QMetaType.Type.Double, 'dschg_go_q':   QMetaType.Type.Int,
    'dschg_s':     QMetaType.Type.Double, 'dschg_s_u':    QMetaType.Type.Double,
    'dschg_ssf':   QMetaType.Type.Double, 'dschg_s_q':    QMetaType.Type.Int,
    'dschg_gs':    QMetaType.Type.Double, 'dschg_gs_u':   QMetaType.Type.Double,
    'dschg_gssf':  QMetaType.Type.Double, 'dschg_gs_q':   QMetaType.Type.Int,
    'dschg_i':     QMetaType.Type.Double, 'dschg_i_u':    QMetaType.Type.Double,
    'dschg_isf':   QMetaType.Type.Double, 'dschg_i_q':    QMetaType.Type.Int,
    'dschg_gi':    QMetaType.Type.Double, 'dschg_gi_u':   QMetaType.Type.Double,
    'dschg_gisf':  QMetaType.Type.Double, 'dschg_gi_q':   QMetaType.Type.Int,
    'dschg_q_b':   QMetaType.Type.LongLong,   # bitflag — may exceed 32 bits
    'dschg_gq_b':  QMetaType.Type.LongLong,
    'p_maf':       QMetaType.Type.Double,

    # ---- Radar metrics & atmospheric corrections -----------------------
    'layovr_val':  QMetaType.Type.Double,
    'dark_frac':   QMetaType.Type.Double,
    'ice_clim_f':  QMetaType.Type.Int,
    'ice_dyn_f':   QMetaType.Type.Int,
    'partial_f':   QMetaType.Type.Int,
    'n_good_nod':  QMetaType.Type.Int,
    'obs_frac_n':  QMetaType.Type.Double,
    'xovr_cal_q':  QMetaType.Type.Int,
    'solid_tide':  QMetaType.Type.Double,
    'load_tidef':  QMetaType.Type.Double,
    'load_tideg':  QMetaType.Type.Double,
    'pole_tide':   QMetaType.Type.Double,
    'dry_trop_c':  QMetaType.Type.Double,
    'wet_trop_c':  QMetaType.Type.Double,
    'iono_c':      QMetaType.Type.Double,
    'xovr_cal_c':  QMetaType.Type.Double,

    # ---- Quality flags --------------------------------------------------
    'reach_q':     QMetaType.Type.Int,
    'reach_q_b':   QMetaType.Type.LongLong,
    'quality_f':   QMetaType.Type.Int,
    'qual_f_b':    QMetaType.Type.LongLong,
    'p_low_slp':   QMetaType.Type.Int,
    'p_dam_id':    QMetaType.Type.Int,    # per RiverSP shapefile schema

    # ---- Prior values (SWORD river side) -------------------------------
    'p_wse':       QMetaType.Type.Double,
    'p_wse_var':   QMetaType.Type.Double,
    'p_width':     QMetaType.Type.Double,
    'p_wid_var':   QMetaType.Type.Double,

    # ---- Prior values (PLD lake side per Hydrocron API) ----------------
    # `p_res_id` and `p_date_t0` are strings → default QString, not listed.
    'p_ref_wse':   QMetaType.Type.Double,
    'p_ref_area':  QMetaType.Type.Double,
    'p_ds_t0':     QMetaType.Type.Double,
    'p_storage':   QMetaType.Type.Double,
}


def field_type(name):
    """Return the QMetaType for a Hydrocron field, defaulting to QString."""
    return TYPES.get(name, QMetaType.Type.QString)


_NUMERIC_TYPES = {QMetaType.Type.Double, QMetaType.Type.Int, QMetaType.Type.LongLong}
_MISSING_SENTINELS = {'', 'no_data', 'NA', 'na', 'NaN', 'nan', 'null', 'None'}


def coerce_value(name, value):
    """Convert a raw Hydrocron property value to something the QGIS field for
    `name` can actually store.

    Returns NULL (None) for numeric fields whose value is one of:
      - the SWOT-side 'no_data' / 'NaN' / '' sentinel,
      - a ';'-joined merged-observation value (e.g. 'overlap' = '76;1' across
        two PLD lakes — no single number applies),
      - any string that isn't parseable to the target numeric type.
    String fields are passed through unchanged.
    """
    if value is None:
        return None
    qt = field_type(name)
    if qt not in _NUMERIC_TYPES:
        return value
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if s in _MISSING_SENTINELS or ';' in s:
        return None
    try:
        if qt == QMetaType.Type.Double:
            return float(s)
        return int(s)  # Int / LongLong
    except (ValueError, TypeError):
        return None
