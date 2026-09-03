import streamlit as st
import pandas as pd

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
    # Clean whitespace from NSE column names and symbols
    df.columns = df.columns.str.strip()
    df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip()
    
    # Assuming the lot size is in the 'SEP-26' column (adjust as needed dynamically)
    lot_col = [col for col in df.columns if '26' in col or '27' in col][0] 
    
    # Create dictionary: {'NIFTY': 65, 'RELIANCE': 250}
    df[lot_col] = pd.to_numeric(df[lot_col], errors='coerce').fillna(0)
    return dict(zip(df['SYMBOL'], df[lot_col]))

@st.cache_data
def load_trade_data(file):
    return pd.read_excel(file, sheet_name='Sheet1')

# Initialize Session States for Repositories
if 'fa_repo' not in st.session_state:
    st.session_state['fa_repo'] = pd.DataFrame({"NSE Symbol": ["ABB", "ADANIGREEN", "BSE"], "Quantity": [13521, 79051, 30000], "Lot Size": [125, 600, 150]})
if 'ra_repo' not in st.session_state:
    st.session_state['ra_repo'] = pd.DataFrame({"NSE Symbol": ["ADANIENSOL", "ALKEM"], "Quantity": [72359, 18868], "Lot Size": [675, 125]})

# =====================================================================
# 3. SIDEBAR (SETUP)
# =====================================================================
with st.sidebar:
    st.markdown("## Trading Setup")
    st.markdown("<span style='font-size: 12px; color: #A0A0A0; font-weight: bold;'>NSE MASTER LOT SIZE</span>", unsafe_allow_html=True)
    master_file = st.file_uploader("Drop 'fo_mktlots.csv' here", type=['csv'])
    
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
            # Aggregate logic
            summary = df.groupby('Strategy').agg(
                Qty=('BuyQty', 'sum'),
                Value=('BuyValue', 'sum'),
                BPS=('BPS', 'mean')
            ).reset_index()
            
            # Math: Calculate Cr and USD Mil
            summary['Value (Cr)'] = summary['Value'] / 10000000
            summary['Value (USD - Mil)'] = summary['Value (Cr)'] / 8.6 # Assuming ~86 INR = 1 USD
            
            # Reorder columns for display
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
    # 2-Column layout creates the Side-by-Side view. 
    # Custom CSS above adds the Blue and Red Side Accents.
    col_fa, col_ra = st.columns(2)
    
    # --- FRESH ARBITRAGE (FA) SECTION ---
    with col_fa:
        st.markdown("<h3 style='color: #3B82F6;'>Fresh Arbitrage (FA)</h3>", unsafe_allow_html=True)
        
        # Calculate Total Lots dynamically for display
        fa_display = st.session_state['fa_repo'].copy()
        fa_display['Total Lots'] = (fa_display['Quantity'] / fa_display['Lot Size']).round(2)
        
        # Editable Dataframe
        edited_fa = st.data_editor(
            fa_display,
            disabled=["NSE Symbol", "Lot Size", "Total Lots"], # Only Quantity is editable
            use_container_width=True,
            key="fa_editor",
            hide_index=True
        )
        # Save edits back to session state
        st.session_state['fa_repo']['Quantity'] = edited_fa['Quantity']
        
        st.divider()
        st.markdown("<span style='font-size: 12px; color: #3B82F6; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
        
        # Hybrid Lookup Form fields (FA)
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
            if new_fa_sym and fa_lot > 0:
                new_row = pd.DataFrame([{"NSE Symbol": new_fa_sym, "Quantity": fa_qty, "Lot Size": fa_lot}])
                st.session_state['fa_repo'] = pd.concat([st.session_state['fa_repo'], new_row], ignore_index=True)
                st.rerun()

    # --- REVERSE ARBITRAGE (RA) SECTION ---
    with col_ra:
        st.markdown("<h3 style='color: #EF4444;'>Reverse Arbitrage (RA)</h3>", unsafe_allow_html=True)
        
        # Calculate Total Lots dynamically
        ra_display = st.session_state['ra_repo'].copy()
        ra_display['Total Lots'] = (ra_display['Quantity'] / ra_display['Lot Size']).round(2)
        
        edited_ra = st.data_editor(
            ra_display,
            disabled=["NSE Symbol", "Lot Size", "Total Lots"],
            use_container_width=True,
            key="ra_editor",
            hide_index=True
        )
        st.session_state['ra_repo']['Quantity'] = edited_ra['Quantity']
        
        st.divider()
        st.markdown("<span style='font-size: 12px; color: #EF4444; font-weight:600;'>+ Add New Entry</span>", unsafe_allow_html=True)
        
        # Hybrid Lookup Form fields (RA)
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
            if new_ra_sym and ra_lot > 0:
                new_row = pd.DataFrame([{"NSE Symbol": new_ra_sym, "Quantity": ra_qty, "Lot Size": ra_lot}])
                st.session_state['ra_repo'] = pd.concat([st.session_state['ra_repo'], new_row], ignore_index=True)
                st.rerun()