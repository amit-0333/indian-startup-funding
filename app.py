import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Page config 
st.set_page_config(
    page_title="Indian Startup Funding",
    page_icon="",
    layout="wide"
)

# Custom CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; background:#0e1117; }

h1,h2,h3 { font-family:'Syne',sans-serif !important; }

div[data-testid="stMetric"] {
    background: #1a1d2e;
    border: 1px solid #2a2d3e;
    border-radius: 10px;
    padding: 1rem 1.2rem;
}
div[data-testid="stMetric"] label { color:#9ca3af !important; font-size:.8rem !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family:'Syne',sans-serif !important;
    color:#f0f4ff !important;
    font-size:1.6rem !important;
}
section[data-testid="stSidebar"] { background:#10121f; border-right:1px solid #1e2133; }
.block-container { padding-top:1.5rem; }
</style>
""", unsafe_allow_html=True)

#  Load data 
@st.cache_data
def load_data():
    df = pd.read_csv("startupFundingCleaned.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["startup"]    = df["startup"].str.replace(r"\\xe2\\x80\\x99", "'", regex=True)
    df["startup"]    = df["startup"].str.replace("Ola Cabs", "Ola")
    df["startup"]    = df["startup"].str.replace("Byju's", "BYJU'S")
    df["investors"]  = df["investors"].fillna("Undisclosed")
    df["industry"]   = df["industry"].fillna("Other")
    df["city"]       = df["city"].fillna("Unknown")
    df["investment_type"] = df["investment_type"].fillna("Undisclosed")
    df["amount_inr_crore"] = pd.to_numeric(df.get("amount_inr_crore", df.get("amount", 0)), errors="coerce").fillna(0)
    df["year"]       = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    return df

df = load_data()

#  Helpers 
DARK_BG   = "#0e1117"
CARD_BG   = "#1a1d2e"
ACCENT    = "#6366f1"
TEXT      = "#f0f4ff"
MUTED     = "#6b7280"
COLORS    = ["#6366f1","#22d3ee","#f59e0b","#10b981","#f43f5e","#a78bfa","#fb923c","#34d399"]

def style_fig(fig, ax_list=None):
    fig.patch.set_facecolor(DARK_BG)
    axes = ax_list if ax_list else [fig.gca()]
    for ax in axes:
        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.xaxis.label.set_color(MUTED)
        ax.yaxis.label.set_color(MUTED)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2a2d3e")
        ax.title.set_color(TEXT)
    return fig

def investors_exploded():
    return df["investors"].str.split(",").explode().str.strip().dropna()



# SECTION 1 — OVERALL ANALYSIS


def show_overall():
    st.title("Overall Analysis")

    total_funding = df["amount_inr_crore"].sum()
    max_funding   = df["amount_inr_crore"].max()
    avg_funding   = df["amount_inr_crore"][df["amount_inr_crore"] > 0].mean()
    total_funded  = df["startup"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Funding",   f"₹{total_funding:,.0f} Cr")
    c2.metric("Max Single Deal", f"₹{max_funding:,.0f} Cr")
    c3.metric("Avg Deal Size",   f"₹{avg_funding:,.1f} Cr")
    c4.metric("Funded Startups", f"{total_funded:,}")

    st.markdown("---")

    #  MoM chart: Total + Count 
    st.subheader("Month-on-Month Funding")
    mom_toggle = st.radio("View", ["Total (₹ Cr)", "Deal Count"], horizontal=True)

    mom = df.dropna(subset=["date"]).copy()
    mom["ym"] = mom["date"].dt.to_period("M").astype(str)

    if mom_toggle == "Total (₹ Cr)":
        mom_grp = mom.groupby("ym")["amount_inr_crore"].sum().reset_index()
        y_col   = "amount_inr_crore"
        ylabel  = "₹ Crore"
    else:
        mom_grp = mom.groupby("ym")["startup"].count().reset_index()
        y_col   = "startup"
        ylabel  = "Number of Deals"

    fig, ax = plt.subplots(figsize=(14, 3.5))
    ax.fill_between(mom_grp["ym"], mom_grp[y_col], color=ACCENT, alpha=0.3)
    ax.plot(mom_grp["ym"], mom_grp[y_col], color=ACCENT, linewidth=2)
    step = max(1, len(mom_grp) // 12)
    ax.set_xticks(mom_grp["ym"][::step])
    ax.set_xticklabels(mom_grp["ym"][::step], rotation=45, ha="right", fontsize=7)
    ax.set_ylabel(ylabel)
    style_fig(fig)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Sector analysis pie 
    with col1:
        st.subheader("Top Sectors")
        sec_toggle = st.radio("By", ["Deal Count", "Total Funding"], horizontal=True, key="sec")
        if sec_toggle == "Deal Count":
            sec = df["industry"].value_counts().head(8)
        else:
            sec = df.groupby("industry")["amount_inr_crore"].sum().nlargest(8)

        fig, ax = plt.subplots(figsize=(6, 5))
        wedges, texts, autotexts = ax.pie(
            sec.values, labels=sec.index, autopct="%1.1f%%",
            colors=COLORS, startangle=140,
            textprops={"color": TEXT, "fontsize": 8},
            wedgeprops={"edgecolor": DARK_BG, "linewidth": 1.5}
        )
        for at in autotexts:
            at.set_color(DARK_BG); at.set_fontsize(7)
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    # Type of funding 
    with col2:
        st.subheader("Type of Funding")
        inv_type = df["investment_type"].value_counts().head(8)
        fig, ax  = plt.subplots(figsize=(6, 5))
        bars = ax.barh(inv_type.index[::-1], inv_type.values[::-1], color=COLORS)
        ax.bar_label(bars, padding=4, color=MUTED, fontsize=7)
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    st.markdown("---")
    col3, col4 = st.columns(2)

    #  City wise funding 
    with col3:
        st.subheader("City Wise Funding")
        city = df.groupby("city")["amount_inr_crore"].sum().nlargest(10)
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.barh(city.index[::-1], city.values[::-1], color=ACCENT, alpha=0.85)
        ax.bar_label(bars, fmt="%.0f", padding=4, color=MUTED, fontsize=7)
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    # Top investors 
    with col4:
        st.subheader("Top Investors")
        top_inv = investors_exploded().value_counts().drop("Undisclosed", errors="ignore").head(10)
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.barh(top_inv.index[::-1], top_inv.values[::-1], color="#22d3ee", alpha=0.85)
        ax.bar_label(bars, padding=4, color=MUTED, fontsize=7)
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    st.markdown("---")

    # Top startups year wise 
    st.subheader("Top Startups")
    year_filter = st.selectbox("Year", ["Overall"] + sorted(df["year"].unique().tolist(), reverse=True))
    top_n = st.slider("Top N", 5, 20, 10)

    if year_filter == "Overall":
        top_s = df.groupby("startup")["amount_inr_crore"].sum().nlargest(top_n)
    else:
        top_s = df[df["year"] == year_filter].groupby("startup")["amount_inr_crore"].sum().nlargest(top_n)

    fig, ax = plt.subplots(figsize=(12, 4))
    bars = ax.bar(top_s.index, top_s.values, color=COLORS * 3)
    ax.bar_label(bars, fmt="%.0f", padding=3, color=MUTED, fontsize=7)
    plt.xticks(rotation=35, ha="right", fontsize=8)
    style_fig(fig)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")

    # Funding heatmap (year × month) 
    st.subheader(" Funding Heatmap (Year × Month)")
    heat = df.dropna(subset=["date"]).copy()
    heat["month_num"] = heat["date"].dt.month
    heat["month_name"] = heat["date"].dt.strftime("%b")
    pivot = heat.pivot_table(index="year", columns="month_name", values="amount_inr_crore", aggfunc="sum")
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])

    fig, ax = plt.subplots(figsize=(14, 5))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns, fontsize=8)
    ax.set_yticks(range(len(pivot.index)));  ax.set_yticklabels(pivot.index, fontsize=8)
    plt.colorbar(im, ax=ax, label="₹ Crore")
    style_fig(fig)
    st.pyplot(fig)
    plt.close()



# SECTION 2 — STARTUP POV


def show_startup(name):
    st.title(f" {name}")
    data = df[df["startup"].str.lower() == name.lower()].sort_values("date", ascending=False)

    if data.empty:
        st.warning("No data found for this startup.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Raised",  f"₹{data['amount_inr_crore'].sum():,.1f} Cr")
    c2.metric("Funding Rounds", len(data))
    c3.metric("Industry",       data["industry"].iloc[0])
    c4.metric("City",           data["city"].iloc[0])

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Funding Rounds")
        st.dataframe(
            data[["date","investment_type","investors","amount_inr_crore"]]
            .rename(columns={"amount_inr_crore":"₹ Crore"}),
            use_container_width=True
        )

    with col2:
        st.subheader("Funding Over Time")
        fig, ax = plt.subplots(figsize=(6, 4))
        valid = data.dropna(subset=["date"])
        ax.bar(valid["date"].dt.strftime("%b %Y"), valid["amount_inr_crore"], color=ACCENT, alpha=0.85)
        plt.xticks(rotation=35, ha="right", fontsize=8)
        ax.set_ylabel("₹ Crore")
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    st.markdown("---")
    st.subheader("Similar Companies")
    industry = data["industry"].iloc[0]
    similar  = df[(df["industry"] == industry) & (df["startup"] != name)]["startup"].value_counts().head(6).index.tolist()
    st.write(", ".join(similar) if similar else "No similar companies found.")



# SECTION 3 — INVESTOR POV


def show_investor(investor):
    st.title(f"{investor}")
    inv_df = df[df["investors"].str.contains(investor, na=False, regex=False)]

    if inv_df.empty:
        st.warning("No data found for this investor.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Invested",  f"₹{inv_df['amount_inr_crore'].sum():,.1f} Cr")
    c2.metric("Total Deals",     len(inv_df))
    c3.metric("Unique Startups", inv_df["startup"].nunique())
    c4.metric("Avg Deal Size",   f"₹{inv_df['amount_inr_crore'].mean():,.1f} Cr")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Recent investments 
    with col1:
        st.subheader("Most Recent Investments")
        recent = inv_df[["date","startup","industry","amount_inr_crore","investment_type"]]\
            .sort_values("date", ascending=False).head(5)\
            .rename(columns={"amount_inr_crore":"₹ Crore"})
        st.dataframe(recent, use_container_width=True)

    # Biggest investments 
    with col2:
        st.subheader("Biggest Investments")
        big = inv_df.groupby("startup")["amount_inr_crore"].sum().nlargest(5)
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(big.index, big.values, color=COLORS)
        ax.bar_label(bars, fmt="%.0f", padding=3, color=MUTED, fontsize=8)
        plt.xticks(rotation=30, ha="right", fontsize=8)
        ax.set_ylabel("₹ Crore")
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    st.markdown("---")
    col3, col4, col5 = st.columns(3)

    # Sector pie 
    with col3:
        st.subheader("Sectors Invested In")
        sec = inv_df["industry"].value_counts().head(6)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(sec.values, labels=sec.index, colors=COLORS, autopct="%1.0f%%",
               startangle=140, textprops={"color": TEXT, "fontsize": 7},
               wedgeprops={"edgecolor": DARK_BG})
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    # Stage pie 
    with col4:
        st.subheader("Stage Preference")
        stage = inv_df["investment_type"].value_counts().head(6)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(stage.values, labels=stage.index, colors=COLORS[::-1], autopct="%1.0f%%",
               startangle=140, textprops={"color": TEXT, "fontsize": 7},
               wedgeprops={"edgecolor": DARK_BG})
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    # City pie 
    with col5:
        st.subheader("City Preference")
        city = inv_df["city"].value_counts().head(6)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(city.values, labels=city.index, colors=COLORS[2:], autopct="%1.0f%%",
               startangle=140, textprops={"color": TEXT, "fontsize": 7},
               wedgeprops={"edgecolor": DARK_BG})
        style_fig(fig)
        st.pyplot(fig)
        plt.close()

    st.markdown("---")

    # YoY investment graph 
    st.subheader("Year-on-Year Investment")
    yoy = inv_df.groupby("year").agg(total=("amount_inr_crore","sum"), deals=("startup","count")).reset_index()
    yoy = yoy[yoy["year"] > 0]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax2 = ax1.twinx()
    ax1.bar(yoy["year"].astype(str), yoy["total"], color=ACCENT, alpha=0.7, label="₹ Crore")
    ax2.plot(yoy["year"].astype(str), yoy["deals"], color="#f59e0b", marker="o", linewidth=2, label="Deals")
    ax1.set_ylabel("₹ Crore", color=MUTED)
    ax2.set_ylabel("Deal Count", color=MUTED)
    ax1.tick_params(colors=MUTED); ax2.tick_params(colors=MUTED)
    style_fig(fig, [ax1, ax2])
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, labels1+labels2, facecolor=CARD_BG, labelcolor=TEXT, fontsize=8)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")

    # Similar investors 
    st.subheader(" Similar Investors")
    top_sectors  = inv_df["industry"].value_counts().head(2).index.tolist()
    similar_inv  = (
        df[df["industry"].isin(top_sectors)]["investors"]
        .str.split(",").explode().str.strip()
        .value_counts()
        .drop(investor, errors="ignore")
        .drop("Undisclosed", errors="ignore")
        .head(6)
    )
    st.write(", ".join(similar_inv.index.tolist()))



# SIDEBAR + ROUTING


st.sidebar.title("Indian Startup Funding")
st.sidebar.markdown("---")
option = st.sidebar.selectbox("Select View", ["Overall Analysis", "Startup", "Investor"])

if option == "Overall Analysis":
    show_overall()

elif option == "Startup":
    selected_startup = st.sidebar.selectbox(
        "Select Startup",
        sorted(df["startup"].dropna().unique().tolist())
    )
    btn = st.sidebar.button("Analyse Startup")
    if btn:
        show_startup(selected_startup)
    else:
        st.title("Startup Analysis")
        st.info("Select a startup from the sidebar and click **Analyse Startup**")

else:
    investors_list = sorted(
        investors_exploded().value_counts()
        .drop("Undisclosed", errors="ignore").index.tolist()
    )
    selected_investor = st.sidebar.selectbox("Select Investor", investors_list)
    btn = st.sidebar.button("Analyse Investor")
    if btn:
        show_investor(selected_investor)
    else:
        st.title("Investor Analysis")
        st.info("Select an investor from the sidebar and click **Analyse Investor**")
