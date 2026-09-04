import streamlit as st
import pandas as pd
import numpy as np

# =====================================================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# =====================================================================
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. Reduce top whitespace */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    h1 { font-family: 'Segoe UI', sans-serif; padding-bottom: 0px; margin-bottom: 5px; }
    h3 { font-family: 'Segoe UI', sans-serif; font-size: 20px !important; color: white !important; margin-top: 0px !important; }
    
    /* 2. THE TRUE CARD HACK: Target the outer layout columns to act as unified cards */
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(1) {
        background-color: #1E1E1E !important;
        border-left: 4px solid #3B82F6 !important;
        padding: 20px 20px 30px 20px !important;
        border-radius: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(2) {
        background-color: #1E1E1E !important;
        border-left: 4px solid #EF4444 !important;
        padding: 20px 20px 30px 20px !important;
        border-radius: 6px !important;
    }

    /* Prevent inner form columns from inheriting the card border */
    div[data-testid="column"] div[data-testid="column"] {
        border-left: none !important;
        background-color: transparent !important;
        padding: 0px !important;
    }

    /* 3. Fully Expanding Tables (Remove inner scrolling) */
    [data-testid="stDataFrame"] > div > div {
        max-height: none !important;
        height: auto !important;
    }
    [data-testid="stDataFrame"] { height: auto !important; }
    
    /* Force Data Editor Alignment */
    [data-testid="stDataFrame"] td { text-align: right !important; }
    [data-testid="stDataFrame"] td:nth-child(2) { text-align: left !important; } 
    
    /* 4. Input Fields & Buttons */
    .stNumberInput input, .stTextInput input {
        color: #FFFFFF !important;
        font-weight: 600;
        background-color: #121212 !important;
        border: 1px solid #333 !important;
    }
    
    .stButton > button {
        height: 42px !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 28px !important; 
    }
    
    /* FA Button Color */
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(1) .stButton > button {
        background-color: #3B82F6 !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(1) .stButton > button:hover {
        background-color: #2563EB !important;
    }
    
    /* RA Button Color */
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(2) .stButton > button {
        background-color: #EF4444 !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(2) .stButton > button:hover {
        background-color: #DC2626 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. DATA PROCESSING & PARSING FUNCTIONS
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

if 'fa_booted' not in st.session_state:
    st.session_state['fa_booted'] = False
    st.session_state['fa_repo'] = pd.DataFrame(columns=["NSE Symbol", "Quantity"])
if 'ra_booted' not in st.session_state:
    st.session_state['ra_booted'] = False
    st.session_state['ra_repo'] = pd.DataFrame(columns=["NSE Symbol", "Quantity"])

# =====================================================================
# 3. SIDEBAR (SETUP)
# =====================================================================
with st.sidebar:
    st.markdown("## Trading Setup")
    master_file = st.file_uploader("Drop 'NSE Master Lot Size File' here", type=['csv'])
    lot_dict = load_lot_sizes(master_file) if master_file else {}
    st.divider()
    st.markdown("<div style='text-align:center; font-size: 11px; color:#A0A0A0;'>Churn Dashboard v2.0</div>", unsafe_allow_html=True)

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
            else:
                summary['BPS'] = 0.0
            
            summary['Value (Cr)'] = summary['Value'] / 10000000
            summary['Value (USD - Mil)'] = summary['Value (Cr)'] / 8.6
            summary = summary[['Strategy', 'Qty', 'Value', 'Value (Cr)', 'Value (USD - Mil)', 'BPS']]
            st.dataframe(summary.style.format({'Value': "{:,.2f}", 'Value (Cr)': "{:.2f}", 'Value (USD - Mil)': "{:.2f}", 'BPS': "{:.6f}"}), use_container_width=True)

        st.markdown("### Detailed Trade Execution View")
        cols_to_keep = ['ClientCode', 'Strategy', 'Symbol', 'Buy_Month', 'BuyQty', 'BuyLot', 'Buypx', 'BuyValue', 'Sell_Month', 'SellQty', 'SellLot', 'Sellpx', 'SellValue', 'Div', 'BPS', 'Tally']
        display_df = df[[c for c in cols_to_keep if c in df.columns]]
        st.dataframe(display_df, use_container_width=True)

with tab2:
    # Outer block targeted by CSS for cards
    col_fa, col_ra = st.columns(2)
    
    # --- FRESH ARBITRAGE (FA) CARD ---
    with col_fa:
        st.markdown("<h3><span style='color:#3B82F6;'>Fresh Arbitrage</span> (FA)</h3>", unsafe_allow_html=True)
        
        if not st.session_state['fa_booted']:
            fa_batch_input = st.text_area("FA Initial Batch", height=180, key="fa_init_box", placeholder="Paste Excel Batch Here...\nABB\t13455\nADANIENSOL\t72166")
            if st.button("Process FA Batch", use_container_width=True):
                success, result = parse_excel_paste(fa_batch_input)
                if success:
                    st.session_state['fa_repo'] = pd.DataFrame(result)
                    st.session_state['fa_booted'] = True
                    st.toast(f"✅ Success! Loaded {len(result)} FA entries.", icon='✅')
                    st.rerun()
                else:
                    st.toast(f"❌ Error: {result}", icon='❌')
        else:
            fa_display = st.session_state['fa_repo'].copy()
            fa_display['NSE Symbol'] = fa_display['NSE Symbol'].astype(str).str.strip().str.upper()
            fa_display['Lot Size'] = fa_display['NSE Symbol'].map(lot_dict).fillna(0)
            
            temp_qty = pd.to_numeric(fa_display['Quantity'], errors='coerce').fillna(0)
            fa_display['Total Lots'] = np.where(fa_display['Lot Size'] > 0, temp_qty / fa_display['Lot Size'], 0).round(2)
            
            # Dynamic height calculation to force table to expand
            table_height = (len(fa_display) * 36) + 40
            
            edited_fa = st.data_editor(
                fa_display,
                disabled=["Lot Size", "Total Lots"], 
                use_container_width=True,
                height=max(table_height, 150),
                num_rows="dynamic",
                key="fa_editor",
                hide_index=True
            )
            st.session_state['fa_repo'] = edited_fa[['NSE Symbol', 'Quantity']]
            
            st.markdown("<br><span style='font-size: 13px; color: #3B82F6; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
            
            f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([2.5, 1, 1.5, 1.2, 1.2])
            with f_c1: new_fa_sym = st.text_input("SYMBOL", key="fa_sym", placeholder="Search...").strip().upper()
            with f_c2:
                auto_lot_fa = lot_dict.get(new_fa_sym, 0) if new_fa_sym else 0
                fa_lot = st.text_input("LOT SIZE", value=str(int(auto_lot_fa)) if auto_lot_fa > 0 else "Auto", disabled=True, key="fa_lot_input")
            with f_c3: fa_qty = st.text_input("QUANTITY", value="0", key="fa_qty_input")
            with f_c4:
                st.markdown("<div style='font-size:11px; font-weight:600; color:#A0A0A0; margin-bottom:12px; margin-top:5px;'>TOTAL LOTS</div>", unsafe_allow_html=True)
                try:
                    calc_fa = (float(fa_qty) / auto_lot_fa) if auto_lot_fa > 0 else 0
                except ValueError:
                    calc_fa = 0
                st.markdown(f"<div style='color:white; font-weight:bold; font-size: 18px; margin-top: 8px;'>{calc_fa:.2f}</div>", unsafe_allow_html=True)
            with f_c5:    
                if st.button("Add", key="fa_single_add", use_container_width=True):
                    if new_fa_sym:
                        new_row = pd.DataFrame([{"NSE Symbol": new_fa_sym, "Quantity": float(fa_qty)}])
                        st.session_state['fa_repo'] = pd.concat([st.session_state['fa_repo'], new_row], ignore_index=True)
                        st.rerun()

    # --- REVERSE ARBITRAGE (RA) CARD ---
    with col_ra:
        st.markdown("<h3><span style='color:#EF4444;'>Reverse Arbitrage</span> (RA)</h3>", unsafe_allow_html=True)
        
        if not st.session_state['ra_booted']:
            ra_batch_input = st.text_area("RA Initial Batch", height=180, key="ra_init_box", placeholder="Paste Excel Batch Here...\nADANIENSOL\t72359\nALKEM\t18868")
            if st.button("Process RA Batch", use_container_width=True):
                success, result = parse_excel_paste(ra_batch_input)
                if success:
                    st.session_state['ra_repo'] = pd.DataFrame(result)
                    st.session_state['ra_booted'] = True
                    st.toast(f"✅ Success! Loaded {len(result)} RA entries.", icon='✅')
                    st.rerun()
                else:
                    st.toast(f"❌ Error: {result}", icon='❌')
        else:
            ra_display = st.session_state['ra_repo'].copy()
            ra_display['NSE Symbol'] = ra_display['NSE Symbol'].astype(str).str.strip().str.upper()
            ra_display['Lot Size'] = ra_display['NSE Symbol'].map(lot_dict).fillna(0)
            
            temp_qty_ra = pd.to_numeric(ra_display['Quantity'], errors='coerce').fillna(0)
            ra_display['Total Lots'] = np.where(ra_display['Lot Size'] > 0, temp_qty_ra / ra_display['Lot Size'], 0).round(2)
            
            # Dynamic height calculation
            table_height_ra = (len(ra_display) * 36) + 40
            
            edited_ra = st.data_editor(
                ra_display,
                disabled=["Lot Size", "Total Lots"],
                use_container_width=True,
                height=max(table_height_ra, 150),
                num_rows="dynamic",
                key="ra_editor",
                hide_index=True
            )
            st.session_state['ra_repo'] = edited_ra[['NSE Symbol', 'Quantity']]
            
            st.markdown("<br><span style='font-size: 13px; color: #EF4444; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
            
            r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([2.5, 1, 1.5, 1.2, 1.2])
            with r_c1: new_ra_sym = st.text_input("SYMBOL", key="ra_sym", placeholder="Search...").strip().upper()
            with r_c2:
                auto_lot_ra = lot_dict.get(new_ra_sym, 0) if new_ra_sym else 0
                ra_lot = st.text_input("LOT SIZE", value=str(int(auto_lot_ra)) if auto_lot_ra > 0 else "Auto", disabled=True, key="ra_lot_input")
            with r_c3: ra_qty = st.text_input("QUANTITY", value="0", key="ra_qty_input")
            with r_c4:
                st.markdown("<div style='font-size:11px; font-weight:600; color:#A0A0A0; margin-bottom:12px; margin-top:5px;'>TOTAL LOTS</div>", unsafe_allow_html=True)
                try:
                    calc_ra = (float(ra_qty) / auto_lot_ra) if auto_lot_ra > 0 else 0
                except ValueError:
                    calc_ra = 0
                st.markdown(f"<div style='color:white; font-weight:bold; font-size: 18px; margin-top: 8px;'>{calc_ra:.2f}</div>", unsafe_allow_html=True)
            with r_c5:
                if st.button("Add", key="ra_single_add", use_container_width=True):
                    if new_ra_sym:
                        new_row = pd.DataFrame([{"NSE Symbol": new_ra_sym, "Quantity": float(ra_qty)}])
                        st.session_state['ra_repo'] = pd.concat([st.session_state['ra_repo'], new_row], ignore_index=True)
                        st.rerun()
