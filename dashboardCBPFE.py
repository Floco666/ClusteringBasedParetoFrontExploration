import plotly.express as px  # (version 4.7.0)
import plotly.graph_objects as go
import plotly.figure_factory as ff

import pandas as pd
import numpy as np
import math
from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree, fcluster
from scipy.spatial.distance import squareform, pdist
from wordcloud import WordCloud, STOPWORDS
import json
import base64
import io
import ast

import dash  # (version 1.12.0) pip install dash
from dash.dependencies import Input, Output, State

# ------------------------------------------------------------------------------
# The layout was placed on a separate file for organizational reasons.
# The variables related to this layout were also put aside
from layout import *
modo_desarrollador = True


def boolean_distance(str1: str, str2: str) -> int:
    """
    Return distance between two lists of boolean.
    :param str1: First list of boolean
    :param str2: Second list of boolean
    :return: number of elements in common between the two input strings
    """
    r1_boolean = np.array(list(str1), dtype=int)
    r2_boolean = np.array(list(str2), dtype=int)
    return sum(r1_boolean != r2_boolean)

def distance(sol1: list, sol2: list) -> float:
    """
    Distance between two quasi-optimal solutions
    :param sol1: first solution
    :param sol2: second solution
    :return: distance
    """
    c1 = sol1[1] / max_profit
    c2 = sol2[1] / max_profit
    p1 = sol1[2] / max_cost
    p2 = sol2[2] / max_cost
    euc_dist = math.sqrt((c1 - c2) ** 2 + (p1 - p2) ** 2)
    d_req = boolean_distance(sol1[3], sol2[3]) / len(sol1[3])
    d_stk = boolean_distance(sol1[4], sol2[4]) / len(sol1[4])
    return 1 * euc_dist + 1 * d_req + 1 * d_stk

def generar_filtros(keys):
    """
    Generates a boolean array that filter the solutions
    :param keys: list of strings that represent requerimients or stakeholders
    :return: boolean array
    """
    global data

    filtro = [True] * len(data)
    #For each solution
    for r in range(len(data)):
        #For each key
        for key in keys:
            #A key is composed by a category and an index. For example: "reqs,4" refers to index 4 in the 'reqs' array of a solution.
            (categoria, index) = key.split(',')
            #The filter's corresponding position to each solution mantains its True value if that solution includes all the req/stk of the keys
            filtro[r] = np.logical_and(filtro[r], data[categoria][r][int(index)] == '1')
    
    return filtro


distance_matrix = None
def get_distance_matrix():
    """
    Distance matrix calculated from the data
    :return: distance matrix
    """
    global distance_matrix
    if distance_matrix is None:
        # Calculate the distance between each pair of quasi-optimal solutions.
        distance_matrix = squareform(pdist(data.values, distance))
        print('se genero la distance_matrix')
    return distance_matrix

# Statistics--------------------------------------------------------------------------
def cluster_statistics(indices, nivel, n_generado_de_clusters):
    """
    Statistics of each cluster
    :param indices: list of boolean that indicates which rows are going to be clustered.
    :param nivel: level of clustering zoom.
    :n_generado_de_clusters: number of generated clusters (int)
    :return: dictionary of statistics
    """
    global data

    df = data.loc[indices]
    estadisticos = {}
    for c in range(1, n_generado_de_clusters+1):
        cluster_elements = df.loc[df["Level {}".format(nivel)] == str(c)]

        stat = {
            'n_elementos' : len(cluster_elements),
            'profit_mean' : cluster_elements.profit.mean(),
            'cost_mean' : cluster_elements.cost.mean(),
            'profit_SD' : cluster_elements.profit.std(),
            'cost_SD' : cluster_elements.cost.std()
            }

        estadisticos[c] = stat
    return estadisticos

## Plotting----------------------------------------
def fill(array):
    """
    Fills an array with empty dics
    :param array: array to be filled
    :return: the filled array
    """
    faltantes = MAXCLUST - len(array)
    for x in range(faltantes):
        array.append({})
    return array

def plot_wordclouds(indices, dim, categorias, nivel):
    """
    Generates a wordcloud for each cluster
    :param indices: list of boolean that indicates which rows are going to be clustered.
    :param dim: data column to get info from (string)
    :categorias: dict of categories to pair the data info
    :nivel: level of clustering zoom.
    :return: array of wordclouds
    """
    global data
    df = data.loc[indices]
    conjuntos_palabras = {}
    for x in list(set(df["Level {}".format(nivel)])):
        conjuntos_palabras[str(x)] = "" #preparo una lista de strings vacios, uno por cada cluster
    array_wordclouds = [{},{},{},{}]  # array para retornar los wordclouds generados

    # para cada renglón del dataset
    for r in df["id"]:
        # para cada req/stk
        for i in range(len(categorias)):
            # si se incluye el req/stk
            if df[dim][r][i] == '1':
                # para cada palabra asociada al req/stk
                for j in range(len(categorias[str(i)]['keys'])):
                    # se agrega esa palabra a la string del cluster
                    conjuntos_palabras[df["Level {}".format(nivel)][r]] += categorias[str(i)]['keys'][j] + ' '

    for c in list(set(df["Level {}".format(nivel)])):  # se crea una nube de palabras por cada cluster
        wordcloud = WordCloud(width=800, height=400,
                              background_color='white',
                              stopwords=STOPWORDS,
                              min_font_size=8,
                              collocations=False).generate(conjuntos_palabras[c])
        # plot the WordCloud image   
        fig = px.imshow(wordcloud)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, b=0, t=0))

        array_wordclouds[int(c)-1] = fig

    return array_wordclouds

def algoritmo_clustering(indices, n_deseado_de_clusters, nivel):
    """
    Hierarchical clustering on the dataframe rows indicated by indeces parameter.
    :param indices: list of boolean that indicates which rows are going to be clustered.
    :n_deseado_de_clusters: maximum number of clusters to be generated.
    :param nivel: level of clustering zoom.
    :return: linkage matrix, number of generated clusters.
    """
    global data
    
    # filter rows and columns according to indices
    dist_matrix_filtrada = pd.DataFrame.to_numpy((pd.DataFrame(get_distance_matrix())).loc[indices, indices])
    # get linkage matrix for hierarchical clustering
    linkage_matrix = linkage(dist_matrix_filtrada, method="complete")

    # get clusters
    clusters = fcluster(linkage_matrix, n_deseado_de_clusters, criterion='maxclust')
    n_generado_de_clusters = len(set(clusters))
    # if index = True, next(clusters) else None
    clusters = iter(clusters)
    data["Level {}".format(nivel)] = [str(next(clusters)) if valor else None for valor in indices] #esta guardando los clusters como float

    return linkage_matrix, n_generado_de_clusters

def plot_all(nivel, n_deseado_de_clusters, array_filtros):
    """
    Runs the clustering algorithm and generates a dendogram, cluster statistics and wordclouds, and a dispersion graph.
    :param nivel: level of clustering zoom.
    :n_deseado_de_clusters: maximum number of clusters to be generated.
    :return: control variables, graphs to be displayed.
    """
    global data

    error=False
    try:
        #Applies the filters on each stage of clustering (this avoids errors when zooming out after applying filters)
        for n in range(nivel+1):
            indices = np.logical_and(obtener_indices(n), array_filtros)
            if not(any(indices)):
                #An exception is raised if the resulting boolean array is all False
                raise Exception("There are no solutions that fulfill all restrictions")
            (linkage_matrix, n_generado_de_clusters) = algoritmo_clustering(indices, n_deseado_de_clusters, n)
    except:
        error=True
        return (error, True, [], {}, {}, {}, {}, {}, "", "", "", "", {}, {}, {}, {}, {})

    dn = ff.create_dendrogram(linkage_matrix)
    dn.update_xaxes(showticklabels=False)
    dn.update_yaxes(showticklabels=False)
    dn.update_layout(margin=dict(l=0, r=0, b=0, t=0))

    wcreq = plot_wordclouds(indices, "reqs", requirements, nivel)
    wcstk = plot_wordclouds(indices, "stks", stakeholders, nivel)

    estadisticos = cluster_statistics(indices, nivel, n_generado_de_clusters)
    stat = {1: "", 2: "", 3: "", 4: ""}
    for clus in range(1, n_generado_de_clusters+1):
        stat[clus] = "Cluster {}\nElement count: {}\nProfit mean:   {}\nProfit SD:     {}\nCost mean:     {}\nCost SD:       {}".format(clus, estadisticos[clus]['n_elementos'], estadisticos[clus]['profit_mean'], estadisticos[clus]['profit_SD'], estadisticos[clus]['cost_mean'], estadisticos[clus]['cost_SD'])

    pcg = px.scatter(data.loc[indices], x="profit", y="cost", color=("Level {}".format(nivel)), hover_data=['id'])
    pcg.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, b=0, t=0))

    #Disable zoomin if there are no clusters to choose
    deshabilitar_zoomin = (n_generado_de_clusters<=1)
    #You can't zoom in a cluster with less than 3 solutions
    options = [{'label': 'Cluster{}'.format(c), 'value': c, 'disabled': (estadisticos[c]['n_elementos'] <= 2)} for c in range(1, n_generado_de_clusters+1)]
    
    return (error, deshabilitar_zoomin, options, dn, wcreq[0], wcreq[1], wcreq[2], wcreq[3], stat[1], stat[2], stat[3], stat[4], wcstk[0], wcstk[1], wcstk[2], wcstk[3], pcg)

def obtener_indices(nivel):
    """
    Generates the boolean array used to filter the pareto-front by its level of clustering zoom
    :param nivel: level of clustering zoom.
    :return: boolean array
    """
    global data
    global cluster_por_nivel

    if nivel >= 1:
        # obtiene los indices de las filas cuya última columna de cluster coincide con
        # el ultimo cluster elegido. Es un array de booleanos.
        indices = data["Level {}".format(nivel-1)] == cluster_por_nivel[nivel-1]
    else:
        indices = [True] * len(data)
    return indices

def validate_files(list_upload):
    data_isok = False
    reqs_isok = False
    stks_isok = False
    error_list = []

    if "pareto_front.json" in list_upload.keys():
        content_type, content_string = list_upload["pareto_front.json"].split(',')
        decoded = base64.b64decode(content_string)

        dataframe = pd.read_json(io.BytesIO(decoded), orient='index', dtype={'reqs': str, 'stks': str})
        if set(['id','profit','cost','reqs','stks']).issubset(dataframe.columns):
            if (len(dataframe) >= 3):
                data_isok = True
            else: error_list.append("The file 'pareto_front.json' must have at least 3 elements")
        else: error_list.append("The file 'pareto_front.json' does not meet the standard (it must have 'id','profit','cost','reqs' and 'stks' fields)")
    else: error_list.append("The file 'pareto_front.json' is missing")

    if "requirements.json" in list_upload.keys():
        content_type, content_string = list_upload["requirements.json"].split(',')
        decoded = ast.literal_eval((base64.b64decode(content_string)).decode("UTF-8"))

        if data_isok:
            if (len(decoded) == len(dataframe['reqs'][0])):
                if (("id" in decoded['0'].keys()) and ("keys" in decoded['0'].keys())):
                    reqs_isok = True
                else: error_list.append("The file 'requirements.json' does not meet the standard (it must have 'id' and 'keys' fields)")
            else: error_list.append("The file 'requirements.json' do not fit the lenght of 'pareto_front.json' 'reqs' field")
    else: error_list.append("The file 'requirements.json' is missing")

    if "stakeholders.json" in list_upload.keys():
        content_type, content_string = list_upload["stakeholders.json"].split(',')
        decoded = ast.literal_eval((base64.b64decode(content_string)).decode("UTF-8"))

        if data_isok:
            if (len(decoded) == len(dataframe['stks'][0])):
                if (("id" in decoded['0'].keys()) and ("keys" in decoded['0'].keys())):
                    stks_isok = True
                else: error_list.append("The file 'stakeholders.json' does not meet the standard (it must have 'id' and 'keys' fields)")
            else: error_list.append("The file 'stakeholders.json' do not fit the lenght of 'pareto_front.json' 'stks' field")
    else: error_list.append("The file 'stakeholders.json' is missing")

    return error_list
# ------------------------------------------------------------------------------

app = dash.Dash(__name__)
# App layout
app.title = "ParetoFrontExploration"
app.layout = layout

# ------------------------------------------------------------------------------

@app.callback(
    [Output(component_id='btn-continue',  component_property='disabled'),
     Output(component_id='error_list',    component_property='children')],
    [Input(component_id='upload-data',    component_property='contents')],
    [State(component_id='upload-data',    component_property='filename')]
)
def upload_data(list_contents, list_filenames):
    """
    Callback function for uploading the dataframe.
    :content: .json file that contains the dataframe.
    :return: a boolean that disables the "Continue" button and a graph of the dataframe.
    """
    global data
    global requirements
    global stakeholders
    global palabras_clave

    continue_disabled = True
    list_upload = dict(zip(list_filenames, list_contents))
    error_list = validate_files(list_upload)

    if (error_list == []):
        continue_disabled = False

        content_type, content_string = list_upload["pareto_front.json"].split(',')
        decoded = base64.b64decode(content_string)
        data = pd.read_json(io.BytesIO(decoded), orient='index', dtype={'reqs': str, 'stks': str})
        
        content_type, content_string = list_upload["requirements.json"].split(',')
        requirements = ast.literal_eval((base64.b64decode(content_string)).decode("UTF-8"))
        
        content_type, content_string = list_upload["stakeholders.json"].split(',')
        stakeholders = ast.literal_eval((base64.b64decode(content_string)).decode("UTF-8"))

        palabras_clave = []
        for x in range(len(requirements)):
            palabras_clave.append({
                'label' : requirements[str(x)]['id'],
                'value' : "reqs,{}".format(x)
                })
        for x in range(len(stakeholders)):
            palabras_clave.append({
                'label' : stakeholders[str(x)]['id'],
                'value' : "stks,{}".format(x)
                })


    reporte_errores = ""
    for error in error_list:
        reporte_errores += "\n* " + error

    return (continue_disabled, reporte_errores)

@app.callback(
    Output(component_id='page_content',    component_property='children'),
    [Input(component_id='btn-continue',     component_property='n_clicks')],
    [State(component_id='upload-data',      component_property='contents')]
)
def start(n_clicks, content):
    """
    Callback function that updates the layout.
    :n_clicks: not used
    :content: .json file that contains the dataframe.
    :return: the main layout.
    """

    global data
    global max_cost
    global max_profit
    global start_layout
    global main_layout
    global array_filtros

    layout = start_layout

    if not(data is None):
        max_cost = max(data["cost"])
        max_profit = max(data["profit"])
        layout = main_layout
        array_filtros = [True] * len(data)

    return layout


@app.callback(
    [#Controles
     Output(component_id='cluster_seleccionado',    component_property='value'),
     Output(component_id='slider_nivel',            component_property='marks'),
     Output(component_id='slider_nivel',            component_property='value'),  
     Output(component_id='btn-restore',             component_property='disabled'),  
     Output(component_id='btn-zoomout',             component_property='disabled'),
     Output(component_id='filtros-dropdown',        component_property='options'),
     Output(component_id='error_message',           component_property='displayed'),
     Output(component_id='btn-zoomin',              component_property='disabled'),
     Output(component_id='cluster_seleccionado',    component_property='options'),
     #Graficos
     Output(component_id='dendrogram_graph',        component_property='figure'),
     Output(component_id='wordcloud_req_cluster1',  component_property='figure'),
     Output(component_id='wordcloud_req_cluster2',  component_property='figure'),
     Output(component_id='wordcloud_req_cluster3',  component_property='figure'),
     Output(component_id='wordcloud_req_cluster4',  component_property='figure'),
     Output(component_id='textarea_cluster1',       component_property='value'),
     Output(component_id='textarea_cluster2',       component_property='value'),
     Output(component_id='textarea_cluster3',       component_property='value'),
     Output(component_id='textarea_cluster4',       component_property='value'),
     Output(component_id='wordcloud_stk_cluster1',  component_property='figure'),
     Output(component_id='wordcloud_stk_cluster2',  component_property='figure'),
     Output(component_id='wordcloud_stk_cluster3',  component_property='figure'),
     Output(component_id='wordcloud_stk_cluster4',  component_property='figure'),
     Output(component_id='profit_cost_graph',       component_property='figure')],

    [ Input(component_id='btn-restore',             component_property='n_clicks'),
      Input(component_id='btn-zoomout',             component_property='n_clicks'),
      Input(component_id='btn-zoomin',              component_property='n_clicks'),
      Input(component_id='slider_num_clusters',     component_property='value'),
      Input(component_id='filtros-dropdown',        component_property='value')],
    [ State(component_id='cluster_seleccionado',    component_property='value'),
      State(component_id='slider_nivel',            component_property='marks'),
      State(component_id='slider_nivel',            component_property='value')]
)
def update_graphs(n_clicks_restore, n_clicks_out, n_clicks_in, num_clusters, keys, option_slctd, marcas_de_nivel, nivel):
    """
    Callback function used to update the graphs.
    :n_clicks_out: number of clicks on the "zoom out" button.
    :n_clicks_in: number of clicks on the "zoom in" button.
    :num_clusters: maximum number of clusters to be generated.
    :option_slctd: cluster selected to zoom in.
    :marcas_de_nivel: marks in the clustering zoom level slider.
    :param nivel: level of clustering zoom.
    :return: control variables and graphs.
    """
    global data
    global palabras_clave
    global array_filtros
    global cluster_por_nivel

    # get triggered event from callback_context
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Filtrado
    if ctx.triggered:
        if trigger_id == 'btn-restore':
            cluster_por_nivel = []
            while (nivel>0):
                del data["Level {}".format(nivel)]
                nivel -= 1

        if trigger_id == 'btn-zoomout':
            cluster_por_nivel.pop()
            del data["Level {}".format(nivel)]
            nivel -= 1

        if trigger_id == 'btn-zoomin':
            nivel += 1
            marcas_de_nivel[nivel] = str(nivel)
            cluster_por_nivel.append(str(option_slctd))

        if trigger_id == 'filtros-dropdown':
            array_filtros = generar_filtros(keys)

    deshab_restore = (nivel==0)
    deshab_zoomout = (nivel==0)

    # Plot
    return (None, marcas_de_nivel, nivel, deshab_restore, deshab_zoomout, palabras_clave) + plot_all(nivel, num_clusters, array_filtros)

#______________________________________________________________________________

#  Read Pareto front in JSON format.
#  There is a little problem with reqs and stks attributes. They are read as integers and it may produce some errors.
data = None 
max_cost = None 
max_profit = None

array_filtros = []

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=modo_desarrollador,dev_tools_props_check=modo_desarrollador)