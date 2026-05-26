import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


# Hub suffix map — last letter of Order ID identifies the outlet
HUB_MAP = {'C': 'Cumilla', 'S': 'Sylhet', 'W': 'Wari'}
HUB_COLORS = {
    'Cumilla': '#4f86f7',
    'Sylhet':  '#f7c948',
    'Wari':    '#f76b4f',
    'Ecom':    '#4fcf70',
}


def detect_hub(order_id: str) -> str:
    """Return hub name from Order ID suffix (C=Cumilla, S=Sylhet, W=Wari, else Ecom)."""
    if pd.isna(order_id):
        return 'Unknown'
    last = str(order_id).strip()[-1].upper()
    return HUB_MAP.get(last, 'Ecom')


# Load data — cached at module level so it's shared across calls
@st.cache_data(ttl=600)
def load_issue_data():
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

    return df


def render():
    """Render the full Issue Log Dashboard — call this from app.py."""

    st.title("📦 Delivery Issue Tracking Dashboard")
    st.markdown("---")

    try:
        df = load_issue_data()

        # ── Sidebar filters ───────────────────────────────────────────────────
        st.sidebar.header("🎛️ Issue Filters")

        min_date = df['Date'].min()
        max_date = df['Date'].max()
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="iss_date_range",
        )

        couriers = ['All'] + sorted(df['Courier'].dropna().unique().tolist())
        selected_courier = st.sidebar.selectbox("Courier", couriers, key="iss_courier")

        issue_types = ['All'] + sorted(df['Delivery Issue'].dropna().unique().tolist())
        selected_issue = st.sidebar.selectbox("Delivery Issue Type", issue_types, key="iss_type")

        fu_statuses = ['All'] + sorted(df['FU Status'].dropna().unique().tolist())
        selected_fu_status = st.sidebar.selectbox("FU Status", fu_statuses, key="iss_fu")

        on_time_options = ['All'] + sorted(df['On Time'].dropna().unique().tolist())
        selected_on_time = st.sidebar.selectbox("On Time Status", on_time_options, key="iss_ontime")

        hub_options = ['All'] + sorted(df['Hub'].dropna().unique().tolist())
        selected_hub = st.sidebar.selectbox("Hub / Outlet", hub_options, key="iss_hub")

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
        st.header("🎯 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)

        total_issues = len(filtered_df)
        pending_inventory = len(filtered_df[filtered_df['Inventory Updated'] == 'Pending'])
        late_followups = len(filtered_df[filtered_df['On Time'] == '⚠️ Late'])
        done_status = len(filtered_df[filtered_df['FU Status'] == 'Done'])
        avg_resolution = filtered_df['Resolution Days'].mean()

        with col1:
            st.metric("Total Issues", f"{total_issues:,}")
        with col2:
            st.metric("Pending Inventory", f"{pending_inventory:,}")
        with col3:
            late_pct = (late_followups / total_issues * 100) if total_issues > 0 else 0
            st.metric("Late Follow-ups", f"{late_followups:,}", f"{late_pct:.1f}%")
        with col4:
            done_pct = (done_status / total_issues * 100) if total_issues > 0 else 0
            st.metric("Completed", f"{done_status:,}", f"{done_pct:.1f}%")
        with col5:
            st.metric(
                "Avg Resolution Days",
                f"{avg_resolution:.1f}" if not pd.isna(avg_resolution) else "N/A",
            )

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
                title='Weekly Issue Trend', markers=True,
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🥧 Issue Type Breakdown")
            issue_counts = filtered_df['Delivery Issue'].value_counts()
            fig = px.pie(values=issue_counts.values, names=issue_counts.index, hole=0.4)
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

        product_reasons = []
        for product in product_issues['Product Details']:
            reasons = (
                filtered_df[filtered_df['Issue Or Product Details'] == product]
                ['Customer Reason'].value_counts()
            )
            product_reasons.append(reasons.index[0] if len(reasons) > 0 else 'N/A')

        product_issues['Top Customer Reason'] = product_reasons
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

        # ── Row 6: Hub Returns Analysis ───────────────────────────────────────
        st.markdown("---")
        st.header("🏪 Hub / Outlet Returns Analysis")
        st.caption("Outlet is detected from the Order ID suffix — C: Cumilla · S: Sylhet · W: Wari · (none): Ecom")

        hub_summary = (
            filtered_df.groupby('Hub')
            .agg(
                Total_Issues=('Order ID', 'count'),
                Late_Followups=('On Time', lambda x: (x == '⚠️ Late').sum()),
                Pending_Inventory=('Inventory Updated', lambda x: (x == 'Pending').sum()),
                Done=('FU Status', lambda x: (x == 'Done').sum()),
                Avg_Resolution=('Resolution Days', 'mean'),
            )
            .reset_index()
        )
        hub_summary['Done %'] = (hub_summary['Done'] / hub_summary['Total_Issues'] * 100).round(1)
        hub_summary['Late %'] = (hub_summary['Late_Followups'] / hub_summary['Total_Issues'] * 100).round(1)

        # KPI cards per hub
        hub_cols = st.columns(len(hub_summary))
        for i, row in hub_summary.iterrows():
            with hub_cols[i]:
                hub_color = HUB_COLORS.get(row['Hub'], '#888')
                st.markdown(
                    f"""
                    <div style="background:{hub_color};border-radius:12px;padding:16px;text-align:center;color:#fff;margin-bottom:8px;">
                        <div style="font-size:1.6rem;font-weight:700;">{int(row['Total_Issues'])}</div>
                        <div style="font-size:1rem;font-weight:600;">{row['Hub']}</div>
                        <div style="font-size:0.8rem;opacity:0.9;">✅ {row['Done %']}% Done &nbsp;|&nbsp; ⚠️ {row['Late %']}% Late</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("")

        # Bar + Pie side by side
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("📊 Issues by Hub")
            fig = px.bar(
                hub_summary,
                x='Hub', y='Total_Issues',
                color='Hub',
                color_discrete_map=HUB_COLORS,
                text='Total_Issues',
                labels={'Total_Issues': 'Issue Count'},
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=380, showlegend=False, xaxis_title='Hub / Outlet')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🥧 Hub Share")
            fig = px.pie(
                hub_summary,
                names='Hub', values='Total_Issues',
                color='Hub',
                color_discrete_map=HUB_COLORS,
                hole=0.45,
            )
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

        # Weekly trend by hub
        st.subheader("📈 Weekly Issues per Hub")
        hub_time_df = (
            filtered_df.groupby([pd.Grouper(key='Date', freq='W'), 'Hub'])
            .size()
            .reset_index(name='Count')
        )
        fig = px.line(
            hub_time_df, x='Date', y='Count', color='Hub',
            color_discrete_map=HUB_COLORS,
            markers=True, title='Weekly Return/Issue Trend by Hub',
        )
        fig.update_layout(height=380, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        # Detailed hub breakdown table
        st.subheader("📋 Hub Breakdown Detail")
        display_summary = hub_summary.rename(columns={
            'Hub': 'Hub / Outlet',
            'Total_Issues': 'Total Issues',
            'Late_Followups': 'Late Follow-ups',
            'Pending_Inventory': 'Pending Inventory',
            'Done': 'Completed',
            'Avg_Resolution': 'Avg Resolution Days',
            'Done %': 'Completion %',
            'Late %': 'Late %',
        })
        display_summary['Avg Resolution Days'] = display_summary['Avg Resolution Days'].round(1)
        st.dataframe(display_summary, use_container_width=True, hide_index=True)

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

