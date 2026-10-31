import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Dashboard Bike Sharing", layout="wide")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def load_data():
    day = pd.read_csv(DATA_DIR / "day.csv", parse_dates=["dteday"])
    hour = pd.read_csv(DATA_DIR / "hour.csv", parse_dates=["dteday"])

    weather_map = {1: "Clear", 2: "Mist/Cloudy", 3: "Light Rain/Snow", 4: "Heavy Rain/Snow"}
    day["weather_label"] = day["weathersit"].map(weather_map)
    return day, hour


day_df, hour_df = load_data()

st.sidebar.header("Filter")
min_date = day_df["dteday"].min().date()
max_date = day_df["dteday"].max().date()
rentang = st.sidebar.date_input(
    "Rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

if len(rentang) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir di sidebar.")
    st.stop()

start, end = pd.to_datetime(rentang[0]), pd.to_datetime(rentang[1])
day_f = day_df[day_df["dteday"].between(start, end)]
hour_f = hour_df[hour_df["dteday"].between(start, end)]

st.title("Dashboard Bike Sharing")
st.caption("Sistem Capital Bikeshare, Washington DC (Januari 2011 sampai Desember 2012)")

st.header("Jam puncak penyewaan di hari kerja")

kerja = hour_f[hour_f["workingday"] == 1]

if kerja.empty:
    st.warning("Tidak ada hari kerja pada rentang tanggal yang dipilih.")
else:
    pola_jam = kerja.groupby("hr")["cnt"].mean()
    top3 = pola_jam.nlargest(3)

    kolom = st.columns(3)
    for k, (urutan, (jam, nilai)) in zip(kolom, enumerate(top3.items(), start=1)):
        k.metric(f"Puncak ke-{urutan}: jam {jam}", f"{nilai:,.0f} penyewaan")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pola_jam.index, pola_jam.values, marker="o", color="steelblue")
    ax.scatter(top3.index, top3.values, color="red", s=80, zorder=3, label="3 jam puncak")
    ax.set_xticks(range(24))
    ax.set_xlabel("Jam")
    ax.set_ylabel("Rata-rata penyewaan")
    ax.set_title("Rata-rata penyewaan per jam pada hari kerja")
    ax.legend()
    st.pyplot(fig)

st.header("Dampak cuaca terhadap penyewaan harian")

urut = ["Clear", "Mist/Cloudy", "Light Rain/Snow"]
warna = {"Clear": "#4c9f70", "Mist/Cloudy": "#e0a43a", "Light Rain/Snow": "#c0504d"}

rata = day_f.groupby("weather_label")["cnt"].agg(["count", "mean"]).reindex(urut).dropna()

if {"Clear", "Light Rain/Snow"}.issubset(rata.index):
    turun = (rata.loc["Light Rain/Snow", "mean"] / rata.loc["Clear", "mean"] - 1) * 100
    st.metric("Selisih rata-rata penyewaan harian (hujan/salju ringan vs cerah)", f"{turun:.1f}%")
else:
    st.info("Rentang tanggal ini tidak memuat hari cerah dan hujan/salju ringan sekaligus.")

if not rata.empty:
    label = [f"{k}\n({int(rata.loc[k, 'count'])} hari)" for k in rata.index]
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    bars = ax2.bar(label, rata["mean"], color=[warna[k] for k in rata.index])
    ax2.bar_label(bars, fmt="%.0f", padding=3)
    ax2.set_ylabel("Rata-rata penyewaan harian")
    ax2.set_title("Rata-rata penyewaan harian menurut cuaca")
    st.pyplot(fig2)