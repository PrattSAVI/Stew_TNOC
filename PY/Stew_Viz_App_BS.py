# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 14:29:13 2020

@author: csucuogl
"""

# Import Dependencies
import pandas as pd
import json
import numpy as np
import plotly.graph_objects as go
import warnings
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
warnings.filterwarnings( "ignore" )

# -------------------  Import and Clean  -------------------
grid = pd.read_csv( "https://raw.githubusercontent.com/PrattSAVI/IdeasTesting/master/grid.csv" )
prim = pd.read_csv( r"https://raw.githubusercontent.com/PrattSAVI/IdeasTesting/master/prim.csv" )
eks = pd.read_csv( r'https://raw.githubusercontent.com/PrattSAVI/IdeasTesting/master/prim_Ek.csv')

# Include Groups Bigger then NYC to time
eks['PrimFocus'] = eks['PrimFocus'].astype(str)
eks['PrimFocus'] = [r.split(' and')[0] for i,r in eks.PrimFocus.iteritems()]
eks['PrimFocus'] = [r.split(',')[0] for i,r in eks.PrimFocus.iteritems()]
eks = eks[ eks['PrimFocus'] != 'Other']

with open( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\Geo_Grid_wgs843.geojson" ) as f:
  counties = json.load(f)

#Convert data to list like geojson
sources=[{ "type": "Feature", 'geometry': feat['geometry'] , 'id':feat['properties']['id_str'] } for feat in counties['features']]
s2 = dict( type = 'FeatureCollection' , features = sources ) #Create begining and end

#Reduce Number of Groups based on Group Counts
test = prim[['_ntaname']].groupby( '_ntaname' ).size().reset_index()
test.columns = ['nta','counts']
test = test[ test['counts'] > 120 ]
prim = prim[ prim['_ntaname'].isin( test['nta'] ) ]

#Shorten Names for NTA and PrimFocus
prim['_ntaname'] = [r.split('-')[0] for i,r in prim._ntaname.iteritems()]
prim['_ntaname'] = [r.split('(')[0] for i,r in prim._ntaname.iteritems()]
prim['PrimFocus'] = [r.split(' and')[0] for i,r in prim.PrimFocus.iteritems()]
prim['PrimFocus'] = [r.split(',')[0] for i,r in prim.PrimFocus.iteritems()]

backcolor = '#f2f3f4'
# -------------------  Definitions for Graphics  -------------------

def map_maker( geodata , df , w , h ): # Create Choropleth map , with Group Count

    choro = go.Figure( 
        go.Choroplethmapbox(
            geojson = geodata,
            locations = df['id'],
            z = grid['GroupCount'],
            colorscale = "OrRd",
            zmin = 0, zmax = 70,
            marker_opacity=0.7 , marker_line_width=0,
            showscale = True,
            colorbar = dict(
                title = '# of <br>Groups',
                thicknessmode="pixels", thickness=15,
                nticks=5,
                yanchor="bottom", y = 0,
                len=0.95,lenmode='fraction',
                outlinewidth=0,
                ypad = 5,
                xpad = 0
            )
        )
    )

    choro.update_layout(
        dragmode = 'select',
        margin = dict( l=0,r=0,t=0,b=0),
        width=w, height=h ,
        mapbox_style="carto-positron",
        mapbox_zoom=9,
        mapbox_center = dict(lat=40.71,lon=-73.96),
        plot_bgcolor = backcolor,
        paper_bgcolor = backcolor,
        hoverlabel=dict(
            bgcolor="white", 
            font_size=12, 
            font_family="Futura PT"
            ),
        showlegend = False
        )


    return dict(
        data = choro._data,
        layout = choro._layout
    )

def bubble_maker( prim , w , h ): # Bubble Chart for NTA's
    global backcolor
    t1 = pd.pivot_table( data = prim[['_boroname','_ntaname','PrimFocus']] , columns = ['_boroname','_ntaname'] , index = 'PrimFocus' , aggfunc = len ) 
    for col in t1.columns: t1[col].values[:] = 0

    prim = prim.drop('YrFnd_Num' , axis = 1)

    gr = prim[ prim['select'] == True ].groupby( ['OrgName', 'PrimFocus', '_ntaname','_boroname'] ).size().reset_index()
    gr = gr[ gr.columns[:-1]]
    pt = pd.pivot_table( data = gr.drop('OrgName',axis = 1) , columns = ['_boroname','_ntaname'] , index = 'PrimFocus' , aggfunc = len )

    name_table = pd.pivot_table(data = gr ,index= 'PrimFocus' ,
                                     columns= ['_boroname','_ntaname'] , 
                                     values='OrgName',
                                     aggfunc=lambda x: '--'.join(x))

    pt = t1 + pt

    pt = pt.unstack().reset_index()
    pt.columns = pt.columns.tolist()[:-1] + ['GroupCount']
    pt = pt.fillna(value = 0)

    name_table = name_table.unstack().reset_index()
    name_table .columns = name_table .columns.tolist()[:-1] + ['GroupNames']
    name_table['GroupNames'] = name_table['GroupNames'].replace('--','<br>' , regex = True)
    #print( pt['GroupCount'].min() , pt['GroupCount'].max() ) 

    fig = go.Figure( go.Scatter( #Figure
        x= [pt._boroname ,pt._ntaname] ,
        y= pt['PrimFocus'] ,
        mode='markers',
        #hovertemplate ='<b>Groups</b>: <br>%{text}',
        text = name_table['GroupNames'],
        marker=dict( 
            size = pt['GroupCount'] * 4  ,
            line_width=0 , 
            opacity = 0.6 , 
            color = 'crimson')
        )
                    )

    fig.update_layout( # Layout
        margin = dict( l=0,r=0,t=0,b=80),
        dragmode = 'select',
        width = w , height = h,
        plot_bgcolor = backcolor,
        paper_bgcolor = backcolor,
        font = dict(
            family= 'Futura PT, monospace',
            size= 12,
            color= '#7f7f7f'
            ),
        xaxis=dict(
            range=[ -1 , len(pt._ntaname.unique()) + 0.0 ]
            ),
        yaxis=dict(
            range=[ -0.5 , len(pt.PrimFocus.unique())-0.5 ]
            ),
        )
    
    fig.update_layout( # Hover Template
        hoverlabel=dict(
            bgcolor="white", 
            font_size=12, 
            font_family='Futura PT, monospace',
        )
    )
    fig.update_xaxes(
        tickangle=90,
        showgrid=True, gridwidth=0.25, gridcolor='lightgrey'
        )

    fig.update_yaxes(showgrid=True, gridwidth=0.25, gridcolor='lightgrey')

    return dict(
        data = fig._data,
        layout = fig._layout
    )

def time_maker( prim ,w,h ): # Timeline
    global backcolor
    global eks # Groups Working in whole NYC
    eks['select'] = True

    col_pick = 'PrimFocus'

    prim = prim.append( eks )

    prim = prim[ ~pd.isna(prim['YrFnd_Num']) ]
    prim['YrFnd_Num'] = prim['YrFnd_Num'].astype(int)

    t1 = pd.pivot_table( data = prim[[col_pick,'YrFnd_Num']] , columns = 'YrFnd_Num' , index = col_pick , aggfunc = len ) 
    for col in t1.columns: t1[col].values[:] = 0

    prim = prim.drop( ['_ntaname','_boroname'] , axis = 1)
    gr = prim[ prim['select'] == True ].groupby( ['OrgName', col_pick, 'YrFnd_Num'] ).size().reset_index()
    pt = pd.pivot_table(data = gr[[col_pick, 'YrFnd_Num']] , index = col_pick , columns = 'YrFnd_Num' , aggfunc=len )
    
    try:
        pt = t1 + pt
    except:
        pt = t1
    
    pt = pt.unstack().reset_index()
    pt.columns = pt.columns.tolist()[:-1] + ['GroupCount']
    pt = pt.fillna(value = 0)

    name_table = pd.pivot_table(data = gr ,index= 'PrimFocus' ,
                                    columns= 'YrFnd_Num' , 
                                    values='OrgName',
                                    aggfunc=lambda x: '--'.join(x))

    name_table = name_table.unstack().reset_index()
    name_table .columns = name_table .columns.tolist()[:-1] + ['GroupNames']
    name_table['GroupNames'] = name_table['GroupNames'].replace('--','<br>' , regex = True)

    fig = go.Figure( 
        go.Scatter( #Figure
            x= pt['YrFnd_Num'] ,
            y= pt[ col_pick ] ,
            mode='markers',
            text =  name_table['GroupNames'],
            marker=dict( 
                size = pt['GroupCount'] * 10  ,
                line_width=0 , 
                opacity = 0.6 , 
                color = 'crimson')
            )
        )

    fig.update_layout( # Hover Template
        hoverlabel=dict(
            bgcolor="white", 
            font_size=12, 
            font_family='Futura PT, monospace',
        )
    )

    fig.update_layout( # Layout
        margin = dict( l=0,r=0,t=0,b=0),
        dragmode = 'select',
        width = w , height = h,
        plot_bgcolor = backcolor,
        paper_bgcolor = backcolor,
        font = dict(
            family= 'Futura PT, monospace',
            size= 12,
            color= '#7f7f7f'
            ),
        xaxis=dict( 
            range=[ int(prim['YrFnd_Num'].min())-5 , int(prim['YrFnd_Num'].max())+5 ],
            tickvals = np.linspace( 1840 , 2020 , 21  ),
            ),
        yaxis=dict( 
            range=[ -0.5 , len(pt.PrimFocus.unique())-0.5 ],
            ),
        )

    fig.update_xaxes(tickangle=90,showgrid=True, gridwidth=0.25, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridwidth=0.25, gridcolor='lightgrey')

    return dict(
        data = fig._data,
        layout = fig._layout
    )


# ---------------------  LEGEND  -----------------------------

# Legend Timeline
legfig = go.Figure( # Legend -> Timeline Figure
    go.Scatter( 
        x= [1,2,3] ,
        y= [ 1,1,1] ,
        mode='markers + text',
        text = [1,2,3],
        textposition="bottom center",
        hoverinfo = 'skip',
        marker=dict( 
            size = [10,20,30]  ,
            line_width=0 , 
            opacity = 0.6 , 
            color = 'crimson')
        )
                    )

legfig.update_layout( # Legend -> Timeline Layout
    title = dict(
        text = 'Timeline Legend',
        y = 0.9,x = 0.45 
        ),
    margin = dict( l=0,r=0,t=0,b=0),
    width = 230 , height = 100,
    plot_bgcolor = backcolor,
    paper_bgcolor = backcolor,
    font = dict(
        family= 'Futura PT, monospace',
        size= 16,
        color= '#7f7f7f'
        ),
    xaxis=dict( range=[ 0,4 ] ),
    yaxis=dict( range=[ 0.5,1.5 ] ),
    )
legfig.update_xaxes(showticklabels=False , showgrid = False, zeroline=False )
legfig.update_yaxes(showticklabels=False , showgrid = False, zeroline=False )

# Legend Bubble

bubfig = go.Figure( # Legend -> Bubble Figure
    go.Scatter( 
        x= [1,3,5,7,9] ,
        y= [ 1,1,1,1,1 ] ,
        mode='markers + text',
        text = [2,4,6,8,10],
        textposition="bottom center",
        hoverinfo = 'skip',
        marker=dict( 
            size = [8,16,24,32,40]  ,
            line_width=0 , 
            opacity = 0.6 , 
            color = 'crimson')
        )
                    )

bubfig.update_layout( # Legend -> Timeline Layout
    title = dict(
        text = 'Neighborhood Legend',
        y = 0.9 , x = 0.1 
        ),
    margin = dict( l=0,r=0,t=0,b=0),
    width = 300 , height = 100,
    plot_bgcolor = backcolor,
    paper_bgcolor = backcolor,
    font = dict(
        family= 'Futura PT, monospace',
        size= 16,
        color= '#7f7f7f'
        ),
    xaxis=dict( range=[ 0 , 11 ] ),
    yaxis=dict( range=[ -0.5 , 3 ] ),
    )
bubfig.update_xaxes(showticklabels=False , showgrid = False ,zeroline=False )
bubfig.update_yaxes(showticklabels=False , showgrid = False ,zeroline=False )

# -------------------  Prepare Layout  -------------------
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div( #Main Div Container
        
            [   html.Div( # Title and Intro Paragraph
                    [
                        html.H3( 'Stew-MAP Exploration layout' ),
                        html.P( 'In numquam rerum voluptate in consequatur aut dignissimos. Distinctio consequatur atque dolores excepturi possimus. Optio ut quisquam aut illum. Sit voluptates aut qui officia autem dolore modi. Et aut et molestias deleniti sint voluptates nostrum qui.Recusandae unde dolorem distinctio quo cumque sed voluptatem et. At facere sint qui molestiae consequatur. Excepturi nemo facilis qui. Voluptas sint corporis voluptatem. Veniam ad et qui.<br>Saepe odio quas ut sit dolorem illo ullam et. Odit harum ullam aut. ' ),
                        html.P( 'Recusandae unde dolorem distinctio quo cumque sed voluptatem et. At facere sint qui molestiae consequatur. Excepturi nemo facilis qui. Voluptas sint corporis voluptatem. Veniam ad et qui.<br>Saepe odio quas ut sit dolorem illo ullam et. Odit harum ullam aut. Voluptatum qui odit veniam.' )
                    ],
                    className='row', style = {
                                            'marginBottom': '1em',
                                            'marginLeft': '3em',
                                            'marginRight': '0em',
                                            'marginTop': '2em',
                                            'width':1400 
                                            }
                ),
                html.Div( # Map & Timeline
                    [ html.Div([  # Map
                        dcc.Graph( id = 'g_map' , config={'displayModeBar': True , 'displaylogo': False , 'modeBarButtonsToRemove': ['lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'toggleHover', 'toImage'] } ,
                        figure = map_maker( s2 , grid , 680 , 375 ) 
                        )], className="col" ),

                    html.Div([
                        dcc.Graph( id = 'g_Time' , config={ 'displayModeBar': False } )
                        ], className="col" )
                    
                    ], 
                    className = "row" , style = { 
                                                'width':1395 ,
                                                'height':400 ,
                                                'marginLeft': '3em'
                                                } ,
                ),
                html.Div([ # Middle Text Portion
                    html.Div([ #Text is Here
                        html.H4( 'Where are the Stewards and What are They Doing?' ),
                        html.P('In numquam rerum voluptate in consequatur aut dignissimos. Distinctio consequatur atque dolores excepturi possimus. Optio ut quisquam aut illum. Sit voluptates aut qui officia autem dolore modi. Et aut et molestias deleniti sint voluptates nostrum qui.')
                    ], className = 'col-7' ),

                    html.Div([ # Legend is here
                        dcc.Graph( id = 'legend-time', figure = legfig , config={'displayModeBar': False,'staticPlot': True} )
                    ], className = 'col-2', style = { 
                                                    'marginTop': '0.6em',
                                                    'marginLeft': '0em',
                                                    'width' : '%90',
                                                     } 
                            ),

                    html.Div([ # Legend is here
                        dcc.Graph( id = 'legend-bubble', figure = bubfig , config={'displayModeBar': False,'staticPlot': True} )
                    ], className = 'col-3', style = { 'marginTop': '0.5em' } ),

                ],
                className='row', style = { 
                                        'width':1400,
                                        'marginBottom': '0em',
                                        'marginLeft': '3em',
                                        'marginRight': '0em',
                                        'marginTop': '1em', 
                                        }
                ),

                html.Div( #Main Bubble
                    dcc.Graph( id = 'g_bubble', config={'displayModeBar': False} ,
                    ),
                    className='row', style={
                                            'marginBottom': '2em',
                                            'marginLeft': '3em',
                                            'marginRight': '0em',
                                            'marginTop': '1em'

                                            }
                ),


        ] , className='row' , style={
            'background-color': backcolor,
            'marginBottom': '5em',
            'marginLeft': '2em',
            'marginRight': '2em',
            'marginTop': '0em',
            'width':1500,
            'margin-right': 'auto',
            'margin-left': 'auto'
            }
        
        )

# -------------------  Add Callbacks  -------------------
@app.callback( # Filter Bubble plot based on dropdown selection
    dash.dependencies.Output('g_bubble', 'figure'),
    [dash.dependencies.Input( 'g_map' , 'selectedData')] )
def update_bubble( selectedData ): # Update Bubble Plot by Selection on Map 
    if selectedData and selectedData != 0 :
        locs = [ i['location'] for i in selectedData['points'] ]
        trim = prim
        trim['select'] = False
        trim.loc[ trim['id_str'].isin( locs ) , 'select'] = True
    else:
        trim = prim
        trim['select'] = True
    return bubble_maker( trim , 1400 , 425 )

@app.callback( # Filter TIME plot based on dropdown selection
    dash.dependencies.Output('g_Time', 'figure'),
    [dash.dependencies.Input( 'g_map' , 'selectedData')] )
def update_time( selectedData ): # Update Bubble Plot by Selection on Map 
    if selectedData and selectedData != 0 :
        locs = [ i['location'] for i in selectedData['points'] ]
        trim = prim
        trim['select'] = False
        trim.loc[ trim['id_str'].isin( locs ) , 'select'] = True
    else:
        trim = prim
        trim['select'] = True
    return time_maker( trim , 685 , 375 )

#app.css.config.serve_locally = True
#app.scripts.config.serve_locally = True

if __name__ == '__main__':
    app.run_server(debug=True)


