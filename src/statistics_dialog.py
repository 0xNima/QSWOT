import os

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from .stats import (
    numeric_field_names,
    all_field_names,
    time_field_candidates,
    fetch_pair,
    fetch_timeseries,
    compute_correlation,
    linear_regression,
)


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), 'statistics_dialog.ui')
)


# Pick a sensible default group field for a SWOT layer.
_GROUP_FIELD_PREFERENCE = ('reach_id', 'lake_id', 'river_name', 'lake_name')
_NO_GROUP = '(none)'

_ZOOM_FACTOR = 1.2  # per scroll-wheel tick


def _scroll_zoom(canvas, event):
    """Zoom in/out on a matplotlib canvas centered on the cursor position.

    Works on whichever axes the cursor is currently over, so a future
    multi-panel figure would zoom only the panel under the mouse."""
    ax = event.inaxes
    if ax is None or event.xdata is None or event.ydata is None:
        return
    scale = _ZOOM_FACTOR if event.button == 'up' else 1.0 / _ZOOM_FACTOR

    xdata, ydata = event.xdata, event.ydata
    x_lo, x_hi = ax.get_xlim()
    y_lo, y_hi = ax.get_ylim()
    new_x_range = (x_hi - x_lo) / scale
    new_y_range = (y_hi - y_lo) / scale

    # Keep the point under the cursor stationary on screen.
    rel_x = (xdata - x_lo) / (x_hi - x_lo) if x_hi != x_lo else 0.5
    rel_y = (ydata - y_lo) / (y_hi - y_lo) if y_hi != y_lo else 0.5
    ax.set_xlim(xdata - new_x_range * rel_x,
                xdata + new_x_range * (1 - rel_x))
    ax.set_ylim(ydata - new_y_range * rel_y,
                ydata + new_y_range * (1 - rel_y))
    canvas.draw_idle()


class StatisticsDialog(QDialog, FORM_CLASS):
    """Tabbed stats dialog for SWOT vector layers: time series + correlation,
    sharing a single Subset filter at the top."""

    def __init__(self, layer, parent=None, default_subset='all'):
        """default_subset: 'all' or 'selected' — which radio is pre-checked."""
        super().__init__(parent)
        self.setupUi(self)
        self.layer = layer
        self.header_label.setText(f"Layer: {layer.name()}")
        self.setWindowTitle(f"Statistics — {layer.name()}")

        if default_subset == 'selected':
            self.selected_radio.setChecked(True)

        self._numeric_names = numeric_field_names(layer)
        self._all_names = all_field_names(layer)
        self._time_names = time_field_candidates(layer)

        self._init_timeseries_tab()
        self._init_correlation_tab()

        # Embed one matplotlib canvas per tab so flipping between tabs keeps
        # both plots intact.
        self._ts_canvas, self._ts_figure = self._make_plot(self.ts_plot_layout)
        self._corr_canvas, self._corr_figure = self._make_plot(self.corr_plot_layout)

        self.ts_plot_button.clicked.connect(self.run_timeseries)
        self.corr_compute_button.clicked.connect(self.run_correlation)

    # ---- init helpers ---------------------------------------------------

    def _init_timeseries_tab(self):
        self.ts_value_combo.addItems(self._numeric_names)
        self.ts_time_combo.addItems(self._time_names)
        self.ts_group_combo.addItems([_NO_GROUP] + self._all_names)
        # Best-effort defaults
        self._select_default(self.ts_value_combo, ('wse', 'area_total'))
        self._select_default(self.ts_time_combo, ('time', 'time_str'))
        default_group = next(
            (n for n in _GROUP_FIELD_PREFERENCE if n in self._all_names), None
        )
        if default_group:
            self.ts_group_combo.setCurrentText(default_group)

        if not self._numeric_names:
            self.ts_plot_button.setEnabled(False)
            self.ts_status_label.setText("Layer has no numeric fields.")

    def _init_correlation_tab(self):
        self.corr_x_combo.addItems(self._numeric_names)
        self.corr_y_combo.addItems(self._numeric_names)
        self._select_default(self.corr_x_combo, ('wse',))
        self._select_default(self.corr_y_combo, ('width', 'area_total', 'slope'))
        if len(self._numeric_names) < 2:
            self.corr_compute_button.setEnabled(False)
            self.corr_stats_label.setText("Need at least 2 numeric fields.")

    @staticmethod
    def _select_default(combo, candidates):
        for name in candidates:
            idx = combo.findText(name)
            if idx >= 0:
                combo.setCurrentIndex(idx)
                return

    @staticmethod
    def _make_plot(layout):
        figure = Figure(figsize=(6, 4))
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, canvas.parentWidget())
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        # Mouse-wheel zoom centered on cursor position.
        canvas.mpl_connect(
            'scroll_event', lambda evt, c=canvas: _scroll_zoom(c, evt)
        )
        return canvas, figure

    # ---- shared subset state -------------------------------------------

    def _current_subset(self):
        """Returns (expression_or_None, only_selected_bool)."""
        if self.selected_radio.isChecked():
            return None, True
        if self.filter_radio.isChecked():
            expr = self.filter_edit.text().strip()
            return (expr or None), False
        return None, False

    # ---- time series action --------------------------------------------

    def run_timeseries(self):
        value_field = self.ts_value_combo.currentText()
        time_field = self.ts_time_combo.currentText()
        group_choice = self.ts_group_combo.currentText()
        group_field = None if group_choice == _NO_GROUP else group_choice
        expression, only_selected = self._current_subset()

        try:
            groups, dropped = fetch_timeseries(
                self.layer, value_field, time_field, group_field,
                expression=expression, only_selected=only_selected,
            )
        except Exception as e:
            QMessageBox.warning(self, "Time Series", f"Could not read values: {e}")
            return

        if not groups:
            self.ts_status_label.setText("No valid (time, value) pairs to plot.")
            self._clear(self._ts_figure, self._ts_canvas)
            return

        total_pts = sum(len(t) for t, _ in groups.values())
        suffix = f"  (dropped {dropped} group(s) past cap)" if dropped else ""
        self.ts_status_label.setText(
            f"{len(groups)} group(s) · {total_pts:,} point(s){suffix}"
        )
        self._draw_timeseries(groups, value_field, time_field, group_field)

    def _draw_timeseries(self, groups, value_field, time_field, group_field):
        self._ts_figure.clear()
        ax = self._ts_figure.add_subplot(111)
        show_markers = self.ts_markers_check.isChecked()
        marker = 'o' if show_markers else ''

        for key, (times, values) in groups.items():
            label = str(key) if key is not None else 'all'
            ax.plot(times, values, marker=marker, markersize=3, linewidth=1,
                    alpha=0.75, label=label)

        ax.set_xlabel(time_field)
        ax.set_ylabel(value_field)
        ax.grid(True, alpha=0.3)
        self._ts_figure.autofmt_xdate()
        if group_field is not None and len(groups) <= 15:
            ax.legend(loc='best', fontsize=8, ncol=2)
        self._ts_figure.tight_layout()
        self._ts_canvas.draw()

    # ---- correlation action --------------------------------------------

    def run_correlation(self):
        x_field = self.corr_x_combo.currentText()
        y_field = self.corr_y_combo.currentText()
        if x_field == y_field:
            QMessageBox.information(
                self, "Correlation", "X and Y must be different fields."
            )
            return

        method = self._selected_method()
        expression, only_selected = self._current_subset()

        try:
            xs, ys = fetch_pair(
                self.layer, x_field, y_field,
                expression=expression, only_selected=only_selected,
            )
        except Exception as e:
            QMessageBox.warning(self, "Correlation", f"Could not read values: {e}")
            return

        if len(xs) < 2:
            self.corr_stats_label.setText(
                f"Only {len(xs)} valid pair(s) — need at least 2 to correlate."
            )
            self._clear(self._corr_figure, self._corr_canvas)
            return

        try:
            r, p, n = compute_correlation(xs, ys, method=method)
        except Exception as e:
            QMessageBox.warning(self, "Correlation", str(e))
            return

        self._draw_correlation(xs, ys, x_field, y_field)
        self.corr_stats_label.setText(self._format_corr_stats(r, p, n, method))

    def _selected_method(self):
        if self.spearman_radio.isChecked():
            return 'spearman'
        if self.kendall_radio.isChecked():
            return 'kendall'
        return 'pearson'

    def _draw_correlation(self, xs, ys, x_field, y_field):
        self._corr_figure.clear()
        ax = self._corr_figure.add_subplot(111)
        ax.scatter(xs, ys, alpha=0.35, s=12)
        if self.corr_regression_check.isChecked() and len(xs) >= 2:
            slope, intercept = linear_regression(xs, ys)
            xline = np.array([float(xs.min()), float(xs.max())])
            ax.plot(xline, slope * xline + intercept,
                    color='red', linewidth=1.2)
        ax.set_xlabel(x_field)
        ax.set_ylabel(y_field)
        ax.grid(True, alpha=0.3)
        self._corr_figure.tight_layout()
        self._corr_canvas.draw()

    @staticmethod
    def _format_corr_stats(r, p, n, method):
        p_str = "—" if np.isnan(p) else f"{p:.3g}"
        return f"{method.capitalize()}:   r = {r:.4f}    p = {p_str}    n = {n:,}"

    # ---- common ---------------------------------------------------------

    @staticmethod
    def _clear(figure, canvas):
        figure.clear()
        canvas.draw()
