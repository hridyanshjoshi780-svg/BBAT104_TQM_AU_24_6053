"""
Statistical Quality Control (SQC) Module for BBAT104 TQM Project.
Generates Control Charts (Individual X-Chart, Run Chart) with UCL, Mean, and LCL
to monitor catalog search response times and process stability.
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Safe backend for non-GUI initialization, switches to TkAgg inside Tkinter
import matplotlib.pyplot as plt
from database import get_connection


def fetch_latency_data(limit: int = 50) -> pd.DataFrame:
    """Fetch recent search performance metrics from database into a pandas DataFrame."""
    conn = get_connection()
    query = """
        SELECT id, timestamp, duration_ms, query, result_count
        FROM search_metrics
        ORDER BY id DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()

    if not df.empty:
        # Sort chronologically for control chart
        df = df.sort_values(by="id").reset_index(drop=True)
    return df


def generate_sqc_chart(limit: int = 40):
    """
    Generate an SQC Control Chart (X-Chart) for catalog search latency.
    Computes:
      - Center Line (CL) = Mean
      - Upper Control Limit (UCL) = Mean + 3 * StdDev
      - Lower Control Limit (LCL) = max(0, Mean - 3 * StdDev)
    Returns: (fig, stats_dict)
    """
    df = fetch_latency_data(limit)

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=100)
    fig.patch.set_facecolor("#1e222d")
    ax.set_facecolor("#262b38")

    stats = {
        "count": 0,
        "mean": 0.0,
        "std": 0.0,
        "ucl": 0.0,
        "lcl": 0.0,
        "out_of_control_count": 0
    }

    if df.empty or len(df) < 3:
        ax.text(
            0.5, 0.5,
            "Insufficient search data to plot SQC Control Chart.\nPerform a few book searches to populate metrics.",
            color="#ffffff", ha="center", va="center", fontsize=12
        )
        ax.set_axis_off()
        fig.tight_layout()
        return fig, stats

    y = df["duration_ms"].to_numpy()
    x = np.arange(1, len(y) + 1)

    mean_val = float(np.mean(y))
    std_val = float(np.std(y, ddof=1)) if len(y) > 1 else 0.0
    ucl = mean_val + (3 * std_val)
    lcl = max(0.0, mean_val - (3 * std_val))

    out_of_control_mask = (y > ucl) | (y < lcl)
    out_of_control_count = int(np.sum(out_of_control_mask))

    stats["count"] = len(y)
    stats["mean"] = round(mean_val, 2)
    stats["std"] = round(std_val, 2)
    stats["ucl"] = round(ucl, 2)
    stats["lcl"] = round(lcl, 2)
    stats["out_of_control_count"] = out_of_control_count

    # Plot Control Limits
    ax.axhline(ucl, color="#e74c3c", linestyle="--", linewidth=1.5, label=f"UCL (+3σ) = {ucl:.2f} ms")
    ax.axhline(mean_val, color="#2ecc71", linestyle="-", linewidth=2.0, label=f"Center Line (Mean) = {mean_val:.2f} ms")
    ax.axhline(lcl, color="#3498db", linestyle="--", linewidth=1.5, label=f"LCL (-3σ) = {lcl:.2f} ms")

    # Plot in-control points
    ax.plot(x, y, marker="o", color="#38bdf8", linewidth=1.5, alpha=0.85, label="Search Response Time")

    # Highlight out-of-control points in red
    if out_of_control_count > 0:
        ax.scatter(x[out_of_control_mask], y[out_of_control_mask], color="#ff4757", s=80, zorder=5, label="Special Cause Variation (Out of Limits)")

    ax.set_title("TQM Statistical Quality Control (SQC) Chart — Catalog Search Latency (Q04)", color="#ffffff", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Sample Request Number", color="#94a3b8", fontsize=10)
    ax.set_ylabel("Latency (ms)", color="#94a3b8", fontsize=10)

    ax.tick_params(colors="#94a3b8", labelsize=9)
    ax.grid(True, linestyle=":", alpha=0.3, color="#64748b")
    ax.legend(loc="upper right", facecolor="#1e222d", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    fig.tight_layout()
    return fig, stats
