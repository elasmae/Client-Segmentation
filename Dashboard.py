import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Load and preprocess the data
data_dummies = pd.read_csv("customer_segmentation_data_cleaned.csv")

# Simulate a 'date' column for temporal analysis
data_dummies['date'] = pd.date_range(start="2023-01-01", periods=len(data_dummies), freq='D').to_list()

# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("Ultimate ROI Analysis Dashboard", style={'textAlign': 'center'}),

    # Filter Section
    html.Div([
        html.Div([
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id='date-picker',
                min_date_allowed=data_dummies['date'].min(),
                max_date_allowed=data_dummies['date'].max(),
                start_date=data_dummies['date'].min(),
                end_date=data_dummies['date'].max()
            )
        ], style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Select Cluster:"),
            dcc.Dropdown(
                id='cluster-dropdown',
                options=[{'label': f'Cluster {i}', 'value': i} for i in data_dummies['Cluster'].unique()],
                value=data_dummies['Cluster'].unique()[0],
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Select Region:"),
            dcc.Dropdown(
                id='region-dropdown',
                options=[
                    {'label': 'All Regions', 'value': 'all'},
                    {'label': 'Region 1', 'value': 'region_1'},
                    {'label': 'Region 2', 'value': 'region_2'}
                ],
                value='all'
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
    ]),

    # KPI Cards
    html.Div(id='kpi-cards', style={'display': 'flex', 'justifyContent': 'space-around', 'margin': '20px 0'}),

    # Visualizations
    dcc.Tabs([
        dcc.Tab(label='Bar Chart', children=[
            dcc.Graph(id='bar-chart')
        ]),
        dcc.Tab(label='Line Chart (Trend Analysis)', children=[
            dcc.Graph(id='line-chart')
        ]),
        dcc.Tab(label='Scatter Plot: ROI vs Spend', children=[
            dcc.Graph(id='scatter-chart')
        ]),
        dcc.Tab(label='Correlation Heatmap', children=[
            dcc.Graph(id='heatmap')
        ]),
        dcc.Tab(label='Summary Table', children=[
            dash_table.DataTable(id='roi-table', style_table={'overflowX': 'auto'})
        ])
    ])
])

# Callbacks for interactivity
@app.callback(
    [Output('kpi-cards', 'children'),
     Output('bar-chart', 'figure'),
     Output('line-chart', 'figure'),
     Output('scatter-chart', 'figure'),
     Output('heatmap', 'figure'),
     Output('roi-table', 'data')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('cluster-dropdown', 'value'),
     Input('region-dropdown', 'value')]
)
def update_dashboard(start_date, end_date, selected_clusters, selected_region):
    # Filter data by date range
    filtered_data = data_dummies[(data_dummies['date'] >= start_date) & (data_dummies['date'] <= end_date)]

    # Filter by cluster
    if isinstance(selected_clusters, list):
        filtered_data = filtered_data[filtered_data['Cluster'].isin(selected_clusters)]

    # Filter by region
    if selected_region != 'all':
        filtered_data = filtered_data[filtered_data[selected_region] == True]

    # KPI Cards
    kpi_cards = [
        html.Div([
            html.H4("Average ROI"), html.P(f"{filtered_data['ROI'].mean():.2f}%")
        ], className="card"),
        html.Div([
            html.H4("Average CTR"), html.P(f"{filtered_data['CTR'].mean():.2f}%")
        ], className="card"),
        html.Div([
            html.H4("Total Conversions"), html.P(f"{filtered_data['Conversions'].sum():,}")
        ], className="card"),
        html.Div([
            html.H4("Total Spend"), html.P(f"${filtered_data['Campaign_Spend'].sum():,.2f}")
        ], className="card")
    ]

    # Bar Chart
    bar_fig = px.bar(
        filtered_data.groupby('Cluster').mean().reset_index(),
        x='Cluster', y='ROI', title="ROI by Cluster", color='Cluster'
    )

    # Line Chart for Trend Analysis
    line_fig = px.line(
        filtered_data.groupby(['date', 'Cluster']).mean().reset_index(),
        x='date', y='ROI', color='Cluster', title="ROI Trend Over Time"
    )

    # Scatter Plot
    scatter_fig = px.scatter(
        filtered_data, x='Campaign_Spend', y='ROI', size='Conversions',
        color='Cluster', title="ROI vs Campaign Spend"
    )

    # Correlation Heatmap
    heatmap_data = filtered_data[['ROI', 'CTR', 'Conversions', 'Campaign_Spend']].corr()
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.columns,
        colorscale='Viridis'
    ))
    heatmap_fig.update_layout(title="Correlation Heatmap")

    # ROI Table Data
    roi_table_data = filtered_data.groupby('Cluster').agg({
        'ROI': 'mean',
        'CTR': 'mean',
        'Conversions': 'sum',
        'Campaign_Spend': 'sum'
    }).reset_index().to_dict('records')

    return kpi_cards, bar_fig, line_fig, scatter_fig, heatmap_fig, roi_table_data

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
