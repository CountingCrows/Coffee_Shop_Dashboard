import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar

def load_data():
    df = pd.read_csv('Coffee Shop Sales.csv')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['total_price'] = df['transaction_qty'] * df['unit_price']
    
    return df

def create_daily_metrics(df):
    daily_sales = df.groupby('transaction_date').agg({
        'total_price': 'sum',
        'transaction_id': 'nunique',
        'transaction_qty': 'sum'
    }).reset_index()
    return daily_sales

def create_product_metrics(df):
    return df.groupby(['product_category', 'product_type']).agg({
        'total_price': 'sum',
        'transaction_id': 'count',
        'transaction_qty': 'sum'
    }).reset_index()

def main():
    st.set_page_config(page_title="Maven Roasters Dashboard", layout="wide")
    
    # Load data
    with st.spinner('Loading data...'):
        df = load_data()

    if df.empty:
        return

    # Sidebar filters
    st.sidebar.header('Filters')
    
    # Convert datetime to date for the date input widget
    min_date = df['transaction_date'].min().date()
    max_date = df['transaction_date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Convert the selected dates to datetime64[ns]
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    # Store location filter
    selected_stores = st.sidebar.multiselect(
        'Select Stores',
        options=df['store_location'].unique(),
        default=df['store_location'].unique()
    )
    
    # Filter data using datetime64[ns]
    filtered_df = df[
        (df['transaction_date'].dt.normalize() >= start_date.normalize()) &
        (df['transaction_date'].dt.normalize() <= end_date.normalize()) &
        (df['store_location'].isin(selected_stores))
    ]

    # Main dashboard
    st.title('🍵Maven Roasters Sales Dashboard')
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning('No data available for the selected filters.')
        return
    
    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", 
                 f"${filtered_df['total_price'].sum():,.2f}")
    with col2:
        st.metric("Total Transactions", 
                 f"{filtered_df['transaction_id'].nunique():,}")
    with col3:
        st.metric("Avg Transaction Value", 
                 f"${filtered_df['total_price'].mean():,.2f}")
    with col4:
        st.metric("Total Items Sold", 
                 f"{filtered_df['transaction_qty'].sum():,}")
    
    # Sales Trends
    st.header('Sales Trends')
    daily_sales = create_daily_metrics(filtered_df)
    
    # Daily revenue trend
    fig_revenue = px.line(daily_sales, 
                         x='transaction_date', 
                         y='total_price',
                         title='Daily Revenue Trend',
                         line_shape='linear'
    )
    fig_revenue.update_layout(
        xaxis_title='Date',
        yaxis_title='Revenue ($)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_x=0.5
    )
    fig_revenue.update_traces(
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.2f}<extra></extra>"
    )
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Product Analysis
    st.header('Product Performance')
    col1, col2 = st.columns(2)
    
    with col1:
        # Top products by revenue
        product_metrics = create_product_metrics(filtered_df)
        fig_products = px.bar(
            product_metrics.nlargest(10, 'total_price'),
            x='total_price',
            y='product_type',
            title='Top 10 Products by Revenue',
            orientation='h'
        )
        fig_products.update_layout(
            xaxis_title='Revenue ($)',
            yaxis_title='Product',
            plot_bgcolor='rgba(0,0,0,0)',
            title_x=0.5
        )
        fig_products.update_traces(
            hovertemplate="<b>%{y}</b><br>Revenue: $%{x:.2f}<extra></extra>"
        )
        st.plotly_chart(fig_products, use_container_width=True)
    
    with col2:
        # Category distribution
        fig_categories = px.pie(
            filtered_df,
            names='product_category',
            values='total_price',
            title='Sales Distribution by Category'
        )
        fig_categories.update_layout(
        xaxis_title="Product Category",
        yaxis_title="Revenue ($)",
        plot_bgcolor="rgba(0,0,0,0)",
        title_x=0.5
        )
        fig_categories.update_traces(
        hovertemplate="<b>%{label}</b><br>Revenue: $%{value:.2f}<extra></extra>",
        )
        st.plotly_chart(fig_categories, use_container_width=True)
    
    # Store Performance
    st.header('Store Performance')
    store_metrics = filtered_df.groupby('store_location').agg({
        'total_price': 'sum',
        'transaction_id': 'nunique',
        'transaction_qty': 'sum'
    }).reset_index()
    
    fig_stores = px.bar(
        store_metrics,
        x='store_location',
        y='total_price',
        title='Revenue by Store Location'
    )
    fig_stores.update_layout(
        xaxis_title="Store Location",
        yaxis_title="Revenue ($)",
        plot_bgcolor="rgba(0,0,0,0)",
        title_x=0.5
    )
    fig_stores.update_traces(
    hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.2f}<br>Items Sold: %{text}<extra></extra>",
    text=store_metrics['transaction_qty']  # Assuming 'transaction_id' represents the number of items sold
    )   
    st.plotly_chart(fig_stores, use_container_width=True)
    
    # Time Analysis
    st.header('Time-based Analysis')
    col1, col2 = st.columns(2)
    
    with col1:
        # Hourly patterns
        hourly_data = filtered_df.groupby(
            filtered_df['transaction_time'].str[:2]
        )['total_price'].mean().reset_index()
        hourly_data = hourly_data.sort_values('transaction_time')
        fig_hourly = px.line(
            hourly_data,
            x='transaction_time',
            y='total_price',
            title='Average Sales by Hour'
        )
        fig_hourly.update_layout(
            xaxis_title='Hour of Day',
            yaxis_title='Average Sales ($)',
            plot_bgcolor='rgba(0,0,0,0)',
            title_x=0.5
        )
        fig_hourly.update_traces(
            hovertemplate="<b>%{x}00</b><br>Average Sales: $%{y:.2f}<extra></extra>"
        )   
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        # Daily patterns
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_patterns = filtered_df.assign(
            day_of_week=filtered_df['transaction_date'].dt.day_name()
        ).groupby('day_of_week')['total_price'].mean().reindex(day_order).reset_index()
        
        fig_daily = px.bar(
            daily_patterns,
            x='day_of_week',
            y='total_price',
            title='Average Sales by Day of Week'
        )
        fig_daily.update_layout(
            xaxis_title='Day of Week',
            yaxis_title='Average Sales ($)',
            plot_bgcolor='rgba(0,0,0,0)',
            title_x=0.5
        )
        fig_daily.update_traces(
            hovertemplate="<b>%{x}</b><br>Average Sales: $%{y:.2f}<extra></extra>"
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    with st.expander("View Dataset"):
        st.dataframe(filtered_df)

if __name__ == "__main__":
    main()