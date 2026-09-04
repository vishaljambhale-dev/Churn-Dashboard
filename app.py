import streamlit as st
import pandas as pd
import numpy as np

# =====================================================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# =====================================================================
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Reduce top whitespace */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    
    h1 { font-family: 'Segoe UI', sans-serif; padding-bottom: 0px; margin-bottom: 10px; color: white !important;}
    
    /* -------------------------------------------------------------
       THE BULLETPROOF CARD HACK 
       Added broader selectors to catch the side-borders safely 
    ------------------------------------------------------------- */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.fa-anchor),
    div[data-testid="stVerticalBlock"]:has(.fa-anchor) > div {
        background-color: #1A1C23 !important; 
        border: none !important;
        border-left: 4px solid #3B82F6 !important; /* FA Blue Accent */
        padding: 20px !important;
        border-radius: 6px !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.ra-anchor),
    div[data-testid="stVerticalBlock"]:has(.ra-anchor) > div {
        background-color: #1A1C23 !important; 
        border: none !important;
        border-left: 4px solid #EF4444 !important; /* RA Red Accent */
        padding: 20px !important;
        border-radius: 6px !important;
    }
    
    /* -------------------------------------------------------------
       INPUT FIELDS & BUTTON STYLING 
    ------------------------------------------------------------- */
    .stNumberInput input, .stTextInput input, .stTextArea textarea {
        color: #FFFFFF !important;
        font-weight: 600;
        background-color: #121212 !important;
        border: 1px solid #333 !important;
    }
    
    label {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #A0A0A0 !important;
        text-transform: uppercase !important;
    }
    
    /* The Navy Blue Add Button aligned with inputs */
    .stButton > button {
        height: 40px !important;
        background-color: #1D4ED8 !important; /* Navy Blue Primary Color */
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 25px !important; 
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #1E3A8A !important; /* Darker Navy on hover */
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. DATA PROCESSING & HIGH-DENSITY HTML TABLE GENERATOR
# =====================================================================
@st.cache_data
def load_lot_sizes(file):
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        if 'SYMBOL' in df.columns:
            df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip()
            lot_cols = [col for col in df.columns if '26' in col or '27' in col]
            if lot_cols:
                lot_col = lot_cols[0] 
                df[lot_col] = pd.to_numeric(df[lot_col], errors='coerce').fillna(0)
                return dict(zip(df['SYMBOL'], df[lot_col]))
    except Exception:
        pass
    return {}

@st.cache_data
def load_trade_data(file):
    return pd.read_excel(file, sheet_name=0)

def parse_excel_paste(raw_text):
    if not raw_text.strip():
        return False, "No data found."
    lines = raw_text.strip().split('\n')
    rows = []
    for line in lines:
        parts = line.split('\t')
        if len(parts) < 2: parts = line.split() 
        if len(parts) >= 2:
            sym = parts[0].strip().upper()
            try:
                qty = float(parts[-1].replace(',', '').strip())
                if sym: rows.append({"NSE Symbol": sym, "Quantity": qty})
            except ValueError:
                continue
    if rows:
        return True, rows
    return False, "Unable to read format."

def generate_html_table(df):
    """Generates a hyper-dense, non-scrollable HTML table with prominent headers."""
    if 'Lot Size' not in df.columns: df['Lot Size'] = 0
    df['Total Lots'] = np.where(df['Lot Size'] > 0, np.floor(df['Quantity'] / df['Lot Size']), 0)
    
    html = '<div style="margin-bottom: 25px;">'
    # Reduced font-size to 11px for maximum density
    html += '<table style="width: 100%; border-collapse: collapse; font-size: 11px; color: #E0E0E0; font-family: \'Segoe UI\', sans-serif;">'
    
    # Prominent Header Row
    html += '<thead style="background-color: #2D303E; border-bottom: 2px solid #555;"><tr>'
    html += '<th style="text-align: left; padding: 6px 6px; font-weight: 700; color: #FFFFFF; width: 40%;">NSE Symbol</th>'
    html += '<th style="text-align: right; padding: 6px 6px; font-weight: 700; color: #FFFFFF; width: 20%;">Quantity</th>'
    html += '<th style="text-align: right; padding: 6px 6px; font-weight: 700; color: #FFFFFF; width: 20%;">Lot Size</th>'
    html += '<th style="text-align: right; padding: 6px 6px; font-weight: 700; color: #FFFFFF; width: 20%;">Total Lots</th>'
    html += '</tr></thead><tbody>'
    
    # Rows with Zebra Striping and extremely tight padding
    for i, row in df.iterrows():
        bg_color = "#1A1C23" if i % 2 == 0 else "#22242C"
        html += f'<tr style="background-color: {bg_color}; border-bottom: 1px solid #2A2C35;">'
        html += f'<td style="text-align: left; padding: 2px 6px; font-weight: 500;">{row.get("NSE Symbol", "")}</td>'
        html += f'<td style="text-align: right; padding: 2px 6px;">{row.get("Quantity", 0):g}</td>'
        html += f'<td style="text-align: right; padding: 2px 6px;">{row.get("Lot Size", 0):g}</td>'
        html += f'<td style="text-align: right; padding: 2px 6px;">{int(row.get("Total Lots", 0))}</td>'
        html += '</tr>'
        
    html += '</tbody></table></div>'
    return html

# Initialize Global Session States
if 'fa_booted' not in st.session_state:
    st.session_state.update({'fa_booted': False, 'fa_repo': pd.DataFrame(), 'fa_sym': "", 'fa_qty': 0.0, 'fa_lot_str': ""})
if 'ra_booted' not in st.session_state:
    st.session_state.update({'ra_booted': False, 'ra_repo': pd.DataFrame(), 'ra_sym': "", 'ra_qty': 0.0, 'ra_lot_str': ""})

# =====================================================================
# 3. SIDEBAR & FILE LOADING
# =====================================================================
with st.sidebar:
    st.markdown("## Trading Setup")
    master_file = st.file_uploader("Drop 'NSE Master Lot Size File' here", type=['csv'])
    lot_dict = load_lot_sizes(master_file) if master_file else {}
    st.divider()
    st.markdown("<div style='text-align:center; font-size: 11px; color:#A0A0A0;'>Churn Dashboard v7.0</div>", unsafe_allow_html=True)

# Callbacks for Batch Processing
def process_fa_batch():
    raw = st.session_state.fa_init_box
    success, res = parse_excel_paste(raw)
    if success:
        df = pd.DataFrame(res)
        df['Lot Size'] = df['NSE Symbol'].map(lot_dict).fillna(0)
        st.session_state['fa_repo'] = df
        st.session_state['fa_booted'] = True
        st.toast(f"✅ Success! Loaded {len(res)} FA entries.", icon="✅")
    else:
        st.toast(f"❌ Error: {res}", icon="❌")

def process_ra_batch():
    raw = st.session_state.ra_init_box
    success, res = parse_excel_paste(raw)
    if success:
        df = pd.DataFrame(res)
        df['Lot Size'] = df['NSE Symbol'].map(lot_dict).fillna(0)
        st.session_state['ra_repo'] = df
        st.session_state['ra_booted'] = True
        st.toast(f"✅ Success! Loaded {len(res)} RA entries.", icon="✅")
    else:
        st.toast(f"❌ Error: {res}", icon="❌")

# Callbacks for Single Entries
def add_fa_single():
    sym = st.session_state.fa_sym.strip().upper()
    qty = float(st.session_state.fa_qty)
    lot_str = st.session_state.fa_lot_str
    lot = float(lot_str) if lot_str.replace('.','',1).isdigit() else lot_dict.get(sym, 0)
    
    if sym and qty > 0 and lot > 0:
        new_row = pd.DataFrame([{"NSE Symbol": sym, "Quantity": qty, "Lot Size": lot}])
        st.session_state['fa_repo'] = pd.concat([st.session_state['fa_repo'], new_row], ignore_index=True)
        st.session_state.fa_sym = ""
        st.session_state.fa_qty = 0.0
        st.session_state.fa_lot_str = ""

def add_ra_single():
    sym = st.session_state.ra_sym.strip().upper()
    qty = float(st.session_state.ra_qty)
    lot_str = st.session_state.ra_lot_str
    lot = float(lot_str) if lot_str.replace('.','',1).isdigit() else lot_dict.get(sym, 0)
    
    if sym and qty > 0 and lot > 0:
        new_row = pd.DataFrame([{"NSE Symbol": sym, "Quantity": qty, "Lot Size": lot}])
        st.session_state['ra_repo'] = pd.concat([st.session_state['ra_repo'], new_row], ignore_index=True)
        st.session_state.ra_sym = ""
        st.session_state.ra_qty = 0.0
        st.session_state.ra_lot_str = ""

# =====================================================================
# 4. MAIN DASHBOARD UI
# =====================================================================
st.title("Dashboard")
tab1, tab2 = st.tabs(["Trade Details", "Order Repository"])

with tab1:
    pos_file = st.file_uploader("Drag and drop Net Position here to update execution view.", type=['xlsx', 'xls'])
    if pos_file:
        df = load_trade_data(pos_file)
        st.markdown("### Consolidated Summary")
        if "Strategy" in df.columns:
            summary = df.groupby('Strategy').agg(Qty=('BuyQty', 'sum'), Value=('BuyValue', 'sum')).reset_index()
            if 'BPS' in df.columns:
                bps_mean = df.groupby('Strategy')['BPS'].mean().reset_index()
                summary = pd.merge(summary, bps_mean, on='Strategy', how='left')
            else: summary['BPS'] = 0.0
            summary['Value (Cr)'] = summary['Value'] / 10000000
            summary['Value (USD - Mil)'] = summary['Value (Cr)'] / 8.6
            summary = summary[['Strategy', 'Qty', 'Value', 'Value (Cr)', 'Value (USD - Mil)', 'BPS']]
            st.dataframe(summary.style.format({'Value': "{:,.2f}", 'Value (Cr)': "{:.2f}", 'Value (USD - Mil)': "{:.2f}", 'BPS': "{:.6f}"}), use_container_width=True)

        st.markdown("### Detailed Trade Execution View")
        cols_to_keep = ['ClientCode', 'Strategy', 'Symbol', 'Buy_Month', 'BuyQty', 'BuyLot', 'Buypx', 'BuyValue', 'Sell_Month', 'SellQty', 'SellLot', 'Sellpx', 'SellValue', 'Div', 'BPS', 'Tally']
        display_df = df[[c for c in cols_to_keep if c in df.columns]]
        st.dataframe(display_df, use_container_width=True)

with tab2:
    col_fa, col_ra = st.columns(2)
    
    # --- FRESH ARBITRAGE (FA) CARD ---
    with col_fa:
        fa_card = st.container(border=True)
        with fa_card:
            st.markdown("<div class='fa-anchor'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: white; font-size:18px; font-weight: 600; margin-bottom: 20px;'>Fresh Arbitrage (FA)</h3>", unsafe_allow_html=True)
            
            if not st.session_state['fa_booted']:
                st.text_area("Paste Excel Batch (Symbol & Quantity)", height=150, key="fa_init_box", placeholder="ABB\t13455\nADANIENSOL\t72166...")
                st.button("Process Initial FA Batch", use_container_width=True, on_click=process_fa_batch)
            
            else:
                fa_display = st.session_state['fa_repo'].copy()
                st.markdown(generate_html_table(fa_display), unsafe_allow_html=True)
                
                st.markdown("<span style='font-size: 13px; color: #3B82F6; font-weight:bold;'>+ Add New Entry</span>", unsafe_allow_html=True)
                
                f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([2.5, 1.5, 1.2, 1, 1.2])
                
                sym_val = f_c1.text_input("SYMBOL", key="fa_sym", placeholder="Search...").strip().upper()
                qty_val = f_c2.number_input("QUANTITY", min_value=0.0, step=1.0, key="fa_qty")
                
                auto_lot = lot_dict.get(sym_val, "") if sym_val else ""
                lot_str = f_c3.text_input("LOT SIZE", value=str(int(auto_lot)) if auto_lot else "", placeholder="Auto", key="fa_lot_str")
                
                lot_val = float(lot_str) if lot_str.replace('.','',1).isdigit() else 0
                calc_lots = int(np.floor(qty_val / lot_val)) if lot_val > 0 else 0
                
                f_c4.markdown(f"<div style='font-size:11px; font-weight:600; color:#A0A0A0; margin-bottom:5px; margin-top:2px;'>TOTAL LOTS</div><div style='color:white; font-weight:bold; font-size: 16px; margin-top: 10px;'>{calc_lots}</div>", unsafe_allow_html=True)
                
                f_c5.button("Add", key="fa_add_btn", on_click=add_fa_single, use_container_width=True)

    # --- REVERSE ARBITRAGE (RA) CARD ---
    with col_ra:
        ra_card = st.container(border=True)
        with ra_card:
            st.markdown("<div class='ra-anchor'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: white; font-size:18px; font-weight: 600; margin-bottom: 20px;'>Reverse Arbitrage (RA)</h3>", unsafe_allow_html=True)
            
            if not st.session_state['ra_booted']:
                st.text_area("Paste Excel Batch (Symbol & Quantity)", height=150, key="ra_init_box", placeholder="ALKEM\t6744\nASHOKLEY\t152750...")
                st.button("Process Initial RA Batch", use_container_width=True, on_click=process_ra_batch)
            
            else:
                ra_display = st.session_state['ra_repo'].copy()
                st.markdown(generate_html_table(ra_display), unsafe_allow_html=True)
                
                st.markdown("<span style='font-size: 13px; color: #EF4444; font-weight:bold;'>+ Add New Entry</span>", unsafe_allow_html=True)
                
                r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([2.5, 1.5, 1.2, 1, 1.2])
                
                rsym_val = r_c1.text_input("SYMBOL", key="ra_sym", placeholder="Search...").strip().upper()
                rqty_val = r_c2.number_input("QUANTITY", min_value=0.0, step=1.0, key="ra_qty")
                
                r_auto_lot = lot_dict.get(rsym_val, "") if rsym_val else ""
                rlot_str = r_c3.text_input("LOT SIZE", value=str(int(r_auto_lot)) if r_auto_lot else "", placeholder="Auto", key="ra_lot_str")
                
                rlot_val = float(rlot_str) if rlot_str.replace('.','',1).isdigit() else 0
                rcalc_lots = int(np.floor(rqty_val / rlot_val)) if rlot_val > 0 else 0
                
                r_c4.markdown(f"<div style='font-size:11px; font-weight:600; color:#A0A0A0; margin-bottom:5px; margin-top:2px;'>TOTAL LOTS</div><div style='color:white; font-weight:bold; font-size: 16px; margin-top: 10px;'>{rcalc_lots}</div>", unsafe_allow_html=True)
                
                r_c5.button("Add", key="ra_add_btn", on_click=add_ra_single, use_container_width=True)

# Add a massive transparent buffer at the bottom of the page to prevent "Manage app" toggle overlap
st.markdown("<div style='height: 100px; width: 100%;'></div>", unsafe_allow_html=True)
