# HealthSensex AI — National Health Intelligence Portal
### Kraken'X 2026 Hackathon

---

## Local Setup (VS Code mein chalane ke liye)

### Step 1 — Python environment
```bash
pip install streamlit pandas numpy scikit-learn plotly sqlalchemy
```

### Step 2 — Run karo
```bash
cd healthsensex_portal
streamlit run app.py
```

Browser mein automatically `http://localhost:8501` open ho jaayega.

---

## Login Credentials (Demo)
- **Govt Official Password:** `gov2024`

---

## Deploy on Streamlit Cloud (Free — 5 minutes)

1. Ye poora `healthsensex_portal` folder ek **GitHub repository** mein push karo
   ```bash
   git init
   git add .
   git commit -m "HealthSensex AI - Kraken'X 2026"
   git branch -M main
   git remote add origin https://github.com/TUMHARA_USERNAME/healthsensex.git
   git push -u origin main
   ```

2. Jaao: https://share.streamlit.io

3. "New app" click karo

4. GitHub repo select karo → Branch: `main` → File: `app.py`

5. "Deploy" → 2-3 minute mein LIVE link milega jaise:
   `https://healthsensex-XXXXX.streamlit.app`

---

## Project Structure
```
healthsensex_portal/
├── app.py              ← Main application (sabkuch yahan hai)
├── requirements.txt    ← Python dependencies
├── README.md           ← Ye file
└── healthsensex.db     ← SQLite database (auto-create hoga)
```

---

## Judges ko kya dikhana hai (10 min demo script)

1. **Hospital Registration** (2 min)
   - Form fill karo live, submit karo
   - "Status Check" mein registered hospital dikhao

2. **Public Dashboard** (3 min)
   - HealthSensex Index dikhao (explain: ye India ka health score hai)
   - Disease abbreviation table dikhao
   - Regional charts dikhao
   - Outbreak alert dikhao (dengue spike)

3. **Govt Official Portal** (4 min)
   - Password: `gov2024` enter karo
   - Fraud flags table dikhao — Risk Score column highlight karo
   - "Mark for Audit" button press karo
   - Pie chart dikhao (fraud types)
   - "Verify Hospital" karo ek registration verify karke

4. **Wrap up** (1 min)
   - "Abhi ye synthetic data pe hai, real deployment mein ABDM API se live data aayega"
   - "DNA + biometric module Phase 2 mein aayega"

---

## Data ke baare mein judges ko kya bolna hai

**Q: Data kahan se aaya?**
A: "Prototype ke liye humne realistic synthetic data generate kiya hai jo actual ABDM
   data patterns ko mirror karta hai — actual patient data use karna ethical aur legal
   issues raise karta, isliye synthetic data use kiya. Real deployment mein ABDM ka
   official API use hoga jiska access NHA provide karta hai authorized developers ko."

**Q: Security kya hai?**
A: "Production mein: Role-based access control, AES-256 encryption for stored data,
   every govt action audit-logged, Aadhaar OTP for hospital registration verification,
   and zero PII stored on our servers — only anonymized health event data."
