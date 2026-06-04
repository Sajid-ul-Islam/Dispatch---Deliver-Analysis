import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


# Hub suffix map — last letter of Order ID identifies the outlet
HUB_MAP = {' c': 'Cumilla', ' s': 'Sylhet', ' w': 'Wari'}
def detect_hub(order_id: str) -> str:
    """Return hub name from Order ID suffix (C=Cumilla, S=Sylhet, W=Wari, else Ecom)."""
    if pd.isna(order_id):
        return 'Unknown'
    last = str(order_id).strip()[-1].upper()
    return HUB_MAP.get(last, 'Ecom')


# Load data — cached at module level so it's shared across calls
@st.cache_data(ttl=600)
def load_issue_data() -> tuple[pd.DataFrame, datetime]:
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4j3i94IWVlVYI5gErxzfmmaYNiirGqnrncRKrDCbHvmLYpzH9l4_etjYmfCoDj_Gv-_mps2gnufXE/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(url)

    # Convert date columns
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df['FU'] = pd.to_datetime(df['FU'], format='%m/%d/%Y', errors='coerce')
    df['Received Date'] = pd.to_datetime(df['Received Date'], format='%m/%d/%Y', errors='coerce')

    # Calculate resolution time
    df['Resolution Days'] = (df['FU'] - df['Date']).dt.days

    # Detect hub from Order ID suffix
    df['Hub'] = df['Order ID'].astype(str).apply(detect_hub)

    return df, datetime.now()


def render():
    """Render the full Issue Log Dashboard — call this from app.py."""

    st.title("📦 Delivery Issue Tracking Dashboard")
    st.markdown("---")

    try:
        df, last_fetched = load_issue_data()

        # ── Sidebar filters ───────────────────────────────────────────────────
        with st.sidebar.container(border=True):
            st.caption("📈 Data Summary")
            st.metric("Total Cached Records", f"{len(df):,}")
            
            # Freshness Indicator
            diff = datetime.now() - last_fetched
            minutes = int(diff.total_seconds() // 60)
            freshness = "Just now" if minutes == 0 else f"{minutes}m ago"
            st.caption(f"⏱️ Freshness: {freshness}")

        with st.sidebar.expander("🔍 Issue Filters", expanded=True):
            min_date = df['Date'].min()
            max_date = df['Date'].max()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="iss_date_range",
            )

            selected_courier = st.selectbox("Courier", ['All'] + sorted(df['Courier'].dropna().unique().tolist()), key="iss_courier")
            selected_issue = st.selectbox("Issue Type", ['All'] + sorted(df['Delivery Issue'].dropna().unique().tolist()), key="iss_type")
            selected_fu_status = st.selectbox("FU Status", ['All'] + sorted(df['FU Status'].dropna().unique().tolist()), key="iss_fu")
            selected_on_time = st.selectbox("On Time Status", ['All'] + sorted(df['On Time'].dropna().unique().tolist()), key="iss_ontime")
            selected_hub = st.selectbox("Hub / Outlet", ['All'] + sorted(df['Hub'].dropna().unique().tolist()), key="iss_hub")

        # ── Apply filters ─────────────────────────────────────────────────────
        filtered_df = df.copy()

        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df['Date'] >= pd.to_datetime(date_range[0])) &
                (filtered_df['Date'] <= pd.to_datetime(date_range[1]))
            ]

        if selected_courier != 'All':
            filtered_df = filtered_df[filtered_df['Courier'] == selected_courier]
        if selected_issue != 'All':
            filtered_df = filtered_df[filtered_df['Delivery Issue'] == selected_issue]
        if selected_fu_status != 'All':
            filtered_df = filtered_df[filtered_df['FU Status'] == selected_fu_status]
        if selected_on_time != 'All':
            filtered_df = filtered_df[filtered_df['On Time'] == selected_on_time]
        if selected_hub != 'All':
            filtered_df = filtered_df[filtered_df['Hub'] == selected_hub]

        # ── Key metrics ───────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("### 🎯 Key Performance Indicators")
            col1, col2, col3, col4, col5 = st.columns(5)

            total_issues = len(filtered_df)
            pending_inventory = len(filtered_df[filtered_df['Inventory Updated'] == 'Pending'])
            late_followups = len(filtered_df[filtered_df['On Time'] == '⚠️ Late'])
            done_status = len(filtered_df[filtered_df['FU Status'] == 'Done'])
            avg_resolution = filtered_df['Resolution Days'].mean()

            with col1:
                st.metric("Total Issues", f"{total_issues:,}")
            with col2:
                st.metric("Pending Inv.", f"{pending_inventory:,}")
            with col3:
                late_pct = (late_followups / total_issues * 100) if total_issues > 0 else 0
                st.metric("Late FU", f"{late_followups:,}", f"{late_pct:.1f}%", delta_color="inverse")
            with col4:
                done_pct = (done_status / total_issues * 100) if total_issues > 0 else 0
                st.metric("Completed", f"{done_status:,}", f"{done_pct:.1f}%")
            with col5:
                st.metric("Avg Res. Days", f"{avg_resolution:.1f}" if not pd.isna(avg_resolution) else "N/A")

        st.markdown("---")

        # ── Row 1: Time series + issue breakdown ──────────────────────────────
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📈 Issues Over Time")
            time_df = (
                filtered_df.groupby([pd.Grouper(key='Date', freq='W'), 'Delivery Issue'])
                .size()
                .reset_index(name='Count')
            )
            fig = px.line(
                time_df, x='Date', y='Count', color='Delivery Issue',
                title='Weekly Issue Trend', markers=True, color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🥧 Issue Type Breakdown")
            issue_counts = filtered_df['Delivery Issue'].value_counts()
            fig = px.pie(values=issue_counts.values, names=issue_counts.index, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        # ── Row 2: Customer reasons + courier performance ─────────────────────
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Top Customer Reasons")
            top_reasons = filtered_df['Customer Reason'].value_counts().head(10)
            fig = px.bar(
                x=top_reasons.values, y=top_reasons.index, orientation='h',
                labels={'x': 'Count', 'y': 'Reason'},
                color=top_reasons.values, color_continuous_scale='Blues',
            )
            fig.update_layout(
                height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🚚 Issues by Courier")
            courier_issue_df = (
                filtered_df.groupby(['Courier', 'Delivery Issue']).size().reset_index(name='Count')
            )
            fig = px.bar(
                courier_issue_df, x='Courier', y='Count',
                color='Delivery Issue', barmode='stack',
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # ── Row 3: Timeliness + inventory status ──────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⏰ Follow-up Timeliness")
            on_time_counts = filtered_df['On Time'].value_counts()
            fig = px.bar(
                x=on_time_counts.index, y=on_time_counts.values,
                labels={'x': 'Status', 'y': 'Count'},
                color=on_time_counts.index,
                color_discrete_map={'⚠️ Late': '#ff6b6b', 'On Time': '#51cf66'},
            )
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📦 Inventory Status")
            inventory_counts = filtered_df['Inventory Updated'].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=inventory_counts.index,
                values=inventory_counts.values,
                marker=dict(colors=['#ffd43b', '#51cf66']),
                textinfo='label+percent+value',
            )])
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        # ── Row 4: Top products table ─────────────────────────────────────────
        st.subheader("🔍 Top Products with Issues")
        product_issues = (
            filtered_df['Issue Or Product Details'].value_counts().head(20).reset_index()
        )
        product_issues.columns = ['Product Details', 'Issue Count']
        
        # Optimized Top Reason mapping using grouping
        top_reasons = filtered_df.groupby('Issue Or Product Details')['Customer Reason'].agg(lambda x: x.value_counts().index[0] if not x.empty else 'N/A')
        product_issues['Top Customer Reason'] = product_issues['Product Details'].map(top_reasons)
        
        product_issues['% of Total'] = (
            product_issues['Issue Count'] / total_issues * 100
        ).round(2)

        st.dataframe(product_issues, use_container_width=True, height=400)

        # ── Row 5: Resolution time trend ──────────────────────────────────────
        st.subheader("📅 Resolution Time Trend")
        resolution_df = filtered_df.dropna(subset=['Resolution Days'])
        if len(resolution_df) > 0:
            weekly_resolution = (
                resolution_df.groupby(pd.Grouper(key='Date', freq='W'))
                .agg({'Resolution Days': 'mean', 'Order ID': 'count'})
                .reset_index()
            )
            weekly_resolution.columns = ['Week', 'Avg Resolution Days', 'Issue Count']

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=weekly_resolution['Week'], y=weekly_resolution['Issue Count'],
                name='Issue Count', yaxis='y', marker_color='lightblue',
            ))
            fig.add_trace(go.Scatter(
                x=weekly_resolution['Week'], y=weekly_resolution['Avg Resolution Days'],
                name='Avg Resolution Days', yaxis='y2',
                mode='lines+markers', marker_color='red',
            ))
            fig.update_layout(
                yaxis=dict(title='Issue Count'),
                yaxis2=dict(title='Avg Resolution Days', overlaying='y', side='right'),
                height=400,
                hovermode='x unified',
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No resolution time data available for selected filters")

        # ── Export ────────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📥 Export Data")
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name=f"issue_log_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="iss_download",
        )

        st.markdown("---")
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Total records: {len(df):,} | Filtered: {len(filtered_df):,}"
        )

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure the Google Sheet is publicly accessible and the URL is correct.")
