# =============================================================================
# HealthSensex — National Hospital Registration & Health Intelligence Portal
# Kraken'X 2026 Hackathon | Run: streamlit run app.py
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import warnings, os
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="HealthSensex — National Health Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────────────────────────────────

DB_PATH = "healthsensex.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_name TEXT NOT NULL,
            registration_number TEXT UNIQUE NOT NULL,
            abdm_id TEXT,
            hospital_type TEXT,
            state TEXT,
            district TEXT,
            pincode TEXT,
            beds INTEGER,
            contact_email TEXT,
            contact_phone TEXT,
            medical_superintendent TEXT,
            status TEXT DEFAULT 'Pending Verification',
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            verified_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            hospital_id INTEGER,
            performed_by TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Government portal aesthetic, deep navy + saffron + white
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #04080f;
    color: #d4dce8;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #070d18 !important;
    border-right: 1px solid #0f1e30;
}
[data-testid="stSidebar"] .stRadio label {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.88rem;
    letter-spacing: 0.04em;
    color: #7a9ab8;
    padding: 6px 0;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] input:checked + div {
    border-color: #d4830a !important;
}

/* Input fields */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stNumberInput"] input {
    background: #07111e !important;
    border: 1px solid #0f2233 !important;
    border-radius: 4px !important;
    color: #d4dce8 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #d4830a !important;
    box-shadow: 0 0 0 2px rgba(212,131,10,0.15) !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #07111e;
    border: 1px solid #0f2233;
    border-top: 3px solid #d4830a;
    border-radius: 6px;
    padding: 1.2rem 1.4rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #5a7a9a !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    color: #e8f0f8 !important;
}

/* Buttons */
.stButton > button {
    background: #d4830a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    font-size: 0.82rem !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #b8700a !important;
    box-shadow: 0 4px 16px rgba(212,131,10,0.3) !important;
}

/* Success / Error */
.stSuccess { background: #071a0e !important; border-left: 4px solid #16a34a !important; }
.stError   { background: #1a0707 !important; border-left: 4px solid #dc2626 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #0f2233 !important; border-radius: 6px; }

/* Expander */
[data-testid="stExpander"] {
    background: #07111e !important;
    border: 1px solid #0f2233 !important;
    border-radius: 6px !important;
}

h1,h2,h3,h4 { font-family: 'Source Serif 4', serif !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #04080f; }
::-webkit-scrollbar-thumb { background: #0f2233; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #d4830a; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

def render_header(subtitle=""):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #070d18 0%, #0a1628 60%, #07111e 100%);
        border-bottom: 3px solid #d4830a;
        padding: 1.4rem 2rem 1.2rem 2rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 1.4rem;
    ">
        <div style="
            width: 54px; height: 54px;
            background: linear-gradient(135deg, #d4830a, #b8700a);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem; flex-shrink: 0;
            box-shadow: 0 4px 16px rgba(212,131,10,0.4);
        ">🏛️</div>
        <div>
            <div style="
                font-family: 'Source Serif 4', serif;
                font-size: 1.55rem; font-weight: 700;
                color: #e8f0f8; letter-spacing: 0.01em; line-height: 1.2;
            ">HealthSensex — National Health Intelligence Portal</div>
            <div style="
                font-family: 'IBM Plex Sans', sans-serif;
                font-size: 0.72rem; color: #4a6a8a;
                letter-spacing: 0.14em; text-transform: uppercase; margin-top: 4px;
            ">Ministry of Health & Family Welfare · Government of India {'· ' + subtitle if subtitle else ''}</div>
        </div>
        <div style="margin-left: auto; text-align: right;">
            <div style="
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.7rem; color: #2a6a2a;
                background: #071a0e; border: 1px solid #164a16;
                border-radius: 20px; padding: 4px 14px; display: inline-block;
                animation: blink 2s infinite;
            ">● LIVE SYSTEM</div>
            <div style="font-size: 0.65rem; color: #2a4a6a; margin-top: 6px; font-family: IBM Plex Mono;">
                {datetime.now().strftime('%d %b %Y  %H:%M IST')}
            </div>
        </div>
    </div>
    <style>@keyframes blink {{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}</style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# INDIA STATES LIST
# ─────────────────────────────────────────────────────────────────────────────

INDIA_STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
    "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
    "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
    "Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
    "Andaman & Nicobar Islands","Chandigarh","Dadra & Nagar Haveli",
    "Daman & Diu","Delhi","Jammu & Kashmir","Ladakh","Lakshadweep","Puducherry"
]

DISEASE_ABBR = {
    "Dengue": "DEN", "Tuberculosis": "TB", "Malaria": "MAL",
    "Typhoid": "TYP", "COVID-19": "COV", "Cardiac": "CAR",
    "Orthopedic": "ORT", "Cancer": "CAN", "Cholera": "CHL",
    "Pneumonia": "PNE", "Hepatitis B": "HEP-B", "HIV/AIDS": "HIV",
    "Chikungunya": "CHK", "Japanese Encephalitis": "JE", "Leptospirosis": "LEP"
}

# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC DATA (same as existing prototype + region info)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def generate_data(seed=42):
    np.random.seed(seed)
    N_HOSPITALS = 12
    N_DOCTORS   = 60
    date_range  = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    hosp_ids    = [f"HOSP-{str(i).zfill(3)}" for i in range(1, N_HOSPITALS+1)]
    dr_ids      = [f"DR-{str(i).zfill(4)}" for i in range(1, N_DOCTORS+1)]
    diseases    = list(DISEASE_ABBR.keys())[:8]
    states      = ["Maharashtra","Delhi","Karnataka","Tamil Nadu","Uttar Pradesh",
                   "Gujarat","West Bengal","Rajasthan","Kerala","Telangana",
                   "Punjab","Madhya Pradesh"]
    hosp_states = {h: states[i] for i, h in enumerate(hosp_ids)}

    records = []
    for date in date_range:
        for hosp in hosp_ids:
            for _ in range(np.random.randint(3,9)):
                billing = np.clip(np.random.lognormal(10.5, 0.6), 5000, 200000)
                records.append({
                    "Date": date, "Hospital_ID": hosp,
                    "Doctor_ID": np.random.choice(dr_ids),
                    "Disease_Type": np.random.choice(diseases),
                    "State": hosp_states[hosp],
                    "Daily_Billing_Amount": round(billing, 2),
                    "Death_Certs_Signed": np.random.choice([0,1,2], p=[0.70,0.22,0.08]),
                    "_fraud_label": "None"
                })
    df = pd.DataFrame(records)

    # Fraud injection
    m1 = (df.Hospital_ID=="HOSP-007")&(df.Disease_Type=="Dengue")&(df.Date>="2024-06-01")&(df.Date<="2024-06-14")
    df.loc[m1,"Daily_Billing_Amount"] *= 10
    df.loc[m1,"_fraud_label"] = "Billing Spike"
    m2 = (df.Doctor_ID=="DR-0042")&(df.Date>="2024-10-15")&(df.Date<="2024-10-16")
    df.loc[m2,"Death_Certs_Signed"] = np.random.randint(28,36)
    df.loc[m2&(df._fraud_label=="None"),"_fraud_label"] = "Death Cert Velocity"
    return df

@st.cache_data
def run_model(seed=42, contamination=0.03):
    df = generate_data(seed)
    df = df.sort_values(["Hospital_ID","Date"]).reset_index(drop=True)
    df["Billing_7d_Avg"] = df.groupby("Hospital_ID")["Daily_Billing_Amount"].transform(
        lambda x: x.rolling(7, min_periods=1).mean())
    df["Billing_Dev"] = df["Daily_Billing_Amount"] / (df["Billing_7d_Avg"] + 1e-6)
    daily_dc = df.groupby(["Doctor_ID","Date"])["Death_Certs_Signed"].sum().reset_index().rename(
        columns={"Death_Certs_Signed":"Doctor_Daily_DC"})
    df = df.merge(daily_dc, on=["Doctor_ID","Date"], how="left")
    stats = df.groupby("Disease_Type")["Daily_Billing_Amount"].agg(["mean","std"])
    df = df.merge(stats, on="Disease_Type", how="left")
    df["Billing_Z"] = (df["Daily_Billing_Amount"] - df["mean"]) / (df["std"] + 1e-6)
    df.drop(columns=["mean","std"], inplace=True)

    X = df[["Daily_Billing_Amount","Billing_7d_Avg","Billing_Dev","Doctor_Daily_DC","Billing_Z"]].fillna(0)
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42, n_jobs=-1)
    model.fit(X)
    df["Anomaly_Raw"] = -model.score_samples(X)
    df["Flagged"] = model.predict(X) == -1
    s_min, s_max = df.Anomaly_Raw.min(), df.Anomaly_Raw.max()
    df["Risk_Score"] = ((df.Anomaly_Raw - s_min)/(s_max - s_min + 1e-9)*100).round(1)

    conds   = [df.Doctor_Daily_DC>=10, df.Billing_Dev>=5.0, df.Billing_Z>=3.0]
    choices = ["⚰️ Death Cert Velocity", "💰 Billing Spike", "📊 Statistical Outlier"]
    df["Flag_Reason"] = np.select(conds, choices, default="🔍 Composite Anomaly")

    anomaly_rate = df.Flagged.mean()
    h = max(0, min(100, round(100 - anomaly_rate*1500 - (10 if df.Billing_Dev.max()>5 else 0) - (5 if df.Doctor_Daily_DC.max()>20 else 0), 1)))
    return df, h

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAV
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 0.5rem 0;">
        <div style="font-family:'Source Serif 4',serif;font-size:1.1rem;color:#d4830a;font-weight:700;">
            HealthSensex
        </div>
        <div style="font-size:0.65rem;color:#2a4a6a;letter-spacing:0.1em;text-transform:uppercase;margin-top:2px;">
            National Health Portal
        </div>
    </div>
    <hr style="border:none;border-top:1px solid #0f2233;margin:0.8rem 0;">
    """, unsafe_allow_html=True)

    page = st.radio("NAVIGATION", [
        "🏥  Hospital Registration",
        "📊  Public Health Dashboard",
        "🔒  Govt Official Portal",
    ], label_visibility="visible")

    st.markdown("""
    <hr style="border:none;border-top:1px solid #0f2233;margin:1rem 0 0.5rem 0;">
    <div style="font-size:0.62rem;color:#1a3050;font-family:IBM Plex Mono;line-height:2;">
    DATA SOURCE: Synthetic (Demo)<br>
    ABDM SYNC: Simulated<br>
    RECORDS: ~30,000+<br>
    MODEL: Isolation Forest<br>
    BUILD: Kraken'X 2026
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# PAGE 1 — HOSPITAL REGISTRATION
# =============================================================================

if page == "🏥  Hospital Registration":
    render_header("Hospital Registration System")

    # Stats row
    conn = get_conn()
    total_reg = pd.read_sql("SELECT COUNT(*) as c FROM hospitals", conn).iloc[0,0]
    verified  = pd.read_sql("SELECT COUNT(*) as c FROM hospitals WHERE status='Verified'", conn).iloc[0,0]
    pending   = pd.read_sql("SELECT COUNT(*) as c FROM hospitals WHERE status='Pending Verification'", conn).iloc[0,0]
    conn.close()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🏥 Registered Hospitals", f"{total_reg:,}")
    c2.metric("✅ Verified", f"{verified:,}")
    c3.metric("⏳ Pending", f"{pending:,}")
    c4.metric("🔗 ABDM Linked (Simulated)", "28,145")

    st.markdown("<br>", unsafe_allow_html=True)

    # Info banner
    st.markdown("""
    <div style="
        background: #07111e; border: 1px solid #0f2233;
        border-left: 4px solid #d4830a; border-radius: 6px;
        padding: 1rem 1.4rem; margin-bottom: 1.5rem;
        font-size: 0.83rem; color: #7a9ab8; line-height: 1.7;
    ">
        <strong style="color:#d4830a;">📌 Registration Guidelines</strong><br>
        All hospitals operating in India are required to register on this portal under the
        National Health Policy 2024. Hospitals already registered with ABDM (Ayushman Bharat
        Digital Mission) must provide their ABDM ID for automatic re-verification.
        New registrations will be reviewed within <strong style="color:#e8f0f8;">5–7 working days</strong>.
        Fraudulent registrations are subject to action under IPC Section 420.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝  New Registration", "🔍  Verify / Check Status"])

    # ── TAB 1: Registration Form ──────────────────────────────────────────────
    with tab1:
        st.markdown("""
        <div style="font-family:'Source Serif 4',serif;font-size:1.2rem;color:#a8c8e8;
                    margin-bottom:1.2rem;padding-bottom:0.6rem;border-bottom:1px solid #0f2233;">
            Hospital Registration Form
            <span style="font-family:'IBM Plex Sans',sans-serif;font-size:0.72rem;
                         color:#4a6a8a;margin-left:1rem;letter-spacing:0.1em;text-transform:uppercase;">
                Form HSX-REG-2024
            </span>
        </div>
        """, unsafe_allow_html=True)

        with st.form("hospital_registration_form", clear_on_submit=True):
            st.markdown("**SECTION A — Hospital Identity**")
            col1, col2 = st.columns(2)
            with col1:
                hosp_name   = st.text_input("Hospital / Institution Name *", placeholder="e.g. Apollo Hospitals Delhi")
                reg_number  = st.text_input("Registration Number *", placeholder="e.g. MH/HOS/2024/001234")
                abdm_id     = st.text_input("ABDM Health Facility ID (if registered)", placeholder="HFR-XXXXXX (leave blank if not yet registered)")
            with col2:
                hosp_type   = st.selectbox("Hospital Type *", [
                    "— Select —",
                    "Government District Hospital",
                    "Government Medical College Hospital",
                    "Government Primary Health Centre (PHC)",
                    "Government Community Health Centre (CHC)",
                    "Private Multi-Specialty Hospital",
                    "Private Single-Specialty Clinic",
                    "Private Nursing Home",
                    "Charitable / Trust Hospital",
                    "AIIMS / Central Govt Institution",
                    "ESI / CGHS Empanelled",
                ])
                beds        = st.number_input("Total Bed Capacity *", min_value=1, max_value=5000, value=50)
                ms_name     = st.text_input("Medical Superintendent Name *", placeholder="Dr. Full Name")

            st.markdown("<br>**SECTION B — Location**", unsafe_allow_html=True)
            col3, col4, col5 = st.columns(3)
            with col3:
                state    = st.selectbox("State / UT *", ["— Select —"] + INDIA_STATES)
            with col4:
                district = st.text_input("District *", placeholder="e.g. South Delhi")
            with col5:
                pincode  = st.text_input("PIN Code *", placeholder="110001", max_chars=6)

            st.markdown("<br>**SECTION C — Contact**", unsafe_allow_html=True)
            col6, col7 = st.columns(2)
            with col6:
                email = st.text_input("Official Email Address *", placeholder="admin@hospital.gov.in")
            with col7:
                phone = st.text_input("Contact Number *", placeholder="+91 XXXXX XXXXX")

            st.markdown("<br>", unsafe_allow_html=True)
            col_cb, col_btn = st.columns([3,1])
            with col_cb:
                declaration = st.checkbox(
                    "I hereby declare that all information provided is accurate and I authorise the "
                    "Ministry of Health to verify this data with ABDM and relevant state authorities."
                )
            with col_btn:
                submitted = st.form_submit_button("SUBMIT REGISTRATION →", use_container_width=True)

        if submitted:
            errors = []
            if not hosp_name.strip(): errors.append("Hospital Name")
            if not reg_number.strip(): errors.append("Registration Number")
            if hosp_type == "— Select —": errors.append("Hospital Type")
            if state == "— Select —": errors.append("State")
            if not district.strip(): errors.append("District")
            if not pincode.strip() or not pincode.isdigit() or len(pincode)!=6: errors.append("Valid 6-digit PIN Code")
            if not email.strip() or "@" not in email: errors.append("Valid Email")
            if not ms_name.strip(): errors.append("Medical Superintendent Name")
            if not declaration: errors.append("Declaration checkbox")

            if errors:
                st.error(f"⚠️ Please fill in: **{', '.join(errors)}**")
            else:
                try:
                    conn = get_conn()
                    conn.execute("""
                        INSERT INTO hospitals
                        (hospital_name, registration_number, abdm_id, hospital_type,
                         state, district, pincode, beds, contact_email, contact_phone,
                         medical_superintendent, status)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,'Pending Verification')
                    """, (hosp_name.strip(), reg_number.strip(), abdm_id.strip() or None,
                          hosp_type, state, district.strip(), pincode.strip(),
                          beds, email.strip(), phone.strip(), ms_name.strip()))
                    conn.commit()
                    ref_id = f"HSX{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    conn.close()
                    st.success(f"""
                    ✅ **Registration Submitted Successfully**

                    **Reference ID:** `{ref_id}`
                    **Hospital:** {hosp_name}
                    **Status:** Pending Verification

                    Please save your Reference ID. Verification will be completed within 5–7 working days.
                    You will receive a confirmation on **{email}**.
                    """)
                except sqlite3.IntegrityError:
                    st.error("⚠️ A hospital with this Registration Number already exists in the system.")

    # ── TAB 2: Check Status ───────────────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div style="font-family:'Source Serif 4',serif;font-size:1.2rem;color:#a8c8e8;
                    margin-bottom:1.2rem;padding-bottom:0.6rem;border-bottom:1px solid #0f2233;">
            Hospital Verification Status Check
        </div>
        """, unsafe_allow_html=True)

        search_reg = st.text_input("Enter Registration Number", placeholder="MH/HOS/2024/001234")
        if st.button("CHECK STATUS"):
            if search_reg.strip():
                conn = get_conn()
                row = pd.read_sql(
                    "SELECT * FROM hospitals WHERE registration_number=?",
                    conn, params=(search_reg.strip(),)
                )
                conn.close()
                if len(row) > 0:
                    r = row.iloc[0]
                    status_color = {"Verified":"#16a34a","Pending Verification":"#d4830a","Rejected":"#dc2626"}.get(r.status,"#7a9ab8")
                    st.markdown(f"""
                    <div style="background:#07111e;border:1px solid #0f2233;border-radius:8px;padding:1.6rem 2rem;margin-top:1rem;">
                        <div style="font-family:'Source Serif 4',serif;font-size:1.1rem;color:#e8f0f8;margin-bottom:1rem;">
                            {r.hospital_name}
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;font-size:0.82rem;">
                            <div><span style="color:#4a6a8a;text-transform:uppercase;font-size:0.65rem;letter-spacing:0.1em;">Reg Number</span><br>
                                 <span style="color:#e8f0f8;font-family:IBM Plex Mono;">{r.registration_number}</span></div>
                            <div><span style="color:#4a6a8a;text-transform:uppercase;font-size:0.65rem;letter-spacing:0.1em;">Type</span><br>
                                 <span style="color:#e8f0f8;">{r.hospital_type}</span></div>
                            <div><span style="color:#4a6a8a;text-transform:uppercase;font-size:0.65rem;letter-spacing:0.1em;">Location</span><br>
                                 <span style="color:#e8f0f8;">{r.district}, {r.state}</span></div>
                            <div><span style="color:#4a6a8a;text-transform:uppercase;font-size:0.65rem;letter-spacing:0.1em;">Beds</span><br>
                                 <span style="color:#e8f0f8;">{r.beds}</span></div>
                            <div><span style="color:#4a6a8a;text-transform:uppercase;font-size:0.65rem;letter-spacing:0.1em;">Registered On</span><br>
                                 <span style="color:#e8f0f8;">{r.registered_at[:10]}</span></div>
                            <div><span style="color:#4a6a8a;text-transform:uppercase;font-size:0.65rem;letter-spacing:0.1em;">Status</span><br>
                                 <span style="color:{status_color};font-weight:600;">● {r.status}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No hospital found with that registration number.")

        # Show all registered hospitals (demo data)
        st.markdown("<br>**All Registered Hospitals (Demo Data)**", unsafe_allow_html=True)
        conn = get_conn()
        all_hosps = pd.read_sql(
            "SELECT hospital_name, registration_number, hospital_type, state, district, beds, status, registered_at FROM hospitals ORDER BY id DESC",
            conn
        )
        conn.close()
        if len(all_hosps) > 0:
            all_hosps["registered_at"] = all_hosps["registered_at"].str[:10]
            st.dataframe(all_hosps, use_container_width=True, height=320)
        else:
            st.info("No registrations yet. Use the registration form above to add hospitals.")


# =============================================================================
# PAGE 2 — PUBLIC HEALTH DASHBOARD
# =============================================================================

elif page == "📊  Public Health Dashboard":
    render_header("Public Health Intelligence")

    df, h_index = run_model()

    # ── HealthSensex Index ────────────────────────────────────────────────────
    score_color = "#22c55e" if h_index>=75 else "#f97316" if h_index>=50 else "#ef4444"
    status_text = "HEALTHY" if h_index>=75 else "MODERATE RISK" if h_index>=50 else "HIGH RISK"

    col_idx, col_info = st.columns([1, 2.5], gap="large")

    with col_idx:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #070d18, #0a1628, #07111e);
            border: 2px solid #0f2a4a; border-radius: 12px;
            padding: 2rem 1.5rem; text-align: center;
            box-shadow: 0 0 40px rgba(20,80,160,0.15);
        ">
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.7rem;
                        letter-spacing:0.2em;text-transform:uppercase;color:#4a6a8a;">
                HEALTHSENSEX INDEX
            </div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:5.5rem;
                        font-weight:600;line-height:1;color:{score_color};margin:0.5rem 0;">
                {h_index}
            </div>
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.78rem;
                        color:{score_color};letter-spacing:0.18em;opacity:0.9;">
                {status_text}
            </div>
            <div style="font-size:0.65rem;color:#1e3a5a;margin-top:1rem;font-family:IBM Plex Mono;">
                0 = CRISIS &nbsp;·&nbsp; 100 = PERFECT
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("📋 Total Records", f"{len(df):,}")
        m2.metric("🚨 Anomalies", f"{df.Flagged.sum():,}", delta=f"{df.Flagged.mean()*100:.1f}%", delta_color="inverse")
        m3.metric("🏥 Hospitals Monitored", "12")
        m4.metric("💊 Disease Types Tracked", str(len(DISEASE_ABBR)))

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#07111e;border:1px solid #0f2233;border-radius:6px;
                    padding:0.9rem 1.2rem;font-size:0.8rem;color:#5a7a9a;line-height:1.8;">
            <strong style="color:#d4830a;">What is HealthSensex Index?</strong><br>
            Similar to how SENSEX tracks market health (0–30,000), HealthSensex tracks
            national healthcare integrity on a <strong style="color:#e8f0f8;">0–100 scale</strong>.
            Score drops when fraud, billing anomalies, or mortality spikes are detected.
            Government officials receive alerts when the index falls below 70.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Disease Abbreviation Reference ───────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Source Serif 4',serif;font-size:1.15rem;color:#a8c8e8;margin-bottom:0.8rem;">
        Disease Tracking Reference
        <span style="font-family:'IBM Plex Sans',sans-serif;font-size:0.7rem;color:#4a6a8a;
                     margin-left:1rem;letter-spacing:0.1em;text-transform:uppercase;">
            Standardised Abbreviation System
        </span>
    </div>
    """, unsafe_allow_html=True)

    cols_ab = st.columns(2)
    for idx, (disease, abbr) in enumerate(list(DISEASE_ABBR.items())[:8]):
        count = len(df[df.Disease_Type==disease]) if disease in df.Disease_Type.values else 0
        with cols_ab[idx % 2]:
            st.markdown(f'<div style="background:#07111e;border:1px solid #0f2233;border-radius:6px;padding:0.7rem 1rem;display:flex;align-items:center;justify-content:space-between;margin-bottom:0.6rem;"><div><span style="font-family:IBM Plex Mono,monospace;font-size:0.95rem;color:#d4830a;font-weight:600;">{abbr}</span><span style="font-size:0.82rem;color:#7a9ab8;margin-left:0.8rem;">{disease}</span></div><span style="font-size:0.7rem;color:#2a4a6a;">{count:,} records</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown("**Regional Disease Distribution**")
        state_disease = df.groupby(["State","Disease_Type"]).size().reset_index(name="Cases")
        top_states = state_disease.groupby("State")["Cases"].sum().nlargest(8).index
        chart_df = state_disease[state_disease.State.isin(top_states)]
        fig = px.bar(
            chart_df, x="State", y="Cases", color="Disease_Type",
            color_discrete_sequence=px.colors.qualitative.Set2,
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="#07111e", plot_bgcolor="#04080f",
            font=dict(family="IBM Plex Sans", color="#7a9ab8", size=11),
            legend=dict(bgcolor="#07111e", bordercolor="#0f2233", font_size=10),
            margin=dict(l=0,r=0,t=10,b=0), height=320,
            xaxis=dict(gridcolor="#0f2233", tickangle=-30),
            yaxis=dict(gridcolor="#0f2233"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Monthly Billing Trend (National)**")
        monthly = df.groupby(df.Date.dt.to_period("M"))["Daily_Billing_Amount"].sum().reset_index()
        monthly["Date"] = monthly["Date"].astype(str)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=monthly.Date, y=monthly.Daily_Billing_Amount,
            mode="lines+markers", line=dict(color="#d4830a", width=2),
            marker=dict(size=4), name="Total Billing",
            fill="tozeroy", fillcolor="rgba(212,131,10,0.08)"
        ))
        fig2.update_layout(
            paper_bgcolor="#07111e", plot_bgcolor="#04080f",
            font=dict(family="IBM Plex Sans", color="#7a9ab8", size=11),
            margin=dict(l=0,r=0,t=10,b=0), height=320, showlegend=False,
            xaxis=dict(gridcolor="#0f2233", tickangle=-30),
            yaxis=dict(gridcolor="#0f2233"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Outbreak Alerts ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-family:'Source Serif 4',serif;font-size:1.15rem;color:#a8c8e8;margin-bottom:0.8rem;">
        ⚠️ Active Outbreak Alerts
        <span style="font-family:'IBM Plex Sans',sans-serif;font-size:0.7rem;color:#4a6a8a;
                     margin-left:1rem;letter-spacing:0.1em;text-transform:uppercase;">
            Triggered when 7-day rolling average doubles
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Simulate outbreak detection
    df_sorted = df.sort_values(["State","Disease_Type","Date"])
    df_sorted["7d_avg"] = df_sorted.groupby(["State","Disease_Type"])["Daily_Billing_Amount"].transform(
        lambda x: x.rolling(7, min_periods=1).mean())
    alerts = df_sorted[df_sorted.Billing_Dev > 4.0][["State","Disease_Type","Daily_Billing_Amount","Date"]].drop_duplicates(
        subset=["State","Disease_Type"]).head(5)

    if len(alerts) > 0:
        for _, row in alerts.iterrows():
            abbr = DISEASE_ABBR.get(row.Disease_Type, row.Disease_Type[:3].upper())
            st.markdown(f"""
            <div style="background:#1a0a0a;border:1px solid #3a1010;border-left:4px solid #ef4444;
                        border-radius:6px;padding:0.8rem 1.2rem;margin-bottom:0.6rem;
                        display:flex;align-items:center;justify-content:space-between;">
                <div>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.8rem;
                                 color:#ef4444;font-weight:600;">🔴 [{abbr}] OUTBREAK ALERT</span>
                    <span style="font-size:0.82rem;color:#9a5a5a;margin-left:1rem;">
                        {row.Disease_Type} spike detected in <strong style="color:#e8c8c8;">{row.State}</strong>
                    </span>
                </div>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;color:#4a2a2a;">
                    {row.Date.strftime('%d %b %Y')}
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#071a0e;border:1px solid #0f3a1e;border-radius:6px;
                    padding:0.8rem 1.2rem;color:#16a34a;font-size:0.82rem;">
            ✅ No active outbreak alerts. All disease trends within normal parameters.
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# PAGE 3 — GOVT OFFICIAL PORTAL
# =============================================================================

elif page == "🔒  Govt Official Portal":
    render_header("Government Official Access — Restricted")

    # Simple password gate
    if "govt_authed" not in st.session_state:
        st.session_state.govt_authed = False

    if not st.session_state.govt_authed:
        st.markdown("""
        <div style="max-width:420px;margin:3rem auto;">
            <div style="background:#07111e;border:1px solid #0f2233;border-top:3px solid #d4830a;
                        border-radius:8px;padding:2.4rem 2rem;text-align:center;">
                <div style="font-size:2.5rem;margin-bottom:0.8rem;">🔐</div>
                <div style="font-family:'Source Serif 4',serif;font-size:1.2rem;color:#e8f0f8;margin-bottom:0.4rem;">
                    Restricted Access
                </div>
                <div style="font-size:0.75rem;color:#4a6a8a;letter-spacing:0.08em;margin-bottom:1.6rem;">
                    AUTHORISED GOVERNMENT PERSONNEL ONLY
                </div>
        """, unsafe_allow_html=True)

        pwd = st.text_input("Enter Access Code", type="password", placeholder="••••••••")
        if st.button("AUTHENTICATE →", use_container_width=True):
            if pwd == "gov2024":   # demo password
                st.session_state.govt_authed = True
                st.rerun()
            else:
                st.error("⚠️ Invalid access code. This attempt has been logged.")

        st.markdown("""
                <div style="font-size:0.65rem;color:#1a3050;margin-top:1.2rem;font-family:IBM Plex Mono;">
                    DEMO CODE: gov2024 &nbsp;·&nbsp; All access attempts are logged
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        df, h_index = run_model()

        # ── Logout ────────────────────────────────────────────────────────────
        col_title, col_logout = st.columns([4,1])
        with col_logout:
            if st.button("🔓 Logout"):
                st.session_state.govt_authed = False
                st.rerun()

        # ── Welcome banner ────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#071a0e;border:1px solid #0f3a1e;border-radius:6px;
                    padding:0.9rem 1.4rem;margin-bottom:1.5rem;
                    display:flex;align-items:center;justify-content:space-between;">
            <span style="color:#16a34a;font-size:0.83rem;">
                ✅ Authenticated · Official Portal Active ·
                Access logged at {datetime.now().strftime('%H:%M IST')}
            </span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:#0f3a1e;">
                SESSION SECURED
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ── Score + KPIs ──────────────────────────────────────────────────────
        score_color = "#22c55e" if h_index>=75 else "#f97316" if h_index>=50 else "#ef4444"
        col_idx, col_kpi = st.columns([1,3], gap="large")

        with col_idx:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#070d18,#0a1628,#07111e);
                        border:2px solid #0f2a4a;border-radius:12px;
                        padding:1.8rem 1.2rem;text-align:center;">
                <div style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:#4a6a8a;font-family:IBM Plex Mono;">
                    NATIONAL INDEX
                </div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:4.5rem;
                            font-weight:600;line-height:1;color:{score_color};margin:0.4rem 0;">
                    {h_index}
                </div>
                <div style="font-size:0.72rem;color:{score_color};letter-spacing:0.15em;">
                    {"HEALTHY" if h_index>=75 else "MODERATE RISK" if h_index>=50 else "⚠️ HIGH RISK"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_kpi:
            kc1,kc2,kc3,kc4 = st.columns(4)
            flagged_df = df[df.Flagged]
            kc1.metric("🚨 Total Flags", f"{len(flagged_df):,}")
            kc2.metric("🏥 Hospitals at Risk", str(flagged_df.Hospital_ID.nunique()))
            kc3.metric("💰 Suspicious Billing", f"₹{flagged_df.Daily_Billing_Amount.sum()/1e7:.1f} Cr")
            kc4.metric("⚰️ Death Cert Alerts", str((df.Doctor_Daily_DC>=10).sum()))

        st.markdown("---")

        # ── Fraud Flags Table ─────────────────────────────────────────────────
        st.markdown("""
        <div style="font-family:'Source Serif 4',serif;font-size:1.15rem;color:#a8c8e8;
                    margin-bottom:0.8rem;">
            🔴 Flagged High-Risk Records
            <span style="font-family:'IBM Plex Sans',sans-serif;font-size:0.7rem;color:#4a6a8a;
                         margin-left:1rem;letter-spacing:0.1em;text-transform:uppercase;">
                IsolationForest · Sorted by Risk Score
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Active alert banner
        top_hosp = flagged_df.Hospital_ID.value_counts().idxmax() if len(flagged_df)>0 else "N/A"
        st.markdown(f"""
        <div style="background:#1a0a0a;border:1px solid #3a1010;border-left:4px solid #ef4444;
                    border-radius:6px;padding:0.8rem 1.4rem;margin-bottom:1rem;
                    font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:#ff9999;">
            🔴 ACTIVE ALERT &nbsp;|&nbsp; {len(flagged_df):,} suspicious records detected
            &nbsp;·&nbsp; Highest-risk hospital: <strong>{top_hosp}</strong>
            &nbsp;·&nbsp; Recommend: Immediate audit
        </div>
        """, unsafe_allow_html=True)

        # Filter controls
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            sel_hosp = st.multiselect("Filter Hospital", df.Hospital_ID.unique().tolist(), default=df.Hospital_ID.unique().tolist())
        with fc2:
            sel_reason = st.multiselect("Filter Flag Type", df.Flag_Reason.unique().tolist(), default=df.Flag_Reason.unique().tolist())
        with fc3:
            min_risk = st.slider("Min Risk Score", 0, 100, 70)

        view = (
            flagged_df[
                flagged_df.Hospital_ID.isin(sel_hosp) &
                flagged_df.Flag_Reason.isin(sel_reason) &
                (flagged_df.Risk_Score >= min_risk)
            ]
            [["Date","Hospital_ID","Doctor_ID","Disease_Type","State",
              "Daily_Billing_Amount","Billing_Dev","Doctor_Daily_DC","Risk_Score","Flag_Reason"]]
            .sort_values("Risk_Score", ascending=False)
            .rename(columns={
                "Daily_Billing_Amount":"Billing (₹)",
                "Billing_Dev":"Deviation ×",
                "Doctor_Daily_DC":"Death Certs/Day",
                "Risk_Score":"Risk Score",
                "Flag_Reason":"Flag Type",
            })
            .reset_index(drop=True)
        )
        view["Date"] = view["Date"].dt.strftime("%d %b %Y")
        view["Billing (₹)"] = view["Billing (₹)"].map(lambda x: f"₹{x:,.0f}")
        view["Deviation ×"] = view["Deviation ×"].map(lambda x: f"{x:.1f}×")

        st.dataframe(view, use_container_width=True, height=380,
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score", min_value=0, max_value=100, format="%.1f")
            })

        st.caption(f"Showing {len(view):,} flagged records. Click any row to investigate.")

        st.markdown("---")

        # ── Action Buttons ────────────────────────────────────────────────────
        st.markdown("**Official Actions**")
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1:
            if st.button("📋 Mark All for Audit", use_container_width=True):
                conn = get_conn()
                conn.execute("INSERT INTO audit_log (action, performed_by, notes) VALUES (?,?,?)",
                             ("BULK_AUDIT_MARK","govt_official@mohfw.gov.in",f"{len(flagged_df)} records flagged"))
                conn.commit(); conn.close()
                st.success("✅ Flagged records sent to Audit Queue")
        with ac2:
            if st.button("📤 Export CSV", use_container_width=True):
                csv = view.to_csv(index=False)
                st.download_button("⬇️ Download", csv, "fraud_flags.csv", "text/csv", use_container_width=True)
        with ac3:
            if st.button("📨 Alert State Officials", use_container_width=True):
                st.info("📧 Alerts dispatched to State Health Secretaries (simulated)")
        with ac4:
            if st.button("🔄 Re-run Model", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        st.markdown("---")

        # ── Charts ────────────────────────────────────────────────────────────
        col_c1, col_c2 = st.columns(2, gap="large")

        with col_c1:
            st.markdown("**Fraud Flags by Hospital**")
            hf = flagged_df.groupby("Hospital_ID").size().reset_index(name="Flags").sort_values("Flags", ascending=False)
            fig = px.bar(hf, x="Hospital_ID", y="Flags", template="plotly_dark",
                         color="Flags", color_continuous_scale="Reds")
            fig.update_layout(paper_bgcolor="#07111e", plot_bgcolor="#04080f",
                              font=dict(family="IBM Plex Sans", color="#7a9ab8", size=11),
                              margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col_c2:
            st.markdown("**Fraud Type Breakdown**")
            fr = flagged_df.groupby("Flag_Reason").size().reset_index(name="Count")
            fig2 = px.pie(fr, names="Flag_Reason", values="Count", template="plotly_dark",
                          color_discrete_sequence=["#ef4444","#f97316","#eab308","#3b82f6"])
            fig2.update_layout(paper_bgcolor="#07111e", plot_bgcolor="#04080f",
                               font=dict(family="IBM Plex Sans", color="#7a9ab8", size=11),
                               margin=dict(l=0,r=0,t=10,b=0), height=300,
                               legend=dict(bgcolor="#07111e"))
            st.plotly_chart(fig2, use_container_width=True)

        # ── Registered Hospitals Management ───────────────────────────────────
        st.markdown("---")
        with st.expander("🏥 Manage Hospital Registrations", expanded=False):
            conn = get_conn()
            hosps = pd.read_sql("SELECT * FROM hospitals ORDER BY id DESC", conn)
            conn.close()
            if len(hosps) > 0:
                st.dataframe(hosps, use_container_width=True, height=300)
                col_v, col_r = st.columns(2)
                with col_v:
                    verify_id = st.number_input("Verify Hospital ID", min_value=1, step=1)
                    if st.button("✅ Mark as Verified"):
                        conn = get_conn()
                        conn.execute("UPDATE hospitals SET status='Verified', verified_at=? WHERE id=?",
                                     (datetime.now().isoformat(), int(verify_id)))
                        conn.execute("INSERT INTO audit_log (action,hospital_id,performed_by) VALUES (?,?,?)",
                                     ("VERIFIED", int(verify_id), "govt_official"))
                        conn.commit(); conn.close()
                        st.success(f"Hospital ID {verify_id} marked as Verified"); st.rerun()
                with col_r:
                    reject_id = st.number_input("Reject Hospital ID", min_value=1, step=1)
                    if st.button("❌ Mark as Rejected"):
                        conn = get_conn()
                        conn.execute("UPDATE hospitals SET status='Rejected' WHERE id=?", (int(reject_id),))
                        conn.commit(); conn.close()
                        st.error(f"Hospital ID {reject_id} marked as Rejected"); st.rerun()
            else:
                st.info("No hospital registrations yet.")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 0.5rem 0;
            font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#0f2233;border-top:1px solid #0a1828;margin-top:2rem;">
    HealthSensex AI &nbsp;·&nbsp; Built for Kraken'X 2026 &nbsp;·&nbsp;
    Isolation Forest · Scikit-learn · Streamlit · SQLite<br>
    Synthetic data only — no real patient information used or stored.
</div>
""", unsafe_allow_html=True)
