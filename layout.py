import dash_core_components as dcc
import dash_html_components as html

# Constantes
MAXCLUST = 4  # máxima cantidad de clusters

# Variables
cluster_por_nivel = []

start_layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '99%',
            'height': '120px',
            'lineHeight': '120px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True,
        contents=[],
        filename=[]
    ),
    dcc.Markdown(id= 'error_list', children=[]), #"* Error 1 \n* Error 2"
    html.Button('Continue', id='btn-continue', style={'font-family' : 'helvetica', 'textAlign' : 'center'}, disabled=False)
])


main_layout = html.Div([
    dcc.ConfirmDialog(
        id='error_message',
        message="There are no solutions that fulfill all restrictions",
        ),

    html.H2("Clustering-based Pareto-Front exploration", style={'text-align': 'center'}),
    dcc.Slider(
        id="slider_nivel",
        min=0,
        max=10,
        value=0,
        step=1,
        marks={0: '0'}, # Ponerlo como default, luego se irá sobreescribiendo, no hace falta la variable global.
        included=False,
        disabled=True
    ),
    html.Div([
        html.Div([
            html.Button('Restore', id='btn-restore', style={'font-family' : 'helvetica', 'width': "33%", 'height': "20%"}, disabled=True),
            html.Button('Zoom out', id='btn-zoomout', style={'font-family' : 'helvetica', 'width': "33%", 'height': "20%"}, disabled=True),
            html.Button('Zoom in', id='btn-zoomin', style={'font-family' : 'helvetica', 'width': "33%", 'height': "20%"}, disabled=False),
            dcc.RadioItems(
                id="cluster_seleccionado",
                # list comprehension to save time avoiding loops
                options=[{'label': 'Cluster{}'.format(c), 'value': str(c)} for c in range(1, MAXCLUST + 1)],
                labelStyle={'display': 'inline-block'},
                value=1
                ),
            html.Br(),
            html.Div(children='Desired number of clusters', style={'text-align': 'left'}),
            dcc.Slider(
                id="slider_num_clusters",
                min=2,
                max=MAXCLUST,
                value=MAXCLUST,
                step=1,
                # dict from list comprehension to save time avoiding loops
                marks=dict(zip(range(2, MAXCLUST+1), [str(x) for x in range(2, MAXCLUST+1)])),
                included=False,
                )
            ], style={'columnCount': 2}),
        html.Div([
            html.Div(children='Filters'),
            dcc.Dropdown(
                id='filtros-dropdown',
                options=[],
                value=None,
                multi=True,
                placeholder="Filter solutions that include..."
                ),
            html.Hr()
            ])
        ]),


    html.Div([
        dcc.Graph(id='profit_cost_graph', responsive=True, style={'height': '30vw'}),
        dcc.Graph(id='dendrogram_graph', responsive=True, style={'height': '18vw'})
        ], style={'columnCount': 1}),

    html.Hr(),
    html.H3("Cluster metadata", style={'text-align': 'center'}),
    html.Div([
        dcc.Textarea(id="textarea_cluster1", value="", rows=6, readOnly=True, style={'width' : "100%"}),
        dcc.Graph(id='wordcloud_req_cluster1', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Graph(id='wordcloud_stk_cluster1', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Textarea(id="textarea_cluster2", value="", rows=6, readOnly=True, style={'width' : "100%"}),
        dcc.Graph(id='wordcloud_req_cluster2', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Graph(id='wordcloud_stk_cluster2', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Textarea(id="textarea_cluster3", value="", rows=6, readOnly=True, style={'width' : "100%"}),
        dcc.Graph(id='wordcloud_req_cluster3', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Graph(id='wordcloud_stk_cluster3', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Textarea(id="textarea_cluster4", value="", rows=6, readOnly=True, style={'width' : "100%"}),
        dcc.Graph(id='wordcloud_req_cluster4', figure={}, style={'height': '12.5vw', 'width': '25vw'}),
        dcc.Graph(id='wordcloud_stk_cluster4', figure={}, style={'height': '12.5vw', 'width': '25vw'})
        ], style={'columnCount': 4})
    ])

layout = html.Div(id='page_content', children=start_layout, style={'font-family' : 'helvetica'})