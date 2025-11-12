"""
SMART ROAD SAFETY INTERVENTION COST ESTIMATOR - WEB APP
National Road Safety Hackathon 2025 - IIT Madras

Interactive Streamlit interface for cost estimation

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import estimator_helper as est_api

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MAARG SETU - Smart Road Safety Cost Estimator",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        font-weight: bold;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #424242;
        text-align: center;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .intervention-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<div class="main-header">🛣️ MAARG SETU -  Smart Road Safety Cost Estimator</div>', 
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Intervention Cost Analysis</div>', 
            unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("assets/margsetu.png", width=600)
    st.title("⚙️ Configuration")
    
    # Rate source selection
    rate_source = st.radio(
        "Select Rate Source:",
        ["CPWD SOR 2024", "GeM Portal"],
        help="Choose between CPWD Schedule of Rates or Government e-Marketplace prices"
    )
    
    use_gem = (rate_source == "GeM Portal")
    
    st.markdown("---")
    
    # Information section
    st.subheader("📚 About")
    st.info("""
    This tool automatically:
    - Extracts interventions from reports
    - Maps to IRC standards
    - Computes material costs
    - Provides detailed breakdowns
    """)
    
    st.markdown("---")
    
    st.subheader("📖 IRC Standards")
    with st.expander("View Standards"):
        for irc_code, info in est_api.IRC_STANDARDS_MAP.items():
            st.text(f"{irc_code}")
            st.caption(info['title'])
            st.markdown("")
    
    st.markdown("---")
    
    # Sample data
    st.subheader("📝 Sample Reports")
    sample_choice = st.selectbox(
        "Load Sample:",
        ["None", "Highway Safety", "Urban Road", "Rural Road"]
    )

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Input & Estimate", "📊 Results", "📈 Visualizations", "📥 Export"])

# ============================================================================
# TAB 1: INPUT & ESTIMATE
# ============================================================================

with tab1:
    st.header("Input Intervention Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Load sample data if selected
        default_text = ""
        if sample_choice == "Highway Safety":
            default_text = """Highway Safety Improvement Project - NH-44 Section

Proposed Interventions:
1. Install metal crash barrier as per IRC 119 for 500 meters on both sides
2. Provide warning sign boards as per IRC 67 at 10 locations
3. Construct concrete median barrier for 200 meters
4. Road marking including zebra crossing covering 150 sqm
5. Install speed breakers at 3 locations
6. Cat eye reflectors at 100 meter intervals for 1 km"""
        
        elif sample_choice == "Urban Road":
            default_text = """Urban Road Safety Enhancement

Safety Measures Required:
- Sign boards for traffic regulation - 15 numbers as per IRC 67
- Crash barriers on flyover - 80 meters W-beam type per IRC 119
- Footpath kerb stones - 300 meters
- Thermoplastic road markings - 200 square meters
- Rumble strips at junctions - 5 locations"""
        
        elif sample_choice == "Rural Road":
            default_text = """Rural Road Safety Project

Interventions Needed:
1. Warning signage for curves - IRC 67 - 8 locations
2. Speed humps at village entry - 4 nos
3. Road studs for delineation - 150 numbers
4. Guard rails at bridges - 60 meters
5. Pedestrian crossing markings - 80 sqm"""
        
        # Text input
        input_text = st.text_area(
            "Enter intervention report:",
            value=default_text,
            height=300,
            placeholder="Paste your road safety intervention report here..."
        )
        
        # Process button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            process_button = st.button("🔍 Analyze & Estimate", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_button:
            st.rerun()
    
    with col2:
        st.subheader("💡 Tips")
        st.markdown("""
        **Supported Keywords:**
        - Sign board, warning sign
        - Crash barrier, guard rail
        - Road marking, zebra crossing
        - Speed breaker, rumble strip
        - Median, divider
        - Kerb, curb
        - Cat eye, road stud
        
        **Quantity Formats:**
        - "100 meters"
        - "50 sqm"
        - "10 numbers"
        - "2 km"
        
        **IRC Standards:**
        - IRC 67 (Signs)
        - IRC 99 (Markings)
        - IRC 119 (Barriers)
        - IRC SP:84 (Medians)
        - IRC SP:87 (Speed Control)
        """)
    
    # Process the input
    if process_button and input_text:
        with st.spinner("🔄 Processing interventions..."):
            # Load rates
            if use_gem:
                rates_df = est_api.load_gem_rates()
            else:
                rates_df = est_api.load_cpwd_rates()
            
            # Extract and compute
            estimates, summary_df, detailed_df = est_api.estimate_costs_from_text(
                input_text, 
                use_gem_rates=use_gem
            )
            
            # Store in session state
            st.session_state['estimates'] = estimates
            st.session_state['summary_df'] = summary_df
            st.session_state['detailed_df'] = detailed_df
            st.session_state['processed'] = True
            
            st.success(f"✅ Successfully processed {len(estimates)} interventions!")
            st.balloons()

# ============================================================================
# TAB 2: RESULTS
# ============================================================================

with tab2:
    if 'processed' in st.session_state and st.session_state['processed']:
        estimates = st.session_state['estimates']
        summary_df = st.session_state['summary_df']
        detailed_df = st.session_state['detailed_df']
        
        # Overall metrics
        st.header("📊 Cost Estimation Results")
        
        total_cost = sum(est.total_cost for est in estimates)
        avg_cost = total_cost / len(estimates) if estimates else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Interventions", len(estimates))
        with col2:
            st.metric("Total Material Cost", f"₹{total_cost:,.0f}")
        with col3:
            st.metric("Avg Cost/Intervention", f"₹{avg_cost:,.0f}")
        with col4:
            st.metric("Rate Source", rate_source)
        
        st.markdown("---")
        
        # Summary table
        st.subheader("📋 Summary by Intervention")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Detailed breakdown
        st.subheader("🔍 Detailed Material Breakdown")
        
        for idx, est in enumerate(estimates, 1):
            with st.expander(f"**{idx}. {est.intervention.intervention_type.replace('_', ' ').title()}** - ₹{est.total_cost:,.2f}"):
                st.markdown(f"**Description:** {est.intervention.raw_text}")
                st.markdown(f"**IRC Standard:** {est.irc_clause}")
                st.markdown(f"**Quantity:** {est.intervention.quantity} {est.intervention.unit}")
                
                st.markdown("**Materials:**")
                
                material_data = []
                for material, quantity in est.materials:
                    cost = quantity * material.rate_per_unit
                    material_data.append({
                        'Material': material.description,
                        'Item Code': material.item_code,
                        'Quantity': f"{quantity:.2f}",
                        'Unit': material.unit,
                        'Rate (₹)': f"{material.rate_per_unit:.2f}",
                        'Cost (₹)': f"{cost:,.2f}",
                        'Source': material.source
                    })
                
                st.dataframe(pd.DataFrame(material_data), use_container_width=True, hide_index=True)
    
    else:
        st.info("👈 Please process an intervention report in the 'Input & Estimate' tab first")

# ============================================================================
# TAB 3: VISUALIZATIONS
# ============================================================================

with tab3:
    if 'processed' in st.session_state and st.session_state['processed']:
        estimates = st.session_state['estimates']
        
        st.header("📈 Visual Analytics")
        
        # Cost by intervention
        chart_data = []
        for est in estimates:
            chart_data.append({
                'Intervention': est.intervention.intervention_type.replace('_', ' ').title(),
                'Cost (₹)': est.total_cost
            })
        
        df_chart = pd.DataFrame(chart_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cost by Intervention")
            fig1 = px.bar(
                df_chart,
                x='Intervention',
                y='Cost (₹)',
                color='Cost (₹)',
                color_continuous_scale='Blues',
                title="Material Cost Breakdown"
            )
            fig1.update_layout(height=400)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("Cost Distribution")
            fig2 = px.pie(
                df_chart,
                values='Cost (₹)',
                names='Intervention',
                title="Percentage Share by Intervention"
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Material category analysis
        st.subheader("Material Category Analysis")
        
        category_costs = {}
        rates_df = est_api.load_cpwd_rates() if not use_gem else est_api.load_gem_rates()
        
        for est in estimates:
            for material, quantity in est.materials:
                cat_data = rates_df[rates_df['item_code'] == material.item_code]
                if not cat_data.empty:
                    category = cat_data['category'].values[0]
                    cost = quantity * material.rate_per_unit
                    category_costs[category] = category_costs.get(category, 0) + cost
        
        if category_costs:
            cat_df = pd.DataFrame(list(category_costs.items()), 
                                 columns=['Category', 'Total Cost (₹)'])
            cat_df = cat_df.sort_values('Total Cost (₹)', ascending=True)
            
            fig3 = px.bar(
                cat_df,
                y='Category',
                x='Total Cost (₹)',
                orientation='h',
                title="Cost by Material Category",
                color='Total Cost (₹)',
                color_continuous_scale='Viridis'
            )
            fig3.update_layout(height=500)
            st.plotly_chart(fig3, use_container_width=True)
    
    else:
        st.info("👈 Please process an intervention report first")

# ============================================================================
# TAB 4: EXPORT
# ============================================================================

with tab4:
    if 'processed' in st.session_state and st.session_state['processed']:
        st.header("📥 Export Reports")
        
        estimates = st.session_state['estimates']
        summary_df = st.session_state['summary_df']
        detailed_df = st.session_state['detailed_df']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 CSV Export")
            csv_data = summary_df.to_csv(index=False)
            st.download_button(
                label="Download Summary CSV",
                data=csv_data,
                file_name=f"cost_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            detailed_csv = detailed_df.to_csv(index=False)
            st.download_button(
                label="Download Detailed CSV",
                data=detailed_csv,
                file_name=f"cost_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.subheader("📊 Excel Export")
            
            # Create Excel file in memory
            from io import BytesIO
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                detailed_df.to_excel(writer, sheet_name='Detailed', index=False)
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="Download Excel Report",
                data=excel_data,
                file_name=f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Generate text report
        st.subheader("📝 Formatted Text Report")
        
        total_cost = sum(est.total_cost for est in estimates)
        
        report_text = f"""
ROAD SAFETY INTERVENTION COST ESTIMATION REPORT
{'=' * 70}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Rate Source: {rate_source}

SUMMARY
-------
Total Interventions: {len(estimates)}
Total Material Cost: ₹{total_cost:,.2f}
Average Cost per Intervention: ₹{total_cost/len(estimates):,.2f}

DETAILED BREAKDOWN
------------------
"""
        
        for idx, est in enumerate(estimates, 1):
            report_text += f"\n{idx}. {est.intervention.intervention_type.upper()}\n"
            report_text += f"   {est.intervention.raw_text}\n"
            report_text += f"   IRC Standard: {est.irc_clause}\n"
            report_text += f"   Quantity: {est.intervention.quantity} {est.intervention.unit}\n\n"
            report_text += "   Materials:\n"
            
            for material, quantity in est.materials:
                cost = quantity * material.rate_per_unit
                report_text += f"   - {material.description}\n"
                report_text += f"     Code: {material.item_code} | "
                report_text += f"Qty: {quantity:.2f} {material.unit} | "
                report_text += f"Rate: ₹{material.rate_per_unit:.2f} | "
                report_text += f"Cost: ₹{cost:,.2f}\n"
            
            report_text += f"\n   TOTAL: ₹{est.total_cost:,.2f}\n"
            report_text += "-" * 70 + "\n"
        
        st.text_area("Report Preview", report_text, height=400)
        
        st.download_button(
            label="Download Text Report",
            data=report_text,
            file_name=f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    else:
        st.info("👈 Please process an intervention report first")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><b>MAARG SETU - Smart Road Safety Cost Estimator</b></p>
    <p>National Road Safety Hackathon 2025 | IIT Madras</p>
    <p>Powered by AI/ML • IRC Standards • CPWD SOR • GeM Portal</p>
</div>
""", unsafe_allow_html=True)