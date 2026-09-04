import streamlit as st
import pandas as pd
import numpy as np

# =====================================================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# =====================================================================
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS to force Streamlit to look exactly like the mockup
st.markdown("""
    <style>
    /* Reduce massive top whitespace */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Clean up headers */
    h1 { font-family: 'Segoe UI', sans-serif; padding-bottom: 0px; margin-bottom: 0px; }
    h2, h3 { font-family: 'Segoe UI', sans-serif; }
    
    /* Force Quantity editable text to be strictly white */
    .stNumberInput input, .stTextInput input {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    
    /* Hide row indices in dataframes */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
    /* Force Data Editor Alignment */
    [data-testid="stDataFrame"] td { text-align: right !important; }
    [data-testid="stDataFrame"] td:nth-child(2) { text-align: left !important; } 
    
    /* Style the massive Add Button */
    .stButton > button {
        height: 42px !important;
        background-color: #3B82F6 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 28px !important; /* Align with inputs */
    }
    .stButton > button:hover {
        background-color: #2563EB !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. DATA PROCESSING FUNCTIONS
# =====================================================================
@st.cache_data
def load_lot_sizes(file):
    """Parses the NSE Master Lot Size CSV to create a lookup dictionary."""
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

# Initialize Session States for Repositories as STRICT BLANK SLATES
# By keeping everything as empty strings, Excel block pasting works natively.
def get_blank_repo():
    df = pd.DataFrame({
        "NSE Symbol": ["", "", "", "", ""],
        "Quantity": ["", "", "", "", ""] 
    })
    return df

if 'fa_repo' not in st.session_state:
    st.session_state['fa_repo'] = get_blank_repo()
if 'ra_repo' not in st.session_state:
    st.session_state['ra_repo'] = get_blank_repo()

# =====================================================================
# 3. SIDEBAR (SETUP)
# =====================================================================
with st.sidebar:
    st.markdown("## Trading Setup")
    master_file = st.file_uploader("Drop 'NSE Master Lot Size File' here", type=['csv'])
    lot_dict = load_lot_sizes(master_file) if master_file else {}
    st.divider()
    st.markdown("<div style='text-align:center; font-size: 11px; color:#A0A0A0;'>Churn Dashboard v1.1</div>", unsafe_allow_html=True)

# =====================================================================
# 4. MAIN DASHBOARD UI
# =====================================================================
st.title("Dashboard")
tab1, tab2 = st.tabs(["Trade Details", "Order Repository"])

# ---------------------------------------------------------------------
# TAB 1: TRADE DETAILS DASHBOARD
# ---------------------------------------------------------------------
with tab1:
    pos_file = st.file_uploader("Drag and drop Net Position here to update execution view.", type=['xlsx', 'xls'])
    if pos_file:
        df = load_trade_data(pos_file)
        st.markdown("### Consolidated Summary")
        if "Strategy" in df.columns:
            summary = df.groupby('Strategy').agg(
                Qty=('BuyQty', 'sum'),
                Value=('BuyValue', 'sum')
            ).reset_index()
            if 'BPS' in df.columns:
                bps_mean = df.groupby('Strategy')['BPS'].mean().reset_index()
                summary = pd.merge(summary, bps_mean, on='Strategy', how='left')
            else:
                summary['BPS'] = 0.0
            
            summary['Value (Cr)'] = summary['Value'] / 10000000
            summary['Value (USD - Mil)'] = summary['Value (Cr)'] / 8.6
            summary = summary[['Strategy', 'Qty', 'Value', 'Value (Cr)', 'Value (USD - Mil)', 'BPS']]
            st.dataframe(summary.style.format({
                'Value': "{:,.2f}", 'Value (Cr)': "{:.2f}", 'Value (USD - Mil)': "{:.2f}", 'BPS': "{:.6f}"
            }), use_container_width=True)

        st.markdown("### Detailed Trade Execution View")
        cols_to_keep = ['ClientCode', 'Strategy', 'Symbol', 'Buy_Month', 'BuyQty', 'BuyLot', 'Buypx', 'BuyValue', 'Sell_Month', 'SellQty', 'SellLot', 'Sellpx', 'SellValue', 'Div', 'BPS', 'Tally']
        display_df = df[[c for c in cols_to_keep if c in df.columns]]
        st.dataframe(display_df, use_container_width=True)

# ---------------------------------------------------------------------
# TAB 2: ORDER REPOSITORY (FA vs RA)
# ---------------------------------------------------------------------
with tab2:
    st.info("💡 **Tip:** Click inside the empty table rows below and press **Ctrl+V / Cmd+V** to paste a batch of *Symbols* and *Quantities* directly from Excel.")
    col_fa, col_ra = st.columns(2)
    
    # --- FRESH ARBITRAGE (FA) SECTION ---
    with col_fa:
        # Wrap everything in a simulated HTML "Card" with the Blue Side Accent
        st.markdown("""
        <div style='border-left: 4px solid #3B82F6; background-color: #1E1E1E; padding: 20px; border-radius: 4px;'>
            <h3 style='color: white; margin-top: 0px;'>Fresh Arbitrage (FA)</h3>
        </div>
        """, unsafe_allow_html=True)
        
        fa_display = st.session_state['fa_repo'].copy()
        
        # Safe calculations allowing for empty strings
        fa_display['NSE Symbol'] = fa_display['NSE Symbol'].astype(str).str.strip().str.upper()
        fa_display['Lot Size'] = fa_display['NSE Symbol'].map(lot_dict).fillna(0)
        
        # Convert Quantity to numeric purely for math, leave original for display safety
        temp_qty = pd.to_numeric(fa_display['Quantity'], errors='coerce').fillna(0)
        fa_display['Total Lots'] = np.where(fa_display['Lot Size'] > 0, temp_qty / fa_display['Lot Size'], 0).round(2)
        
        # Render Table
        edited_fa = st.data_editor(
            fa_display,
            disabled=["Lot Size", "Total Lots"], 
            use_container_width=True,
            num_rows="dynamic",
            key="fa_editor",
            hide_index=True
        )
        # Save edits back to session state
        st.session_state['fa_repo'] = edited_fa[['NSE Symbol', 'Quantity']]
        
        st.markdown("<br><span style='font-size: 13px; color: #A0A0A0; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
        
        # Form layout matching the mockup
        f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([2.5, 1, 1.5, 1.2, 1])
        with f_c1: new_fa_sym = st.text_input("SYMBOL", key="fa_sym", placeholder="Search...").strip().upper()
        with f_c2:
            auto_lot_fa = lot_dict.get(new_fa_sym, 0) if new_fa_sym else 0
            fa_lot = st.text_input("LOT SIZE", value=str(int(auto_lot_fa)) if auto_lot_fa > 0 else "Auto", disabled=True, key="fa_lot_input")
        with f_c3: fa_qty = st.text_input("QUANTITY", value="0", key="fa_qty_input")
        with f_c4:
            st.markdown("<div style='font-size:12px; font-weight:600; color:#A0A0A0; margin-bottom:12px; margin-top:5px;'>TOTAL LOTS</div>", unsafe_allow_html=True)
            try:
                calc_qty = float(fa_qty)
                calc_fa = (calc_qty / auto_lot_fa) if auto_lot_fa > 0 else 0
            except ValueError:
                calc_fa = 0
            st.markdown(f"<div style='color:white; font-weight:bold; font-size: 16px; margin-top: 8px;'>{calc_fa:.2f}</div>", unsafe_allow_html=True)
        with f_c5:    
            if st.button("Add", key="fa_add", use_container_width=True):
                if new_fa_sym:
                    new_row = pd.DataFrame([{"NSE Symbol": new_fa_sym, "Quantity": fa_qty}])
                    st.session_state['fa_repo'] = pd.concat([st.session_state['fa_repo'], new_row], ignore_index=True)
                    st.rerun()

    # --- REVERSE ARBITRAGE (RA) SECTION ---
    with col_ra:
        # Wrap everything in a simulated HTML "Card" with the Red Side Accent
        st.markdown("""
        <div style='border-left: 4px solid #EF4444; background-color: #1E1E1E; padding: 20px; border-radius: 4px;'>
            <h3 style='color: white; margin-top: 0px;'>Reverse Arbitrage (RA)</h3>
        </div>
        """, unsafe_allow_html=True)
        
        ra_display = st.session_state['ra_repo'].copy()
        
        ra_display['NSE Symbol'] = ra_display['NSE Symbol'].astype(str).str.strip().str.upper()
        ra_display['Lot Size'] = ra_display['NSE Symbol'].map(lot_dict).fillna(0)
        
        temp_qty_ra = pd.to_numeric(ra_display['Quantity'], errors='coerce').fillna(0)
        ra_display['Total Lots'] = np.where(ra_display['Lot Size'] > 0, temp_qty_ra / ra_display['Lot Size'], 0).round(2)
        
        edited_ra = st.data_editor(
            ra_display,
            disabled=["Lot Size", "Total Lots"],
            use_container_width=True,
            num_rows="dynamic",
            key="ra_editor",
            hide_index=True
        )
        st.session_state['ra_repo'] = edited_ra[['NSE Symbol', 'Quantity']]
        
        st.markdown("<br><span style='font-size: 13px; color: #A0A0A0; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
        
        r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([2.5, 1, 1.5, 1.2, 1])
        with r_c1: new_ra_sym = st.text_input("SYMBOL", key="ra_sym", placeholder="Search...").strip().upper()
        with r_c2:
            auto_lot_ra = lot_dict.get(new_ra_sym, 0) if new_ra_sym else 0
            ra_lot = st.text_input("LOT SIZE", value=str(int(auto_lot_ra)) if auto_lot_ra > 0 else "Auto", disabled=True, key="ra_lot_input")
        with r_c3: ra_qty = st.text_input("QUANTITY", value="0", key="ra_qty_input")
        with r_c4:
            st.markdown("<div style='font-size:12px; font-weight:600; color:#A0A0A0; margin-bottom:12px; margin-top:5px;'>TOTAL LOTS</div>", unsafe_allow_html=True)
            try:
                calc_qty_ra = float(ra_qty)
                calc_ra = (calc_qty_ra / auto_lot_ra) if auto_lot_ra > 0 else 0
            except ValueError:
                calc_ra = 0
            st.markdown(f"<div style='color:white; font-weight:bold; font-size: 16px; margin-top: 8px;'>{calc_ra:.2f}</div>", unsafe_allow_html=True)
            
        with r_c5:
            if st.button("Add", key="ra_add", use_container_width=True):
                if new_ra_sym:
                    new_row = pd.DataFrame([{"NSE Symbol": new_ra_sym, "Quantity": ra_qty}])
                    st.session_state['ra_repo'] = pd.concat([st.session_state['ra_repo'], new_row], ignore_index=True)
                    st.rerun()
