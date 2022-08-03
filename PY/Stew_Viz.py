# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 14:29:13 2020

@author: csucuogl
"""

#%% START


import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sys
import seaborn as sns
import plotly.graph_objects as go
print (sys.prefix)

#%% IMPORT and Prepare Data
stew = gpd.read_file( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\NYC2017_StewMap.shp" )
grid = gpd.read_file( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\NYC_Grid800_18N_2.shp" )

grid['id'] = grid['id'].astype(int).astype(str)
grid = grid.set_index( 'id' )

#Remove some very large groups
stew['area'] = stew.geometry.area
stew = stew[ stew['area']/10000000 < 10000 ]
#%%
#Spatial join, Groups are multipled by the times they intersect with a grid. index_right column is the grid id.
stew_grid = gpd.sjoin(stew, grid, how="inner", op='intersects').sort_values(by='OrgName')

# Summarize Data
stew_grid = stew_grid[['OrgName','PrimFocus','geometry','id_str','_boroname','_ntaname','YrFnd_Num']]
stew_grid.head(5)

#%% Stew Year
stew2 = gpd.read_file( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\NYC2017_StewMap.shp" )

stew2 = stew2[ ~pd.isna( stew2['YrFnd_Num'] )]
stew2['YrFnd_Num'] = stew2['YrFnd_Num'].astype(int)

pt2 = pd.pivot_table(data = stew2[['PrimFocus','YrFnd_Num']] , index = 'PrimFocus' , columns = 'YrFnd_Num' , aggfunc=len ) 
sns.heatmap( pt2 , cmap = 'Reds')

#%%  Count the number of groups in each grid
temp = stew_grid.groupby( by = 'id_str' ).size().reset_index()
temp = temp.set_index( 'id_str')
temp.columns = ['GroupCount']
grid = grid.join( temp, on = 'id' )

grid = grid.reset_index()
grid['id'] = grid['id'].astype( float ).astype( int ).astype(str)
grid = grid[['id','GroupCount']]
grid.sample(5)


#%% Remove groups that are city wide. I'll add them to each plot individually. 
dfc = stew_grid.groupby( by = 'OrgName' ).size().reset_index()
dfc.columns = ['OrgName','count']
dfc = dfc.sort_values( by = 'count' )
df_nyc = dfc[ dfc['count'] > 2900 ]
stew_gridB =  stew_grid[ stew_grid['OrgName'].isin( df_nyc['OrgName'].tolist() ) ]
stew_grid = stew_grid[ ~stew_grid['OrgName'].isin( df_nyc['OrgName'].tolist() ) ]

stew_grid = stew_grid[ stew_grid['PrimFocus'] != 'Other' ]
stew_grid = stew_grid.dropna( axis = 0 , subset = ['PrimFocus'] )
stew_grid['PrimFocus'] = [ r.split('(')[0] for i,r in stew_grid['PrimFocus'].iteritems() ]
stew_grid.head(5)
#%%
stew_grid = stew_grid[ ~ pd.isna( stew_grid._ntaname ) ]
stew_grid =stew_grid[~stew_grid._ntaname.str.contains('park-cemetery') ]
stew_grid.head(5)

#%% Year Grid

stew_gridB.drop('geometry',axis = 1).to_csv( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\App_Data\prim_Ek.csv" , index=False)


#%%
gr2 = stew_gridB.groupby( ['OrgName', 'PrimFocus', 'YrFnd_Num'] ).size().reset_index()
gr2 = gr2[ gr2.columns[:-1]]
pt2 = pd.pivot_table( data = gr2.drop('OrgName',axis = 1) , columns = 'YrFnd_Num' , index = 'PrimFocus' , aggfunc = len )

pt2.fillna(0).astype(int)

#%%

name_table = pd.pivot_table(data = gr2 ,index= 'PrimFocus' ,
                                columns= 'YrFnd_Num' , 
                                values='OrgName',
                                aggfunc=lambda x: '--'.join(x))
name_table = name_table.unstack().reset_index().dropna(axis=0)
name_table .columns = name_table .columns.tolist()[:-1] + ['GroupNames']

name_table

#%%

name_table.to_csv( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\App_Data\Time_Names.csv")

#pt2.to_csv( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\App_Data\Time.csv")

#%%

t1 = pd.DataFrame( index = name_table.index.tolist() , columns = list(range(1840,2020))  )
t1.columns.name = 'YrFnd_Num' 
t1.index.name = 'PrimFocus'

t1

#%%
stew_grid.drop('geometry',axis = 1).to_csv( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\App_Data\prim.csv" , index=False)

#%%Import geometry as geojson. Projection is WGS84
#-------------------- PLOTLY ----------------------------------
#Prepare Plotly and Format Geojson

import json
import plotly.express as px

with open( r"C:\Users\csucuogl\Desktop\WORK\TNOC\Data\Geo_Grid_wgs843.geojson" ) as f:
  counties = json.load(f)

#Convert data to list like geojson
sources=[{ "type": "Feature", 'geometry': feat['geometry'] , 'id':feat['properties']['id_str'] } for feat in counties['features']]
s2 = dict( type = 'FeatureCollection' , features = sources ) #Create begining and end


# %% Bubble Chart -> Prepare Data

gr = stew_grid.groupby( ['OrgName', 'PrimFocus', '_ntaname','_boroname'] ).size().reset_index()
gr = gr[ gr.columns[:-1]]
pt = pd.pivot_table( data = gr.drop('OrgName',axis = 1) , columns = ['_boroname','_ntaname'] , index = 'PrimFocus' , aggfunc = len )
#pt = pt.reindex( pt.sum( axis = 1).sort_values( ascending = False).index )

pt = pt.unstack().reset_index()
pt.columns = pt.columns.tolist()[:-1] + ['GroupCount']
pt = pt.dropna( axis = 0 , subset = ['GroupCount'] )
pt = pt.fillna(value = 0)

pt.head(5)

#%% Plot Choroplth

choro = go.Figure(go.Choroplethmapbox(
                      geojson = s2,
                      locations = grid['id'],
                      z = grid['GroupCount'],
                      colorscale = "OrRd",
                      zmin = 0, zmax = 70,
                      marker_opacity=0.7 , marker_line_width=0,
                      ))

choro.update_layout(
                  width=900, height=900 ,
                  mapbox_style="carto-positron",
                  mapbox_zoom=9.5,
                  mapbox_center = dict(lat=40.743999,lon=-73.964262),
                  hoverlabel=dict(
                                  bgcolor="white", 
                                  font_size=12, 
                                  font_family="Futura PT"
                              )
                  )

#%%

nums = enumerate( pt['_ntaname'].unique().tolist() )
tt = pd.DataFrame.from_dict( nums )
tt.columns = ['nos','neis']

a = []
for i,row in pt.iterrows():
      temp = tt[ tt.neis == row['_ntaname'] ]
      a.append( temp['nos'].values[0] )

pt['_ntaname2'] = a

# %% Plot Bubble Chart

fig = go.Figure(
  data=go.Scatter(
    x= [ pt._boroname , pt._ntaname ] ,
    y= pt['PrimFocus'],
    mode='markers',
    marker=dict( 
      size = pt['GroupCount'] * 1.5 ,
      line_width=0 ,
      opacity = 0.5 ,
      color = 'crimson')
    ),
  layout = dict(
    xaxis=dict(
      range=[ -1 , len(pt._ntaname.unique()) ]
    ),
    yaxis=dict(
      range=[ -0.1 , len(pt.PrimFocus.unique())-0.9 ]
    ),
    font = dict(
      family= 'Futura PT, monospace',
      size= 5,
      color= '#7f7f7f'
    ),
    dragmode = 'select'
    )
)

fig.update_layout(width=1500, height=500,plot_bgcolor='white',
  margin=dict( l=30,r=30,b=30,t=50,pad=0 )
  )
fig.update_yaxes(tickangle=0 )
fig.update_yaxes(showgrid=True, gridwidth=0.05, gridcolor='#e3e0dd')
fig.update_xaxes(showgrid=True, gridwidth=0.15, gridcolor='lightgrey')


# %%

from ipywidgets import interactive, HBox, VBox
