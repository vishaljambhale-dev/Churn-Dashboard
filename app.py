import streamlit as st
import pandas as pd
import numpy as np

# =====================================================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# =====================================================================
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS for Side Accents, White text overrides, and hiding elements
st.markdown("""
    <style>
    /* Side Accents for FA and RA columns */
    [data-testid="column"]:nth-of-type(1) {
        border-left: 4px solid #3B82F6; /* FA Institutional Blue */
        padding-left: 15px;
        background-color: #1E1E1E;
        border-radius: 4px;
        padding: 15px;
    }
    [data-testid="column"]:nth-of-type(2) {
        border-left: 4px solid #EF4444; /* RA Vibrant Red */
        padding-left: 15px;
        background-color: #1E1E1E;
        border-radius: 4px;
        padding: 15px;
    }
    
    /* Force Quantity editable text to be strictly white */
    .stNumberInput input {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    
    /* Clean up headers */
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
    
    /* Hide row indices in dataframes */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. DATA PROCESSING FUNCTIONS
# =====================================================================
@st.cache_data
def load_lot_sizes(file):
    """Parses the NSE Master Lot Size CSV to create a lookup dictionary."""
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    if 'SYMBOL' in df.columns:
        df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip()
        # Find the first column that looks like a date (e.g., SEP-26) to extract lot size
        lot_cols = [col for col in df.columns if '26' in col or '27' in col]
        if lot_cols:
            lot_col = lot_cols[0] 
            df[lot_col] = pd.to_numeric(df[lot_col], errors='coerce').fillna(0)
            return dict(zip(df['SYMBOL'], df[lot_col]))
    return {}

@st.cache_data
def load_trade_data(file):
    return pd.read_excel(file, sheet_name=0)

# Initialize Session States for Repositories as BLANK SLATES
if 'fa_repo' not in st.session_state:
    st.session_state['fa_repo'] = pd.DataFrame(columns=["NSE Symbol", "Quantity"])
if 'ra_repo' not in st.session_state:
    st.session_state['ra_repo'] = pd.DataFrame(columns=["NSE Symbol", "Quantity"])

# =====================================================================
# 3. SIDEBAR (SETUP)
# =====================================================================
with st.sidebar:
    st.markdown("## Trading Setup")
    master_file = st.file_uploader("Drop 'NSE Master Lot Size File' here", type=['csv'])
    
    # Load dictionary if file uploaded, else empty
    lot_dict = load_lot_sizes(master_file) if master_file else {}
    
    st.divider()
    st.markdown("<div style='text-align:center; font-size: 11px; color:#A0A0A0;'>Churn Dashboard v1.0</div>", unsafe_allow_html=True)

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
            # Aggregate logic based on Net Position Data
            summary = df.groupby('Strategy').agg(
                Qty=('BuyQty', 'sum'),
                Value=('BuyValue', 'sum')
            ).reset_index()
            
            if 'BPS' in df.columns:
                bps_mean = df.groupby('Strategy')['BPS'].mean().reset_index()
                summary = pd.merge(summary, bps_mean, on='Strategy', how='left')
            else:
                summary['BPS'] = 0.0
            
            # Math: Calculate Cr and USD Mil
            summary['Value (Cr)'] = summary['Value'] / 10000000
            summary['Value (USD - Mil)'] = summary['Value (Cr)'] / 8.6
            
            # Reorder columns for display
            summary = summary[['Strategy', 'Qty', 'Value', 'Value (Cr)', 'Value (USD - Mil)', 'BPS']]
            st.dataframe(summary.style.format({
                'Value': "{:,.2f}", 'Value (Cr)': "{:.2f}", 'Value (USD - Mil)': "{:.2f}", 'BPS': "{:.6f}"
            }), use_container_width=True)

        st.markdown("### Detailed Trade Execution View")
        # Extracting specific columns based on your provided format
        cols_to_keep = ['ClientCode', 'Strategy', 'Symbol', 'Buy_Month', 'BuyQty', 'BuyLot', 'Buypx', 'BuyValue', 'Sell_Month', 'SellQty', 'SellLot', 'Sellpx', 'SellValue', 'Div', 'BPS', 'Tally']
        display_df = df[[c for c in cols_to_keep if c in df.columns]]
        st.dataframe(display_df, use_container_width=True)

# ---------------------------------------------------------------------
# TAB 2: ORDER REPOSITORY (FA vs RA)
# ---------------------------------------------------------------------
with tab2:
    st.info("💡 **Tip:** You can click inside the empty table rows and paste a batch of *Symbols* and *Quantities* directly from Excel.")
    col_fa, col_ra = st.columns(2)
    
    # --- FRESH ARBITRAGE (FA) SECTION ---
    with col_fa:
        st.markdown("<h3 style='color: #3B82F6;'>Fresh Arbitrage (FA)</h3>", unsafe_allow_html=True)
        
        # Calculate Lot Size and Total Lots dynamically for display
        fa_display = st.session_state['fa_repo'].copy()
        fa_display['Lot Size'] = fa_display['NSE Symbol'].map(lot_dict).fillna(0)
        # Avoid division by zero
        fa_display['Total Lots'] = np.where(fa_display['Lot Size'] > 0, fa_display['Quantity'] / fa_display['Lot Size'], 0).round(2)
        
        # Dynamic Dataframe - Allows adding rows & pasting from excel
        edited_fa = st.data_editor(
            fa_display,
            disabled=["Lot Size", "Total Lots"], 
            use_container_width=True,
            num_rows="dynamic",
            key="fa_editor",
            hide_index=True
        )
        # Save edits back to session state
        st.session_state['fa_repo'] = edited_fa[['NSE Symbol', 'Quantity']].dropna(subset=['NSE Symbol'])
        
        st.divider()
        st.markdown("<span style='font-size: 12px; color: #3B82F6; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
        
        f_c1, f_c2, f_c3, f_c4 = st.columns([2, 1, 1.5, 1])
        with f_c1: new_fa_sym = st.text_input("Symbol", key="fa_sym").strip().upper()
        with f_c2:
            auto_lot_fa = lot_dict.get(new_fa_sym, 0) if new_fa_sym else 0
            fa_lot = st.number_input("Lot", value=int(auto_lot_fa), disabled=(auto_lot_fa > 0), key="fa_lot_input")
        with f_c3: fa_qty = st.number_input("Quantity", min_value=0, key="fa_qty_input")
        with f_c4:
            st.markdown("<div style='font-size:11px; font-weight:600; color:#A0A0A0; margin-bottom:5px;'>TOTAL LOTS</div>", unsafe_allow_html=True)
            calc_fa = (fa_qty / fa_lot) if fa_lot > 0 else 0
            st.markdown(f"<div style='color:white; font-weight:bold; text-align:right;'>{calc_fa:.2f}</div>", unsafe_allow_html=True)
            
        if st.button("Add", key="fa_add", use_container_width=True):
            if new_fa_sym:
                new_row = pd.DataFrame([{"NSE Symbol": new_fa_sym, "Quantity": fa_qty}])
                st.session_state['fa_repo'] = pd.concat([st.session_state['fa_repo'], new_row], ignore_index=True)
                st.rerun()

    # --- REVERSE ARBITRAGE (RA) SECTION ---
    with col_ra:
        st.markdown("<h3 style='color: #EF4444;'>Reverse Arbitrage (RA)</h3>", unsafe_allow_html=True)
        
        # Calculate Lot Size and Total Lots dynamically
        ra_display = st.session_state['ra_repo'].copy()
        ra_display['Lot Size'] = ra_display['NSE Symbol'].map(lot_dict).fillna(0)
        ra_display['Total Lots'] = np.where(ra_display['Lot Size'] > 0, ra_display['Quantity'] / ra_display['Lot Size'], 0).round(2)
        
        edited_ra = st.data_editor(
            ra_display,
            disabled=["Lot Size", "Total Lots"],
            use_container_width=True,
            num_rows="dynamic",
            key="ra_editor",
            hide_index=True
        )
        st.session_state['ra_repo'] = edited_ra[['NSE Symbol', 'Quantity']].dropna(subset=['NSE Symbol'])
        
        st.divider()
        st.markdown("<span style='font-size: 12px; color: #EF4444; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
        
        r_c1, r_c2, r_c3, r_c4 = st.columns([2, 1, 1.5, 1])
        with r_c1: new_ra_sym = st.text_input("Symbol", key="ra_sym").strip().upper()
        with r_c2:
            auto_lot_ra = lot_dict.get(new_ra_sym, 0) if new_ra_sym else 0
            ra_lot = st.number_input("Lot", value=int(auto_lot_ra), disabled=(auto_lot_ra > 0), key="ra_lot_input")
        with r_c3: ra_qty = st.number_input("Quantity", min_value=0, key="ra_qty_input")
        with r_c4:
            st.markdown("<div style='font-size:11px; font-weight:600; color:#A0A0A0; margin-bottom:5px;'>TOTAL LOTS</div>", unsafe_allow_html=True)
            calc_ra = (ra_qty / ra_lot) if ra_lot > 0 else 0
            st.markdown(f"<div style='color:white; font-weight:bold; text-align:right;'>{calc_ra:.2f}</div>", unsafe_allow_html=True)
            
        if st.button("Add", key="ra_add", use_container_width=True):
            if new_ra_sym:
                new_row = pd.DataFrame([{"NSE Symbol": new_ra_sym, "Quantity": ra_qty}])
                st.session_state['ra_repo'] = pd.concat([st.session_state['ra_repo'], new_row], ignore_index=True)
                st.rerun()
