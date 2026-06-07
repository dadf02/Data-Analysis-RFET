import os
import warnings  
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")



def plot_combined_calibration_curves(data_folder, file_mapping, devicetitle):
    V_GATE_COL = "GateV"
    I_DRAIN_COL = "DrainI"
    
    #In this version, it is plotted on the same graph the calibration curves from both sweeps, the forward and backward one
    sweep_configs = [
        ("Full Sweep (All)", True, True),
        ("Forward Sweep (1st Half)", False, True),
        ("Backward Sweep (2nd Half)", False, False)
    ]
    
    colors = {
        "Full Sweep (All)": ("darkorange", "orange"),
        "Forward Sweep (1st Half)": ("forestgreen", "darkgreen"),
        "Backward Sweep (2nd Half)": ("mediumpurple", "indigo")
    }
    
    plt.figure(figsize=(10, 8))
    text_box_lines = [] 

    print(f"\n--- Calibration Results for {devicetitle} ---")

    for label, all_curve, first_go in sweep_configs:
        ph_points = []
        current_points = []
        skip_sweep = False

        for filename, ph_val in file_mapping.items():
            file_path = os.path.join(data_folder, filename)
            
            if not os.path.exists(file_path):
                print(f"Warning: File {filename} not found in {data_folder}. Skipping.")
                continue
        
            df = pd.read_excel(file_path)
            
            if all_curve:
                df_sliced = df
            elif not all_curve and first_go:
                df_sliced = df[:int(len(df)/2)]
            elif not all_curve and not first_go:
                df_sliced = df[int(len(df)/2):]

            # Filter gate voltage and positive drain currents: based on the collected images, I decided to use [-1.5, -1] voltage range and we also need to excale negative but in this window these ones are minimal
            filtered_df = df_sliced[(df_sliced[V_GATE_COL] >= -1.5) & (df_sliced[V_GATE_COL] <= -1) & (df_sliced[I_DRAIN_COL] >= 0)]

            if filtered_df.empty:
                print(f"Warning: No valid data found for {filename} in {label}!")
                skip_sweep = True
                break

            log_currents = np.log10(filtered_df[I_DRAIN_COL])
            avg_log_current = log_currents.mean()
            
            ph_points.append(ph_val)
            current_points.append(avg_log_current)
            
        if skip_sweep or not ph_points:
            print(f"Skipping plot for {label} due to missing data.")
            continue

        summary_df = pd.DataFrame({"pH": ph_points, "Drain_Current": current_points})
        summary_df = summary_df.sort_values(by="pH")
        
        slope, intercept, r_value, _ , _ = linregress(summary_df["pH"], summary_df["Drain_Current"])
        r_squared = r_value**2
        
        print(f"\n[{label}]")
        print(f"  Linear Equation: Log (Id) = ({slope:.4e}) * pH + ({intercept:.4e})")
        print(f"  R-squared (R²): {r_squared:.4f}")
        
        text_box_lines.append(f"{label}\n$Log(I_d) = ({slope:.2e}) \\cdot \\text{{pH}} + ({intercept:.2e})$\n$R^2 = {r_squared:.4f}$")

        scatter_color, line_color = colors[label]

        plt.scatter(summary_df["pH"], summary_df["Drain_Current"], color=scatter_color, s=80, zorder=3,
                    label=f"{label} Data")
        
        ph_range = np.linspace(summary_df["pH"].min() - 0.5, summary_df["pH"].max() + 0.5, 100)
        fit_line = slope * ph_range + intercept
        plt.plot(ph_range, fit_line, color=line_color, linestyle="--", linewidth=2,
                 label=f"{label} Fit")

    plt.title(f"Calibration Curves RFET: Log Drain Current vs pH\n{devicetitle}", fontsize=14, pad=15)
    plt.xlabel("pH Level", fontsize=12)
    plt.ylabel("Avg Log Drain Current with [-1.5, -1]V in gate ($log(I_d))$", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    
    combined_text = "\n\n".join(text_box_lines)
    plt.gca().text(0.05, 0.95, combined_text, transform=plt.gca().transAxes, fontsize=9,
                   verticalalignment="top",
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.85))
    
    plt.legend(loc="lower right", fontsize=10)
    plt.tight_layout()
    output_chart_path = os.path.join(data_folder, f"combined_calibration_curve_{devicetitle}.png")
    plt.savefig(output_chart_path, dpi=300, bbox_inches="tight")
    plt.show()




#OLD VERSION: NEEDED TO SPECIFIY WHICH SWEEP WE WERE DEALING WITH
'''   
def plot_calibration_current_vs_ph(data_folder, file_mapping, devicetitle, all_curve = True, first_go = True):
    V_GATE_COL = "GateV"
    I_DRAIN_COL = "DrainI"
    
    ph_points = []
    current_points = []

    for filename, ph_val in file_mapping.items():
        file_path = os.path.join(data_folder, filename)
        
        if not os.path.exists(file_path):
            print(f"Warning: File {filename} not found in {data_folder}. Skipping.")
            continue
    
        df = pd.read_excel(file_path)
        #Choose if take first go, second go or all in one:
        if all_curve:
            df = df
        elif not(all_curve) and first_go:
            df = df[:int(len(df)/2)]
        elif not(all_curve) and not(first_go):
            df = df[int(len(df)/2):]

        # Only voltages between -2 and -1 v and drain current positive
        
        filtered_df = df[(df[V_GATE_COL] >= -1.5) & (df[V_GATE_COL] <= -1)& (df[I_DRAIN_COL] >= 0)]

        if filtered_df.empty:
            print(f"Warning: No valid data found for {filename} after filtering window!")
            break

        log_currents = np.log10(filtered_df[I_DRAIN_COL])
        
        # Extract the average log drain current in this window
        avg_log_current = log_currents.mean()
        
        ph_points.append(ph_val)
        current_points.append(avg_log_current)
        
    summary_df = pd.DataFrame({"pH": ph_points, "Drain_Current": current_points})
    summary_df = summary_df.sort_values(by="pH")
    
    #Calibration
    slope, intercept, r_value, p_value, std_err = linregress(summary_df["pH"], summary_df["Drain_Current"])
    r_squared = r_value**2
    
    print("\n--- Calibration Results ---")
    print(f"Linear Equation: Id = ({slope:.4e}) * pH + ({intercept:.4e})")
    print(f"R-squared (R²): {r_squared:.4f}")
    
    #Plot scatter
    plt.figure(figsize=(8, 6))
    plt.scatter(summary_df["pH"],summary_df["Drain_Current"],color="darkorange",s=100,zorder=3,
                label="Extracted Data",)
    
    # Plot the linear fit line
    ph_range = np.linspace(summary_df["pH"].min() - 0.5, summary_df["pH"].max() + 0.5, 100)
    fit_line = slope * ph_range + intercept
    plt.plot(ph_range,fit_line,color="navy",linestyle="--",linewidth=2,
             label=f"Fit Line (R² = {r_squared:.4f})",)
    plt.title(f"Calibration Curve RFET device : Drain Current vs pH - {devicetitle}", fontsize=14, pad=15)
    plt.xlabel("pH Level", fontsize=12)
    plt.ylabel("Avg Log Drain Current in [-1.5,-1]V in gate ($I_d$)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    equation_text = f"$I_d = ({slope:.2e}) \\cdot \\text{{pH}} + ({intercept:.2e})$\n$R^2 = {r_squared:.4f}$"
    plt.gca().text(0.05,0.95,equation_text,transform=plt.gca().transAxes,fontsize=11,
                   verticalalignment="top",
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8))
    plt.legend(loc="lower right")
    plt.tight_layout()
    
    output_chart_path = os.path.join(data_folder, f"calibration_curve_{devicetitle}.png")
    plt.savefig(output_chart_path, dpi=300, bbox_inches="tight")    
    print(f"\nCalibration plot saved to: {output_chart_path}")
    plt.show()
'''