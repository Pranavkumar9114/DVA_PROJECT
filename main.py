import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, date
import requests
import csv
import io
import seaborn as sns
import numpy as np
import matplotlib.dates as mdates

HOSTED_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"

root = tk.Tk()
root.title("COVID-19 Data Tracker Dashboard (Our World in Data)")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")
root.configure(bg="#e9ecef")

canvas = tk.Canvas(root, bg="#e9ecef", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", on_configure)

canvas_window = canvas.create_window((screen_width // 2, 0), window=scrollable_frame, anchor="n")

def center_window(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", center_window)

canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

world_data = None
country_data = None
historical_data = None
country_map = None
data = None
live_world_data = None
live_india_data = None
compare_country_data = None 

def fetch_data():
    try:
        global world_data, country_data, historical_data, country_map, data
  
        response = requests.get(HOSTED_URL, timeout=10)
        response.raise_for_status()
        if not response.text.strip():
            raise ValueError("Empty response from server")

        csv_file = io.StringIO(response.text)
        csv_reader = csv.DictReader(csv_file)
        
        data = {}
        for row in csv_reader:
            iso_code = row.get("iso_code", "")
            if not iso_code:
                continue
            if iso_code not in data:
                data[iso_code] = {
                    "location": row.get("location", ""),
                    "data": []
                }
            data_entry = {
                "date": row.get("date", ""),
                "total_cases": float(row.get("total_cases", 0)) if row.get("total_cases") else 0,
                "total_deaths": float(row.get("total_deaths", 0)) if row.get("total_deaths") else 0
            }
            data[iso_code]["data"].append(data_entry)

        world_code = "OWID_WRL"
        if world_code not in data:
            raise ValueError("World data not found")
        
        world_metrics = data[world_code]["data"]
   
        end_2024 = None
        for entry in reversed(world_metrics):
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            cases = entry.get("total_cases", 0) or 0
            deaths = entry.get("total_deaths", 0) or 0
            if cases > 0 or deaths > 0:
                if date_obj <= date(2024, 12, 31):
                    end_2024 = entry
                    break
        if not end_2024:
            raise ValueError("No valid global data found with non-zero metrics")

        world_cases = int(end_2024.get("total_cases", 0) or 0)
        world_deaths = int(end_2024.get("total_deaths", 0) or 0)
        if world_cases == 0 and world_deaths == 0:
            raise ValueError("Invalid global data: all metrics are zero")
 
        world_recovered = int(world_cases * 0.95) - world_deaths
        world_active = world_cases - (world_recovered + world_deaths)
        if world_active < 0:
            world_active = 0
        world_data = (world_active, world_cases, world_recovered, world_deaths)

        country_input = country_entry.get().strip().upper()
        if not country_input:
            country_input = country_dropdown.get().strip().upper()
        country_code = None
        
        country_map = {
            "USA": "USA", "UNITED STATES": "USA", "INDIA": "IND", "BRAZIL": "BRA",
            "FRANCE": "FRA", "GERMANY": "DEU", "ITALY": "ITA", "SPAIN": "ESP",
            "CHINA": "CHN", "JAPAN": "JPN", "SOUTH KOREA": "KOR", "AUSTRALIA": "AUS",
            "CANADA": "CAN", "UNITED KINGDOM": "GBR", "UK": "GBR", "RUSSIA": "RUS",
            "MEXICO": "MEX", "SOUTH AFRICA": "ZAF", "ARGENTINA": "ARG", "CHILE": "CHL",
            "INDONESIA": "IDN", "PAKISTAN": "PAK", "BANGLADESH": "BGD"
        }
        country_code = country_map.get(country_input)
        if not country_code:
            for code, info in data.items():
                if code == country_input or info["location"].upper() == country_input:
                    country_code = code
                    break
            if not country_code:
                for code, info in data.items():
                    location = info["location"].upper()
                    if country_input in location or location in country_input:
                        country_code = code
                        break
            if not country_code:
                raise ValueError(f"Country '{country_entry.get() or country_dropdown.get()}' not found. Try the ISO code or check spelling.")

        country_metrics = data[country_code]["data"]
 
        country_latest = None
        latest_date = None
        for entry in reversed(country_metrics):
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            cases = entry.get("total_cases", 0) or 0
            deaths = entry.get("total_deaths", 0) or 0
            if (cases > 0 or deaths > 0) and date_obj <= date(2024, 12, 31):
                country_latest = entry
                latest_date = date_obj
                break
        if not country_latest:
            raise ValueError(f"No valid data found for {country_entry.get() or country_dropdown.get()} up to 2024")

        country_cases = int(country_latest.get("total_cases", 0) or 0)
        country_deaths = int(country_latest.get("total_deaths", 0) or 0)
        if country_cases == 0 and country_deaths == 0:
            raise ValueError(f"No non-zero data found for {country_entry.get() or country_dropdown.get()}")

        country_recovered = int(country_cases * 0.98) - country_deaths
        if country_recovered < 0:
            country_recovered = 0
        country_active = country_cases - (country_recovered + country_deaths)
        if country_active < 0:
            country_active = 0

        country_data = {
            "cases": country_cases,
            "recovered": country_recovered,
            "deaths": country_deaths,
            "active": country_active,
            "last_date": latest_date.strftime("%Y-%m-%d") if latest_date else "Unknown"
        }

        historical_data = {"cases": {}, "recovered": {}, "deaths": {}}
        start_date = date(2020, 1, 1)
        end_date = date(2024, 8, 4)
        for entry in country_metrics:
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            if start_date <= date_obj <= end_date:
                date_str = date_obj.strftime("%m/%d/%y")
                cases = int(entry.get("total_cases", 0) or 0)
                deaths = int(entry.get("total_deaths", 0) or 0)
                historical_data["cases"][date_str] = cases
                historical_data["deaths"][date_str] = deaths
                recovered = int(cases * 0.98) - deaths if cases > 0 else 0
                historical_data["recovered"][date_str] = recovered if recovered > 0 else 0

        update_dashboard()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {str(e)}")

def fetch_compare_data():
    try:
        global compare_country_data
        country_input = compare_country_entry.get().strip().upper()
        if not country_input:
            raise ValueError("Please enter a comparison country name!")
        
        country_code = None
        country_code = country_map.get(country_input)
        if not country_code:
            for code, info in data.items():
                if code == country_input or info["location"].upper() == country_input:
                    country_code = code
                    break
            if not country_code:
                for code, info in data.items():
                    location = info["location"].upper()
                    if country_input in location or location in country_input:
                        country_code = code
                        break
            if not country_code:
                raise ValueError(f"Comparison country '{country_input}' not found. Try the ISO code or check spelling.")

        country_metrics = data[country_code]["data"]
        country_latest = None
        latest_date = None
        for entry in reversed(country_metrics):
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            cases = entry.get("total_cases", 0) or 0
            deaths = entry.get("total_deaths", 0) or 0
            if (cases > 0 or deaths > 0) and date_obj <= date(2024, 12, 31):
                country_latest = entry
                latest_date = date_obj
                break
        if not country_latest:
            raise ValueError(f"No valid data found for {country_input} up to 2024")

        country_cases = int(country_latest.get("total_cases", 0) or 0)
        country_deaths = int(country_latest.get("total_deaths", 0) or 0)
        if country_cases == 0 and country_deaths == 0:
            raise ValueError(f"No non-zero data found for {country_input}")
        country_recovered = int(country_cases * 0.98) - country_deaths
        if country_recovered < 0:
            country_recovered = 0
        country_active = country_cases - (country_recovered + country_deaths)
        if country_active < 0:
            country_active = 0

        compare_country_data = {
            "cases": country_cases,
            "recovered": country_recovered,
            "deaths": country_deaths,
            "active": country_active,
            "last_date": latest_date.strftime("%Y-%m-%d") if latest_date else "Unknown",
            "historical_cases": {}
        }

        start_date = date(2020, 1, 1)  
        end_date = date(2024, 12, 31) 
        for entry in country_metrics:
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            if start_date <= date_obj <= end_date:
                date_str = date_obj.strftime("%m/%d/%y")
                cases = int(entry.get("total_cases", 0) or 0)
                compare_country_data["historical_cases"][date_str] = cases

        compare_info.delete(1.0, tk.END)
        compare_info.insert(tk.END, f"Comparison Country: {compare_country_entry.get().capitalize()}\n"
                                   f"Confirmed: {compare_country_data['cases']:,}\n"
                                   f"Active: {compare_country_data['active']:,}\n"
                                   f"Recovered: {compare_country_data['recovered']:,}\n"
                                   f"Deaths: {compare_country_data['deaths']:,}\n"
                                   f"Data as of: {compare_country_data['last_date']}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch comparison data: {str(e)}")

def export_to_csv():
    try:
        if not country_data or not historical_data:
            raise ValueError("No data available to export. Fetch data first!")
        
        country = country_entry.get().strip().capitalize() or country_dropdown.get().strip().capitalize()
        filename = f"{country}_covid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Country", country])
            writer.writerow(["Confirmed Cases", country_data['cases']])
            writer.writerow(["Active Cases", country_data['active']])
            writer.writerow(["Recovered", country_data['recovered']])
            writer.writerow(["Deaths", country_data['deaths']])
            writer.writerow(["Last Date", country_data['last_date']])
            writer.writerow([])
            writer.writerow(["Date", "Total Cases", "Active Cases", "Recovered", "Deaths"])
            dates = sorted(historical_data["cases"].keys(), 
                          key=lambda x: datetime.strptime(x, "%m/%d/%y"))
            for date in dates:
                active = max(0, historical_data["cases"][date] - historical_data["recovered"][date] - historical_data["deaths"][date])
                writer.writerow([
                    date,
                    historical_data["cases"][date],
                    active,
                    historical_data["recovered"][date],
                    historical_data["deaths"][date]
                ])
        
        messagebox.showinfo("Success", f"Data exported to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {str(e)}")

def fetch_live_covid_data():
    try:
        global live_world_data, live_india_data
        response = requests.get(HOSTED_URL, timeout=10)
        response.raise_for_status()
        csv_file = io.StringIO(response.text)
        csv_reader = csv.DictReader(csv_file)

        world_data = next((row for row in csv_reader if row['iso_code'] == 'OWID_WRL'), None)
        if world_data:
            live_world_data = {
                "active": int(float(world_data.get('total_cases', 0) or 0)) - int(float(world_data.get('total_deaths', 0) or 0)),
                "confirmed": int(float(world_data.get('total_cases', 0) or 0)),
                "recovered": int(float(world_data.get('total_cases', 0) or 0) * 0.95) - int(float(world_data.get('total_deaths', 0) or 0)),
                "deaths": int(float(world_data.get('total_deaths', 0) or 0)),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            live_world_data = {"active": 0, "confirmed": 0, "recovered": 0, "deaths": 0, "last_update": "N/A"}

        csv_file.seek(0)
        next(csv_reader)  
        india_data = next((row for row in csv_reader if row['iso_code'] == 'IND'), None)
        if india_data:
            live_india_data = {
                "active": int(float(india_data.get('total_cases', 0) or 0)) - int(float(india_data.get('total_deaths', 0) or 0)),
                "confirmed": int(float(india_data.get('total_cases', 0) or 0)),
                "recovered": int(float(india_data.get('total_cases', 0) or 0) * 0.98) - int(float(india_data.get('total_deaths', 0) or 0)),
                "deaths": int(float(india_data.get('total_deaths', 0) or 0)),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            live_india_data = {"active": 0, "confirmed": 0, "recovered": 0, "deaths": 0, "last_update": "N/A"}

        live_world_label.config(text=f"World - Active: {live_world_data['active']:,} | Confirmed: {live_world_data['confirmed']:,} | "
                                   f"Recovered: {live_world_data['recovered']:,} | Deaths: {live_world_data['deaths']:,} | "
                                   f"Last Updated: {live_world_data['last_update']}")
        live_india_label.config(text=f"India - Active: {live_india_data['active']:,} | Confirmed: {live_india_data['confirmed']:,} | "
                                   f"Recovered: {live_india_data['recovered']:,} | Deaths: {live_india_data['deaths']:,} | "
                                   f"Last Updated: {live_india_data['last_update']}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch live COVID data: {str(e)}")

def update_dashboard():
    active_label.config(text=f"Active Cases: {world_data[0]:,}")
    confirmed_label.config(text=f"Confirmed Cases: {world_data[1]:,}")
    recovered_label.config(text=f"Recovered: {world_data[2]:,}")
    deaths_label.config(text=f"Deaths: {world_data[3]:,}")
    last_update_label.config(text=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    country_info.delete(1.0, tk.END)
    country_info.insert(tk.END, f"Country: {(country_entry.get() or country_dropdown.get()).capitalize()}\n"
                                f"Confirmed: {country_data['cases']:,}\n"
                                f"Active: {country_data['active']:,}\n"
                                f"Recovered: {country_data['recovered']:,}\n"
                                f"Deaths: {country_data['deaths']:,}\n"
                                f"Data as of: {country_data['last_date']}")

def format_indian_number(value, pos):
    """Format numbers into Indian conventions (e.g., X.XCr, X.XL, X.XK)."""
    if value >= 1e7:  
        return f"{value/1e7:.1f}Cr"
    elif value >= 1e5: 
        return f"{value/1e5:.1f}L"
    elif value >= 1e3:  
        return f"{value/1e3:.1f}K"
    else:
        return f"{value:.0f}"

def plot_graphs():
    try:
        country = (country_entry.get().strip() or country_dropdown.get().strip())
        if not country:
            raise ValueError("Please select or enter a country name!")

        confirmed, active, recovered, deaths = country_data['cases'], country_data['active'], country_data['recovered'], country_data['deaths']

        date_objects = []
        for date_str in historical_data["cases"].keys():
            date_obj = datetime.strptime(date_str, "%m/%d/%y").date()
            date_objects.append((date_obj, date_str))
        date_objects.sort()  
        dates = [date_str for _, date_str in date_objects]
        cases_hist = [historical_data["cases"][d] for d in dates]
        recovered_hist = [historical_data["recovered"][d] for d in dates]
        deaths_hist = [historical_data["deaths"][d] for d in dates]

        active_hist = [cases_hist[i] - (recovered_hist[i] + deaths_hist[i]) for i in range(len(cases_hist))]
        active_hist = [max(0, x) for x in active_hist] 

        new_cases_hist = [cases_hist[i] - cases_hist[i-1] if i > 0 else 0 for i in range(len(cases_hist))]
        new_deaths_hist = [deaths_hist[i] - deaths_hist[i-1] if i > 0 else 0 for i in range(len(deaths_hist))]
        new_cases_hist = [max(0, x) for x in new_cases_hist]
        new_deaths_hist = [max(0, x) for x in new_deaths_hist]

        date_objects_all = [datetime.strptime(d, "%m/%d/%y") for d in dates]
       
        total_months = (date(2024, 8, 1) - date(2020, 1, 1)).days // 30
        label_interval = max(1, len(dates) // (total_months // 6)) 
        date_objects_sampled = date_objects_all[::label_interval]
        sampled_dates = dates[::label_interval]
        formatted_dates = [datetime.strptime(d, "%m/%d/%y").strftime("%b %Y") for d in sampled_dates]

        last_date = dates[-1]
        last_date_obj = datetime.strptime(last_date, "%m/%d/%y")
        if last_date_obj not in date_objects_sampled:
            date_objects_sampled.append(last_date_obj)
            formatted_dates.append(last_date_obj.strftime("%b %Y"))

        cases_all = cases_hist
        recovered_all = recovered_hist
        deaths_all = deaths_hist
        active_all = active_hist
        new_cases_all = new_cases_hist
        new_deaths_all = new_deaths_hist

        cases_data = cases_all
        recovered_data = recovered_all
        deaths_data = deaths_all
        active_data = active_all
        new_cases_data = new_cases_all
        new_deaths_data = new_deaths_all
        date_objects_data = date_objects_all

        # Convert dates to numerical values for easier distance calculation
        date_nums = np.array([mdates.date2num(d) for d in date_objects_data])

        compare_cases_hist = None
        if compare_country_data and compare_country_entry.get().strip():
            compare_cases_hist = []
            for d in dates:
                if d in compare_country_data["historical_cases"]:
                    compare_cases_hist.append(compare_country_data["historical_cases"][d])
                else:
                    compare_cases_hist.append(0)
   
            if len(compare_cases_hist) == len(dates):
                compare_cases_hist = compare_cases_hist
            else:
                compare_cases_hist = None
                print(f"Warning: Comparison data length mismatch for {compare_country_entry.get()}")

        for widget in graph_frame.winfo_children():
            widget.destroy()

        plt.style.use('ggplot')
        sns.set_palette("muted")
        plots = []

        # Plot 1: Bar Chart (Cumulative Totals) with Hover Effect
        fig1, ax1 = plt.subplots(figsize=(6, 5))
        bars = ax1.bar(['Cases', 'Recovered', 'Deaths', 'Active'], 
                       [confirmed, recovered, deaths, active], 
                       color=['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e'], 
                       width=0.6, edgecolor='black', label=['Cases', 'Recovered', 'Deaths', 'Active'])
        ax1.set_title(f"Cumulative Totals - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax1.set_ylabel("Count", fontsize=16)
        ax1.tick_params(axis='x', labelsize=14)
        ax1.tick_params(axis='y', labelsize=14)
        ax1.grid(True, axis='y', linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax1.set_facecolor('#f9f9f9')
        fig1.patch.set_facecolor('#f9f9f9')
        ax1.legend(fontsize=12, frameon=True, shadow=True, loc='upper right')

        # Hover effect for bar chart
        original_colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e']
        highlight_colors = ['#4a90e2', '#4cd964', '#ff4c4c', '#ffa500']
        annot1 = ax1.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot1.set_visible(False)

        def update_annot1(bar, value):
            x = bar.get_x() + bar.get_width() / 2.
            y = bar.get_height()
            annot1.xy = (x, y)
            text = f"{format_indian_number(value, None)}"
            annot1.set_text(text)
            annot1.get_bbox_patch().set_alpha(0.8)
            annot1.set_visible(True)

        def hover1(event):
            vis = annot1.get_visible()
            if event.inaxes == ax1:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        bar.set_color(highlight_colors[i])
                        update_annot1(bar, bar.get_height())
                        fig1.canvas.draw_idle()
                        return
            for i, bar in enumerate(bars):
                bar.set_color(original_colors[i])
            if vis:
                annot1.set_visible(False)
                fig1.canvas.draw_idle()

        fig1.canvas.mpl_connect("motion_notify_event", hover1)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig1, master=graph_frame).get_tk_widget())
        plt.close(fig1)

        # Plot 2: Line Plot (Cases Over Time) with Fixed Hover Effect
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        line, = ax2.plot(date_objects_data, cases_data, label="Cases", color='#1f77b4', marker='o', markersize=4, linewidth=2.5)
        ax2.set_title(f"Total Cases Over Time - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax2.set_ylabel("Cases", fontsize=16)
        ax2.tick_params(axis='x', rotation=45, labelsize=12)
        ax2.tick_params(axis='y', labelsize=14)
        ax2.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax2.legend(fontsize=14, frameon=True, shadow=True)
        ax2.set_xticks(date_objects_sampled)
        ax2.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax2.set_facecolor('#f9f9f9')
        fig2.patch.set_facecolor('#f9f9f9')

        # Fixed hover effect for line plot
        annot2 = ax2.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot2.set_visible(False)

        def update_annot2(x, y, value):
            annot2.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\nCases: {format_indian_number(value, None)}"
            annot2.set_text(text)
            annot2.get_bbox_patch().set_alpha(0.8)
            annot2.set_visible(True)

        def hover2(event):
            vis = annot2.get_visible()
            if event.inaxes == ax2:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    # x is in Matplotlib date format (float), compare directly with date_nums
                    idx = np.argmin(np.abs(date_nums - x))
                    x_data = date_objects_data[idx]
                    y_data = cases_data[idx]
                    # Transform y-data to axes coordinates to calculate distance
                    y_data_ax = ax2.transData.transform((0, y_data))[1]
                    y_mouse_ax = ax2.transData.transform((0, y))[1]
                    if abs(y_data_ax - y_mouse_ax) < 20:  # Sensitivity: 20 pixels in y-direction
                        update_annot2(x_data, y_data, y_data)
                        fig2.canvas.draw_idle()
                        return
            if vis:
                annot2.set_visible(False)
                fig2.canvas.draw_idle()

        fig2.canvas.mpl_connect("motion_notify_event", hover2)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig2, master=graph_frame).get_tk_widget())
        plt.close(fig2)

        # Plot 3: Line Plot (Deaths Over Time) with Fixed Hover Effect
        fig3, ax3 = plt.subplots(figsize=(6, 5))
        line, = ax3.plot(date_objects_data, deaths_data, label="Deaths", color='#d62728', marker='o', markersize=4, linewidth=2.5)
        ax3.set_title(f"Total Deaths Cases Over Time - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax3.set_ylabel("Deaths", fontsize=16)
        ax3.tick_params(axis='x', rotation=45, labelsize=12)
        ax3.tick_params(axis='y', labelsize=14)
        ax3.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax3.legend(fontsize=14, frameon=True, shadow=True)
        ax3.set_xticks(date_objects_sampled)
        ax3.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax3.set_facecolor('#f9f9f9')
        fig3.patch.set_facecolor('#f9f9f9')

        # Fixed hover effect for line plot
        annot3 = ax3.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot3.set_visible(False)

        def update_annot3(x, y, value):
            annot3.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\nDeaths: {format_indian_number(value, None)}"
            annot3.set_text(text)
            annot3.get_bbox_patch().set_alpha(0.8)
            annot3.set_visible(True)

        def hover3(event):
            vis = annot3.get_visible()
            if event.inaxes == ax3:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.argmin(np.abs(date_nums - x))
                    x_data = date_objects_data[idx]
                    y_data = deaths_data[idx]
                    y_data_ax = ax3.transData.transform((0, y_data))[1]
                    y_mouse_ax = ax3.transData.transform((0, y))[1]
                    if abs(y_data_ax - y_mouse_ax) < 20:
                        update_annot3(x_data, y_data, y_data)
                        fig3.canvas.draw_idle()
                        return
            if vis:
                annot3.set_visible(False)
                fig3.canvas.draw_idle()

        fig3.canvas.mpl_connect("motion_notify_event", hover3)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig3, master=graph_frame).get_tk_widget())
        plt.close(fig3)

        # Plot 4: Line Plot (Recovered Over Time) with Fixed Hover Effect
        fig4, ax4 = plt.subplots(figsize=(6, 5))
        line, = ax4.plot(date_objects_data, recovered_data, label="Recovered", color='#2ca02c', marker='o', markersize=4, linewidth=2.5)
        ax4.set_title(f"Total Recovered Cases Over Time - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax4.set_ylabel("Recovered", fontsize=16)
        ax4.tick_params(axis='x', rotation=45, labelsize=12)
        ax4.tick_params(axis='y', labelsize=14)
        ax4.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax4.legend(fontsize=14, frameon=True, shadow=True)
        ax4.set_xticks(date_objects_sampled)
        ax4.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax4.set_facecolor('#f9f9f9')
        fig4.patch.set_facecolor('#f9f9f9')

        # Fixed hover effect for line plot
        annot4 = ax4.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot4.set_visible(False)

        def update_annot4(x, y, value):
            annot4.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\nRecovered: {format_indian_number(value, None)}"
            annot4.set_text(text)
            annot4.get_bbox_patch().set_alpha(0.8)
            annot4.set_visible(True)

        def hover4(event):
            vis = annot4.get_visible()
            if event.inaxes == ax4:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.argmin(np.abs(date_nums - x))
                    x_data = date_objects_data[idx]
                    y_data = recovered_data[idx]
                    y_data_ax = ax4.transData.transform((0, y_data))[1]
                    y_mouse_ax = ax4.transData.transform((0, y))[1]
                    if abs(y_data_ax - y_mouse_ax) < 20:
                        update_annot4(x_data, y_data, y_data)
                        fig4.canvas.draw_idle()
                        return
            if vis:
                annot4.set_visible(False)
                fig4.canvas.draw_idle()

        fig4.canvas.mpl_connect("motion_notify_event", hover4)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig4, master=graph_frame).get_tk_widget())
        plt.close(fig4)

        # Plot 5: Line Plot (Active Cases Over Time) with Fixed Hover Effect
        fig5, ax5 = plt.subplots(figsize=(6, 5))
        line, = ax5.plot(date_objects_data, active_data, label="Active Cases", color='#ff7f0e', marker='o', markersize=4, linewidth=2.5)
        ax5.set_title(f"Total Active Cases Over Time - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax5.set_ylabel("Active Cases", fontsize=16)
        ax5.tick_params(axis='x', rotation=45, labelsize=12)
        ax5.tick_params(axis='y', labelsize=14)
        ax5.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax5.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax5.legend(fontsize=14, frameon=True, shadow=True)
        ax5.set_xticks(date_objects_sampled)
        ax5.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax5.set_facecolor('#f9f9f9')
        fig5.patch.set_facecolor('#f9f9f9')

        # Fixed hover effect for line plot
        annot5 = ax5.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot5.set_visible(False)

        def update_annot5(x, y, value):
            annot5.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\nActive: {format_indian_number(value, None)}"
            annot5.set_text(text)
            annot5.get_bbox_patch().set_alpha(0.8)
            annot5.set_visible(True)

        def hover5(event):
            vis = annot5.get_visible()
            if event.inaxes == ax5:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.argmin(np.abs(date_nums - x))
                    x_data = date_objects_data[idx]
                    y_data = active_data[idx]
                    y_data_ax = ax5.transData.transform((0, y_data))[1]
                    y_mouse_ax = ax5.transData.transform((0, y))[1]
                    if abs(y_data_ax - y_mouse_ax) < 20:
                        update_annot5(x_data, y_data, y_data)
                        fig5.canvas.draw_idle()
                        return
            if vis:
                annot5.set_visible(False)
                fig5.canvas.draw_idle()

        fig5.canvas.mpl_connect("motion_notify_event", hover5)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig5, master=graph_frame).get_tk_widget())
        plt.close(fig5)

        # Plot 6: Line Plot (New Cases Over Time) with Fixed Hover Effect
        fig6, ax6 = plt.subplots(figsize=(6, 5))
        line, = ax6.plot(date_objects_data, new_cases_data, label="New Cases", color='#9467bd', marker='o', markersize=4, linewidth=2.5)
        ax6.set_title(f"New Cases Over Time - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax6.set_ylabel("New Cases", fontsize=16)
        ax6.tick_params(axis='x', rotation=45, labelsize=12)
        ax6.tick_params(axis='y', labelsize=14)
        ax6.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax6.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax6.legend(fontsize=14, frameon=True, shadow=True)
        ax6.set_xticks(date_objects_sampled)
        ax6.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax6.set_facecolor('#f9f9f9')
        fig6.patch.set_facecolor('#f9f9f9')

        # Fixed hover effect for line plot
        annot6 = ax6.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot6.set_visible(False)

        def update_annot6(x, y, value):
            annot6.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\nNew Cases: {format_indian_number(value, None)}"
            annot6.set_text(text)
            annot6.get_bbox_patch().set_alpha(0.8)
            annot6.set_visible(True)

        def hover6(event):
            vis = annot6.get_visible()
            if event.inaxes == ax6:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.argmin(np.abs(date_nums - x))
                    x_data = date_objects_data[idx]
                    y_data = new_cases_data[idx]
                    y_data_ax = ax6.transData.transform((0, y_data))[1]
                    y_mouse_ax = ax6.transData.transform((0, y))[1]
                    if abs(y_data_ax - y_mouse_ax) < 20:
                        update_annot6(x_data, y_data, y_data)
                        fig6.canvas.draw_idle()
                        return
            if vis:
                annot6.set_visible(False)
                fig6.canvas.draw_idle()

        fig6.canvas.mpl_connect("motion_notify_event", hover6)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig6, master=graph_frame).get_tk_widget())
        plt.close(fig6)

        # Plot 7: Line Plot (New Deaths Over Time) with Fixed Hover Effect
        fig7, ax7 = plt.subplots(figsize=(6, 5))
        line, = ax7.plot(date_objects_data, new_deaths_data, label="New Deaths", color='#8c564b', marker='o', markersize=4, linewidth=2.5)
        ax7.set_title(f"New Deaths Over Time - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax7.set_ylabel("New Deaths", fontsize=16)
        ax7.tick_params(axis='x', rotation=45, labelsize=12)
        ax7.tick_params(axis='y', labelsize=14)
        ax7.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax7.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax7.legend(fontsize=14, frameon=True, shadow=True)
        ax7.set_xticks(date_objects_sampled)
        ax7.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax7.set_facecolor('#f9f9f9')
        fig7.patch.set_facecolor('#f9f9f9')

        # Fixed hover effect for line plot
        annot7 = ax7.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot7.set_visible(False)

        def update_annot7(x, y, value):
            annot7.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\nNew Deaths: {format_indian_number(value, None)}"
            annot7.set_text(text)
            annot7.get_bbox_patch().set_alpha(0.8)
            annot7.set_visible(True)

        def hover7(event):
            vis = annot7.get_visible()
            if event.inaxes == ax7:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.argmin(np.abs(date_nums - x))
                    x_data = date_objects_data[idx]
                    y_data = new_deaths_data[idx]
                    y_data_ax = ax7.transData.transform((0, y_data))[1]
                    y_mouse_ax = ax7.transData.transform((0, y))[1]
                    if abs(y_data_ax - y_mouse_ax) < 20:
                        update_annot7(x_data, y_data, y_data)
                        fig7.canvas.draw_idle()
                        return
            if vis:
                annot7.set_visible(False)
                fig7.canvas.draw_idle()

        fig7.canvas.mpl_connect("motion_notify_event", hover7)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig7, master=graph_frame).get_tk_widget())
        plt.close(fig7)

        # Plot 8: Pie Chart (Case Distribution) with Hover Effect
        fig8, ax8 = plt.subplots(figsize=(6, 5))
        labels = ['Recovered', 'Active', 'Deaths']
        sizes = [recovered, active, deaths]
        colors = ['#2ca02c', '#ff7f0e', '#d62728']
        explode = (0.05, 0.05, 0.05)
        wedges, texts = ax8.pie(sizes, labels=None, colors=colors, autopct=None, startangle=90, explode=explode, shadow=True, 
                                textprops={'fontsize': 12}, pctdistance=0.85, labeldistance=1.1)
        ax8.set_title(f"Case Distribution - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        fig8.patch.set_facecolor('#f9f9f9')

        # Hover effect for pie chart
        annot8 = ax8.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot8.set_visible(False)

        def update_annot8(wedge, label, value):
            x, y = wedge.center
            annot8.xy = (x, y)
            text = f"{label}: {format_indian_number(value, None)}"
            annot8.set_text(text)
            annot8.get_bbox_patch().set_alpha(0.8)
            annot8.set_visible(True)

        def hover8(event):
            vis = annot8.get_visible()
            if event.inaxes == ax8:
                for i, wedge in enumerate(wedges):
                    cont, _ = wedge.contains(event)
                    if cont:
                        update_annot8(wedge, labels[i], sizes[i])
                        fig8.canvas.draw_idle()
                        return
            if vis:
                annot8.set_visible(False)
                fig8.canvas.draw_idle()

        fig8.canvas.mpl_connect("motion_notify_event", hover8)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig8, master=graph_frame).get_tk_widget())
        plt.close(fig8)

        total = sum(sizes)
        legend_labels = [f"{label} ({size/total*100:.1f}%)" for label, size in zip(labels, sizes)]
        ax8.legend(legend_labels, loc='upper right', bbox_to_anchor=(1.2, 1), fontsize=12, frameon=True)

        # Plot 9: Stack Plot (Cumulative Trends) with Hover Effect
        fig9, ax9 = plt.subplots(figsize=(6, 5))
        stack = ax9.stackplot(date_objects_data, recovered_data, deaths_data, active_data, 
                              labels=['Recovered', 'Deaths', 'Active'], 
                              colors=['#2ca02c', '#d62728', '#ff7f0e'], alpha=0.8)
        ax9.set_title(f"Cumulative Trends - {country.capitalize()}", fontsize=16, weight='bold', pad=10)
        ax9.set_ylabel("Count", fontsize=16)
        ax9.tick_params(axis='x', rotation=45, labelsize=12)
        ax9.tick_params(axis='y', labelsize=14)
        ax9.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
        ax9.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
        ax9.legend(loc='upper left', fontsize=14, frameon=True, shadow=True)
        ax9.set_xticks(date_objects_sampled)
        ax9.set_xticklabels(formatted_dates, rotation=45, ha='right')
        ax9.set_facecolor('#f9f9f9')
        fig9.patch.set_facecolor('#f9f9f9')

        # Hover effect for stack plot
        annot9 = ax9.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                              arrowprops=dict(arrowstyle="->"))
        annot9.set_visible(False)

        def update_annot9(x, y, label, value):
            annot9.xy = (x, y)
            text = f"Date: {x.strftime('%Y-%m-%d')}\n{label}: {format_indian_number(value, None)}"
            annot9.set_text(text)
            annot9.get_bbox_patch().set_alpha(0.8)
            annot9.set_visible(True)

        def hover9(event):
            vis = annot9.get_visible()
            if event.inaxes == ax9:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.argmin(np.abs(date_nums - x))
                    x_val = date_objects_data[idx]
                    y_vals = [recovered_data[idx], deaths_data[idx], active_data[idx]]
                    labels = ['Recovered', 'Deaths', 'Active']
                    cumulative_y = 0
                    for i, (y_val, label) in enumerate(zip(y_vals, labels)):
                        cumulative_y += y_val
                        if y <= cumulative_y:
                            update_annot9(x_val, cumulative_y, label, y_val)
                            fig9.canvas.draw_idle()
                            return
            if vis:
                annot9.set_visible(False)
                fig9.canvas.draw_idle()

        fig9.canvas.mpl_connect("motion_notify_event", hover9)

        plt.tight_layout()
        plots.append(FigureCanvasTkAgg(fig9, master=graph_frame).get_tk_widget())
        plt.close(fig9)

        # Plot 10: Line Plot (Case Comparison) with Fixed Hover Effect
        if compare_cases_hist:
            fig10, ax10 = plt.subplots(figsize=(6, 5))
            line1, = ax10.plot(date_objects_data, cases_data, label=f"{country.capitalize()} Cases", 
                              color='#1f77b4', marker='o', markersize=4, linewidth=2.5)
            line2, = ax10.plot(date_objects_data, compare_cases_hist, 
                              label=f"{compare_country_entry.get().capitalize()} Cases", 
                              color='#ff7f0e', marker='s', markersize=4, linewidth=2.5)
            ax10.set_title(f"Case Comparison", fontsize=16, weight='bold', pad=10)
            ax10.set_ylabel("Cases", fontsize=16)
            ax10.tick_params(axis='x', rotation=45, labelsize=12)
            ax10.tick_params(axis='y', labelsize=14)
            ax10.grid(True, linestyle='--', alpha=0.5, color='gray', linewidth=1, which='both')
            ax10.yaxis.set_major_formatter(plt.FuncFormatter(format_indian_number))
            ax10.legend(fontsize=14, frameon=True, shadow=True)
            ax10.set_xticks(date_objects_sampled)
            ax10.set_xticklabels(formatted_dates, rotation=45, ha='right')
            ax10.set_facecolor('#f9f9f9')
            fig10.patch.set_facecolor('#f9f9f9')

            # Fixed hover effect for comparison line plot
            annot10 = ax10.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
                                    arrowprops=dict(arrowstyle="->"))
            annot10.set_visible(False)

            def update_annot10(x, y, label, value):
                annot10.xy = (x, y)
                text = f"Date: {x.strftime('%Y-%m-%d')}\n{label}: {format_indian_number(value, None)}"
                annot10.set_text(text)
                annot10.get_bbox_patch().set_alpha(0.8)
                annot10.set_visible(True)

            def hover10(event):
                vis = annot10.get_visible()
                if event.inaxes == ax10:
                    x, y = event.xdata, event.ydata
                    if x is not None and y is not None:
                        idx = np.argmin(np.abs(date_nums - x))
                        x_data = date_objects_data[idx]
                        y1_data = cases_data[idx]
                        y2_data = compare_cases_hist[idx]
                        y1_data_ax = ax10.transData.transform((0, y1_data))[1]
                        y2_data_ax = ax10.transData.transform((0, y2_data))[1]
                        y_mouse_ax = ax10.transData.transform((0, y))[1]
                        dist_y1 = abs(y1_data_ax - y_mouse_ax)
                        dist_y2 = abs(y2_data_ax - y_mouse_ax)
                        if dist_y1 < 20 and dist_y1 <= dist_y2:
                            update_annot10(x_data, y1_data, f"{country.capitalize()} Cases", y1_data)
                            fig10.canvas.draw_idle()
                            return
                        elif dist_y2 < 20 and dist_y2 <= dist_y1:
                            update_annot10(x_data, y2_data, f"{compare_country_entry.get().capitalize()} Cases", y2_data)
                            fig10.canvas.draw_idle()
                            return
                if vis:
                    annot10.set_visible(False)
                    fig10.canvas.draw_idle()

            fig10.canvas.mpl_connect("motion_notify_event", hover10)

            plt.tight_layout()
            plots.append(FigureCanvasTkAgg(fig10, master=graph_frame).get_tk_widget())
            plt.close(fig10)

        for idx, widget in enumerate(plots):
            row = idx // 2
            col = idx % 2
            widget.grid(row=row, column=col, padx=25, pady=25, sticky="nsew")

        for i in range(2):
            graph_frame.columnconfigure(i, weight=1)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to plot graphs: {str(e)}")

def generate_summary_report():
    try:
        if not country_data or not historical_data:
            raise ValueError("No data available to generate report. Fetch data first!")

        country = (country_entry.get().strip() or country_dropdown.get().strip()).capitalize()
        summary = f"### COVID-19 Summary Report for {country}\n\n"
        summary += f"**Last Updated:** {country_data['last_date']}\n\n"
        summary += f"**Confirmed Cases:** {country_data['cases']:,}\n"
        summary += f"**Active Cases:** {country_data['active']:,}\n"
        summary += f"**Recovered:** {country_data['recovered']:,}\n"
        summary += f"**Deaths:** {country_data['deaths']:,}\n\n"
        summary += "**Historical Trends Overview:**\n"
        summary += f"- Total cases increased from {min(historical_data['cases'].values()):,} to {max(historical_data['cases'].values()):,}\n"
        summary += f"- Total deaths increased from {min(historical_data['deaths'].values()):,} to {max(historical_data['deaths'].values()):,}\n"
        summary += f"- Recovered cases peaked at {max(historical_data['recovered'].values()):,}\n"

        summary_window = tk.Toplevel(root)
        summary_window.title(f"{country} COVID-19 Summary")
        summary_window.geometry("500x400")
        summary_text = scrolledtext.ScrolledText(summary_window, width=60, height=20, font=("Inter", 12))
        summary_text.insert(tk.END, summary)
        summary_text.pack(padx=15, pady=15)
        ttk.Button(summary_window, text="Close", command=summary_window.destroy, style="TButton").pack(pady=10)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate summary report: {str(e)}")

style = ttk.Style()
style.theme_use('clam')

style.configure("TLabel", font=("Inter", 14), background="#ffffff", foreground="#212529")
style.configure("TButton", font=("Inter", 12, "bold"), padding=12, background="#28a745", foreground="#ffffff", borderwidth=0)
style.map("TButton", 
          background=[('active', '#218838'), ('!disabled', '#28a745')],
          foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')])
style.configure("TEntry", font=("Inter", 14), padding=10, fieldbackground="#ffffff", foreground="#212529")
style.configure("TCombobox", font=("Inter", 14), padding=10, fieldbackground="#ffffff", foreground="#212529")
style.map("TCombobox",
          fieldbackground=[('readonly', '#ffffff')],
          selectbackground=[('readonly', '#ffffff')],
          selectforeground=[('readonly', '#212529')])
style.configure("TFrame", background="#e9ecef")
style.configure("TCheckbutton", font=("Inter", 12), background="#ffffff", foreground="#212529")
style.configure("Card.TFrame", background="#ffffff", relief="raised", borderwidth=2)
style.configure("Custom.TLabelframe", background="#ffffff", relief="flat", font=("Inter", 16, "bold"), foreground="#212529")
style.configure("Header.TLabel", font=("Inter", 28, "bold"), foreground="#28a745", background="#e9ecef")
style.configure("Info.TLabel", font=("Inter", 12), foreground="#6c757d", background="#tracks")
style.configure("TScrollbar", troughcolor="#e9ecef", background="#28a745", arrowcolor="#ffffff")
style.configure("Small.TLabel", font=("Inter", 12), background="#ffffff", foreground="#212529")
style.configure("Small.TButton", font=("Inter", 10, "bold"), padding=8, background="#28a745", foreground="#ffffff", borderwidth=0)
style.map("Small.TButton", 
          background=[('active', '#218838'), ('!disabled', '#28a745')],
          foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')])
style.configure("Small.TEntry", font=("Inter", 12), padding=8, fieldbackground="#ffffff", foreground="#212529")
style.configure("Small.TCombobox", font=("Inter", 12), padding=8, fieldbackground="#ffffff", foreground="#212529")
style.map("Small.TCombobox",
          fieldbackground=[('readonly', '#ffffff')],
          selectbackground=[('readonly', '#ffffff')],
          selectforeground=[('readonly', '#212529')])

header_frame = ttk.Frame(scrollable_frame, style="Card.TFrame", padding="25")
header_frame.pack(fill="x", padx=50, pady=(30, 15), anchor="center")
ttk.Label(header_frame, text="🦠 COVID-19 Data Tracker Dashboard", style="Header.TLabel").pack(anchor="center")

input_frame = ttk.Frame(scrollable_frame, style="Card.TFrame", padding="15")
input_frame.pack(fill="x", padx=50, pady=15, anchor="center")
input_frame.configure(relief="raised", borderwidth=2)

input_inner_frame = ttk.Frame(input_frame, style="Card.TFrame")
input_inner_frame.pack(anchor="center")
ttk.Label(input_inner_frame, text="Select Country:", style="Small.TLabel").grid(row=0, column=0, padx=10, pady=10, sticky="w")
country_dropdown = ttk.Combobox(input_inner_frame, values=["USA", "India", "Brazil", "France", "Germany"], state="readonly", width=15, style="Small.TCombobox")
country_dropdown.grid(row=0, column=1, padx=10, pady=10)
country_dropdown.set("USA")
ttk.Label(input_inner_frame, text="Or Search Other Countries:", style="Small.TLabel").grid(row=0, column=2, padx=10, pady=10, sticky="w")
country_entry = ttk.Entry(input_inner_frame, width=20, style="Small.TEntry")
country_entry.grid(row=0, column=3, padx=10, pady=10)
ttk.Button(input_inner_frame, text="Fetch Data", command=fetch_data, style="Small.TButton").grid(row=0, column=4, padx=10, pady=10)
ttk.Button(input_inner_frame, text="Plot Graphs", command=plot_graphs, style="Small.TButton").grid(row=0, column=5, padx=10, pady=10)
ttk.Button(input_inner_frame, text="Export to CSV", command=export_to_csv, style="Small.TButton").grid(row=0, column=6, padx=10, pady=10)
ttk.Button(input_inner_frame, text="Generate Summary", command=generate_summary_report, style="Small.TButton").grid(row=0, column=7, padx=10, pady=10)

ttk.Label(input_inner_frame, text="Compare Country:", style="Small.TLabel").grid(row=1, column=0, padx=10, pady=10, sticky="w")
compare_country_entry = ttk.Entry(input_inner_frame, width=20, style="Small.TEntry")
compare_country_entry.grid(row=1, column=1, padx=10, pady=10, columnspan=2)
ttk.Button(input_inner_frame, text="Fetch Compare Data", command=fetch_compare_data, style="Small.TButton").grid(row=1, column=3, padx=10, pady=10, columnspan=5, sticky="w")

info_frame = ttk.LabelFrame(scrollable_frame, text="Global & Country Statistics", style="Custom.TLabelframe", padding="20")
info_frame.pack(fill="x", padx=50, pady=15, anchor="center")
info_frame.configure(relief="raised", borderwidth=2)

info_inner_frame = ttk.Frame(info_frame, style="Card.TFrame")
info_inner_frame.pack(anchor="center")
active_label = ttk.Label(info_inner_frame, text="Active Cases: N/A", style="TLabel")
active_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
confirmed_label = ttk.Label(info_inner_frame, text="Confirmed Cases: N/A", style="TLabel")
confirmed_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")
recovered_label = ttk.Label(info_inner_frame, text="Recovered: N/A", style="TLabel")
recovered_label.grid(row=0, column=2, padx=20, pady=10, sticky="w")
deaths_label = ttk.Label(info_inner_frame, text="Deaths: N/A", style="TLabel")
deaths_label.grid(row=0, column=3, padx=20, pady=10, sticky="w")
style.configure("Debug.TLabel", font=("Inter", 14), foreground="#6c757d", background="#e9ecef")
last_update_label = ttk.Label(info_inner_frame, text="Last Updated: N/A", style="Debug.TLabel")
last_update_label.grid(row=1, column=0, columnspan=4, pady=10)

country_info = scrolledtext.ScrolledText(info_inner_frame, width=100, height=7, font=("Inter", 12), bg="#ffffff", relief="flat", borderwidth=1)
country_info.grid(row=2, column=0, columnspan=4, pady=15, padx=20)

compare_info = scrolledtext.ScrolledText(info_inner_frame, width=100, height=7, font=("Inter", 12), bg="#ffffff", relief="flat", borderwidth=1)
compare_info.grid(row=3, column=0, columnspan=4, pady=15, padx=20)

live_data_frame = ttk.LabelFrame(scrollable_frame, text="Live COVID-19 Data", style="Custom.TLabelframe", padding="20")
live_data_frame.pack(fill="x", padx=50, pady=15, anchor="center")
live_data_frame.configure(relief="raised", borderwidth=2)

live_inner_frame = ttk.Frame(live_data_frame, style="Card.TFrame")
live_inner_frame.pack(anchor="center")
live_world_label = ttk.Label(live_inner_frame, text="World - Live Data: N/A", wraplength=800, style="TLabel")
live_world_label.pack(anchor="center", padx=15, pady=10)
live_india_label = ttk.Label(live_inner_frame, text="India - Live Data: N/A", wraplength=800, style="TLabel")
live_india_label.pack(anchor="center", padx=15, pady=10)
ttk.Button(live_inner_frame, text="Fetch Live Data", command=fetch_live_covid_data, style="TButton").pack(anchor="center", padx=15, pady=15)

style.configure("Footer.TLabel", font=("Inter", 14), foreground="#6c757d", background="#ffffff")

graph_frame = ttk.Frame(scrollable_frame, style="Card.TFrame", padding="20")
graph_frame.pack(fill="both", expand=True, padx=0, pady=0, anchor="center")
graph_frame.configure(relief="raised", borderwidth=2)

footer_frame = ttk.Frame(scrollable_frame, style="Card.TFrame", padding="20")
footer_frame.pack(fill="x", padx=10, pady=10, anchor="center")
footer_inner_frame = ttk.Frame(footer_frame, style="Card.TFrame")
footer_inner_frame.pack(anchor="center")
ttk.Label(footer_inner_frame, text="📅 Statistics according to 2020-2024 data", style="Footer.TLabel").pack(side="left", padx=20)
ttk.Label(footer_inner_frame, text="🌐 Source: Our World in Data", style="Footer.TLabel").pack(side="right", padx=20)

ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=0, padx=0)

def on_window_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_window_close)

fetch_data()

root.mainloop()