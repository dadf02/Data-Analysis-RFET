import os
import warnings  
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def plot_hysteresis_area_vs_ph(data_folder, file_mapping, devicetitle):
    V_GATE_COL = "GateV"
    I_DRAIN_COL = "DrainI"
    
    ph_points = []
    auc_diff_points = []
    
    print(f"\n--- Hysteresis (AUC Difference) Calibration for {devicetitle} ---")

    for filename, ph_val in file_mapping.items():
        file_path = os.path.join(data_folder, filename)
        
        if not os.path.exists(file_path):
            print(f"Warning: File {filename} not found in {data_folder}. Skipping.")
            continue
    
        df = pd.read_excel(file_path)
        
        # Split the data into forward (1st half) and backward (2nd half) sweeps FIRST
        midpoint = int(len(df) / 2)
        df_forward = df.iloc[:midpoint]
        df_backward = df.iloc[midpoint:]

        # Filter out negative drain currents for both sweeps
        df_forward = df_forward[df_forward[I_DRAIN_COL] > 0]
        df_backward = df_backward[df_backward[I_DRAIN_COL] > 0]

        if df_forward.empty or df_backward.empty:
            print(f"Warning: Not enough positive drain current data in {filename}. Skipping.")
            continue

        # Sort by Gate Voltage to ensure correct area calculation using the trapezoidal rule
        df_f_sorted = df_forward.sort_values(by=V_GATE_COL)
        df_b_sorted = df_backward.sort_values(by=V_GATE_COL)

        # Calculate Area Under the Curve (AUC) for Log(Id) vs Vg
        auc_forward = np.trapezoid((df_f_sorted[I_DRAIN_COL]), df_f_sorted[V_GATE_COL])
        auc_backward = np.trapezoid((df_b_sorted[I_DRAIN_COL]), df_b_sorted[V_GATE_COL])

        # Difference: Backward - Forward
        auc_diff = auc_backward - auc_forward
        
        ph_points.append(ph_val)
        auc_diff_points.append(auc_diff)
        
    if not ph_points:
        print("No valid data points extracted to plot.")
        return

    # Create summary DataFrame and sort by pH for clean plotting
    summary_df = pd.DataFrame({"pH": ph_points, "AUC_Difference": auc_diff_points})
    summary_df = summary_df.sort_values(by="pH")
    
    # Calculate Linear Regression for the calibration
    slope, intercept, r_value, _, _ = linregress(summary_df["pH"], summary_df["AUC_Difference"])
    r_squared = r_value**2
    
    print(f"Linear Equation: AUC_Diff = ({slope:.4e}) * pH + ({intercept:.4e})")
    print(f"R-squared (R²): {r_squared:.4f}")
    
    # Plotting
    plt.figure(figsize=(9, 7))
    
    # Scatter plot for extracted data
    plt.scatter(summary_df["pH"], summary_df["AUC_Difference"], color="crimson", s=90, zorder=3,
                label="Extracted AUC Difference")
    
    # Plot the linear fit line
    ph_range = np.linspace(summary_df["pH"].min() - 0.5, summary_df["pH"].max() + 0.5, 100)
    fit_line = slope * ph_range + intercept
    plt.plot(ph_range, fit_line, color="darkred", linestyle="--", linewidth=2,
             label=f"Linear Fit")

    # Plot Decorations
    plt.title(f"Hysteresis Calibration RFET: Area Difference vs pH\n{devicetitle}", fontsize=14, pad=15)
    plt.xlabel("pH Level", fontsize=12)
    plt.ylabel(r"AUC Difference (Backward - Forward) for $I_d$ vs $V_g$", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    
    # Add Equation Text Box
    equation_text = f"$\\Delta \\text{{AUC}} = ({slope:.2e}) \\cdot \\text{{pH}} + ({intercept:.2e})$\n$R^2 = {r_squared:.4f}$"
    plt.gca().text(0.05, 0.95, equation_text, transform=plt.gca().transAxes, fontsize=11,
                   verticalalignment="top",
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.85))
    
    plt.legend(loc="lower right", fontsize=10)
    plt.tight_layout()
    
    # Save output image
    output_chart_path = os.path.join(data_folder, f"hysteresis_calibration_{devicetitle}.png")
    plt.savefig(output_chart_path, dpi=300, bbox_inches="tight")    
    print(f"\nHysteresis calibration plot saved to: {output_chart_path}")
    
    plt.show()