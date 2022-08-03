# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 14:29:13 2020

@author: csucuogl
"""

import pandas as pd
import json
import numpy as np
import plotly.graph_objects as go
import warnings
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import requests
warnings.filterwarnings( "ignore" )

print("libs loaded")

# Import data
folder = 'https://raw.githubusercontent.com/PrattSAVI/Stew_TNOC/main/DATA/'
grid = pd.read_csv( folder + "grid.csv" )
prim = pd.read_csv( folder + "prim.csv" )
eks = pd.read_csv( folder + "prim_Ek.csv" )

print("data loaded")

# Include Groups Bigger then NYC to time
eks['PrimFocus'] = eks['PrimFocus'].astype(str)
eks['PrimFocus'] = [r.split(' and')[0] for i,r in eks.PrimFocus.iteritems()]
eks['PrimFocus'] = [r.split(',')[0] for i,r in eks.PrimFocus.iteritems()]
eks = eks[ eks['PrimFocus'] != 'Other']

link = 'https://raw.githubusercontent.com/PrattSAVI/Stew_TNOC/main/DATA/Geo_Grid_wgs843.geojson'
f = requests.get(link)
counties = f.json()

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
        plot_bgcolor = 'white',
        paper_bgcolor = 'white',
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

    fig.update_xaxes(
        tickangle=90,
        showgrid=True, gridwidth=0.25, gridcolor='lightgrey'
        )
    
    fig.update_layout( # Hover Template
        hoverlabel=dict(
            bgcolor="white", 
            font_size=12, 
            font_family='Futura PT, monospace',
        )
    )

    fig.update_yaxes(showgrid=True, gridwidth=0.25, gridcolor='lightgrey')
    #fig.update_xaxes(ticks="ou", tickwidth=2, tickcolor='crimson', ticklen=10 )
    return dict(
        data = fig._data,
        layout = fig._layout
    )

def time_maker( prim ,w,h ): # Timeline

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
        plot_bgcolor = 'white',
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

# Prepare Layout
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.layout = html.Div( #Main Div Container
      
        [   
            html.Div(
                [ html.Div(  #MAP
                    dcc.Graph( id = 'g_map' , config={'displayModeBar': True , 'displaylogo': False , 'modeBarButtonsToRemove': ['lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'toggleHover', 'toImage'] } ,
                    figure = map_maker( s2 , grid , 685 , 375 ) 
                    ),
                    className="six columns", style={
                                            'marginBottom': '0em',
                                            'marginLeft': '0em',
                                            'marginRight': '0em',
                                            'marginTop': '0em',
                                            }
                ),
                html.Div( #Time Line
                    dcc.Graph( id = 'g_Time' , config={ 'displayModeBar': False } ,
                    #figure = time_maker( prim , 685 , 375 ) 
                    ),
                    className="six columns", style={
                                            'marginBottom': '0em',
                                            'marginLeft': '3em',
                                            'marginRight': '0em',
                                            'marginTop': '0em',
                                            }
                )] , className = "row" , style = { 'width':1400 , 'height':400 } ,
            ),
            html.Div( #Main Bubble
                dcc.Graph( id = 'g_bubble', config={'displayModeBar': False} ,
                ),
                className='row', style={
                                        'marginBottom': '0em',
                                        'marginLeft': '0em',
                                        'marginRight': '1em',
                                        'marginTop': '1em'
                                        }
            ),


        ] , className='row' , style={
            'background-color': 'white',
            'marginBottom': '2em',
            'marginLeft': '2em',
            'marginRight': '1em',
            'marginTop': '1em'
            }
        
        )

#For Heroku
server = app.server

# Add Callbacks
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


