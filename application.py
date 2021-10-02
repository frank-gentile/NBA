import dash  # (version 1.12.0) pip install dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import pandas as pd
import requests
import bs4 as bs
from scipy.stats import ttest_ind


def formatLinks(player_names,year):
    links = []
    special = ['Anthony Davis']

    if type(player_names)==str:
        first_name = player_names.split(" ")[0]
        last_name = player_names.split(" ")[1]
        first_letter = last_name[0].casefold()
        first_five = last_name[0:5].casefold()
        first_two = first_name[0:2].casefold()
        links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'01/gamelog/'+str(year)
        if player_names in special:
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'02/gamelog/'+str(year)
    else:
        for player in player_names:
            first_name = player.split(" ")[0]
            last_name = player.split(" ")[1]
            first_letter = last_name[0].casefold()
            first_five = last_name[0:5].casefold()
            first_two = first_name[0:2].casefold()
            link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'01/gamelog/'+str(year)
            if player in special:
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'02/gamelog/'+str(year)
            links.append(link)
    return(links)


def getPlayerData(link):
    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.content,'lxml')
    tables = soup.findAll('table')
    html = resp.text
    soup = bs.BeautifulSoup(html, 'lxml')
    links = soup.find_all('img')
    pic = links[1]['src']
    table = tables[-1]
    points = []
    table_headers = []
    for tx in table.findAll('th'):
        table_headers.append(tx.text)
        if len(table_headers)==30:
            break
    table_headers.pop(0)
    player_data = pd.DataFrame(data=None, columns = table_headers)
        
    if table.findParent("table") is None:
        for row in table.findAll('tr')[1:]:
            line = []
            for obs in row.findAll('td'):
                dummy = obs.text
                line.append(dummy)
                if line[-1]=="Did Not Play" or line[-1]=='Inactive' or line[-1]=='Did Not Dress':
                    zeroes = [0]*29
                    zeroes[:len(line)-1] = line[:-1]
                    zeroes[0]=len(player_data)+1
                    [str(i) for i in zeroes]
                    df2 = pd.DataFrame(zeroes).T
                    df2.columns = table_headers
                    player_data = player_data.append(df2)

            if len(line) == len(table_headers):
                df2 = pd.DataFrame(line).T
                df2.columns = table_headers
                player_data = player_data.append(df2)
    player_data = player_data.reset_index()
    player_data = player_data.drop(['index','G'],axis=1)
    player_data = player_data.drop(player_data.columns[3],axis=1)
    return player_data, pic

def getFantasyPoints(player_data):
    player_data['FPoints'] = 0
    
    for index, row in player_data.iterrows():
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10) or (int(row['PTS'])>=10 and int(row['AST'])>=10) or (int(row['AST'])>=10 and int(row['TRB'])>=10) or \
        (int(row['PTS'])>=10 and int(row['BLK'])>=10) or (int(row['PTS'])>=10 and int(row['STL'])>=10):
            dd = 1
        else: 
            dd = 0
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10 and int(row['AST'])>=10):
            td=1
        else:
            td=0
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10 and int(row['AST'])>=10) and (int(row['BLK'])>=10 or int(row['STL'])>=10):
            qd = 1
        else: 
            qd=0
        player_data.at[index,'FPoints'] = int(row['FG'])-int(row['FGA'])+int(row['FT'])-int(row['FTA'])+int(row['3P'])+int(row['TRB'])+int(row['AST'])+int(row['STL'])+int(row['BLK']) \
            -int(row['TOV'])+int(row['PTS'])+5*dd+10*td+1000*qd
    return player_data


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
application = app.server
app.title = 'Nooice Trade Analysis'
suppress_callback_exceptions=True

app.layout = dbc.Container([
        html.Br(),
        dbc.Row(dbc.Col(html.H1("Nooice Trade Analysis Tool"),width={'size':'auto'}),align='center',justify='center'),
        html.Br(),
        dbc.Row(dbc.Col(dcc.Markdown(
            '''Hello and welcome! This tool was developed to help justify and test potential trades for fantasy basketball.
            You can start with entering a player's name to view their stats, fantasy points and moving averages, then enter 
            a trade to perform a two sample t test for equivalence. If the p-valye is greater than 0.10, there is not enough evidence to
            reject the null that they are statistically different. If such a trade were to be accepted, it would be automatically approved.
            Enjoy!
            '''
        ),width=12,align='center'),align='center',justify='center'),



        html.Br(),
        dbc.Row(
            dbc.Col([
                html.Label('Player = '),
                dcc.Input(id='player_names',value='Stephen Curry'),
                ],width=12),align='center',justify='center'),
        dbc.Row(
            dbc.Col(
                dbc.Button('Update', id='submit-val', n_clicks=0,color='primary'),width=12
        ),align='center',justify='center'),
        dbc.Row(
            [dbc.Col(
                html.Img(id='Prof_pic',n_clicks=0),width={'size':2},align='left'),
            dbc.Col(
                [dcc.Graph(id='Point_graph', figure={})],width={'size':10},align='right')],align='center',justify='center'),

        dbc.Row([
            dbc.Col(
                html.Div([
                    dcc.Dropdown(id="slct_dataset",
                        options=[
                            {"label": "Show all (press update button)", "value": 1},
                            {"label": "Show 5","value":0}],
                        multi=False,
                        value=0,
                        style={'width': "60%"}
                        )]),align='center',width={'size':5})]),

        dbc.Row(dbc.Col(html.Div(id='update_table')),justify='center',align='center'),

        html.Br(),
        html.Br(),

        dbc.Row(dbc.Col(html.H3("Two Sample t test"),width={'size':'auto'}),align='center',justify='center'),
        dbc.Row(
            dbc.Col([
                html.Label('Team1 players (separate by commas)= '),
                dcc.Input(id='1players',value='Nikola Vucevic, Julius Randle',style={'width':'50%'}),
                ],width=12),align='center',justify='center'),
        dbc.Row(
            dbc.Col([
                html.Label('Team2 players (separate by commas) = '),
                dcc.Input(id='2players',value='Giannis Antetokounmpo, Luka Doncic',style={'width':'50%'}),
                ],width=12),align='center',justify='center'),
        html.Br(),
        dbc.Row(
            dbc.Col(
                dbc.Button('Update', id='submit-val2', n_clicks=0,color='primary'),width=12
        ),align='center',justify='center'),

        html.Br(),

        dbc.Row(dbc.Col(html.Div(id='ttest',children=[]),
            ),justify='center',align='center'),
        
        html.Br(),

        dbc.Row(
            dbc.Col(
                [dcc.Graph(id='team1graph', figure={})],width={'size':11},align='center'),align='center',justify='center'),
        dbc.Row(
            dbc.Col(
                [dcc.Graph(id='team2graph', figure={})],width={'size':11},align='center'),align='center',justify='center'),





 ])
    

@app.callback([Output(component_id='Prof_pic', component_property='src'),
               Output("update_table", "children"),
               Output(component_id='Point_graph', component_property='figure')],
     [Input('submit-val','n_clicks')],
     state=[State('player_names','value'),
            State('slct_dataset','value')])

def getPic(n_clicks,player_names,table_opt):
    link = formatLinks(player_names, 2021)
    points = []

    player_data, pic = getPlayerData(link)
    df = getFantasyPoints(player_data)

    fig = go.Scatter(x=df.index,y=df['FPoints'],name='Points')
    fig2 = go.Scatter(x=df.index,y=df['FPoints'].rolling(5,min_periods=1).mean(),name='Moving Average',line=dict(color='rgba(0,100,80,1)'))
    fig3 = go.Scatter(
        x=list(df.index)+list(df.index)[::-1],
        y=list(df['FPoints'].rolling(5,min_periods=1).quantile(0.67))+list(df['FPoints'].rolling(5,min_periods=1).quantile(0.33)),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0)'),
        hoverinfo="skip",
        showlegend=False)
    line = {'data': [fig,fig2,fig3],
            'layout': {
                'xaxis' :{'title': 'Game'},
                'yaxis' :{'title': 'Fantasy Points'},
                'title' : player_names+' Fantasy Points'
            }}
    fig = go.Figure(line)

    if table_opt==1:
        table = html.Div(
            [
                dash_table.DataTable(
                    data=df.to_dict("rows"),
                    columns=[{"id": x, "name": x} for x in df.columns],
                                style_table={'display': 'block', 'max-width': '600px', 'border': '2px grey',
                                                },
                                    style_as_list_view=True,
                                    style_header={
                                        'backgroundColor': '#e1e4eb',
                                        'fontWeight': 'bold',
                                        'align': 'center'
                                    },
                                    style_cell={
                                        # all three widths are needed
                                        'fontSize': '18', 'font-family': 'sans-serif', 'font-color': 'grey',
                                        'minWidth': '30px', 'width': '300px', 'maxWidth': '600px',
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                        'textAlign': 'center', },)
            ]
        )
    elif table_opt==0:
        table = html.Div(
            [
                dash_table.DataTable(
                    data=df.head(5).to_dict("rows"),
                    columns=[{"id": x, "name": x} for x in df.columns],
                                style_table={'display': 'block', 'max-width': '600px', 'border': '2px grey',
                                                },
                                    style_as_list_view=True,
                                    style_header={
                                        'backgroundColor': '#e1e4eb',
                                        'fontWeight': 'bold',
                                        'align': 'center'
                                    },
                                    style_cell={
                                        # all three widths are needed
                                        'fontSize': '18', 'font-family': 'sans-serif', 'font-color': 'grey',
                                        'minWidth': '30px', 'width': '300px', 'maxWidth': '600px',
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                        'textAlign': 'center', },)
            ]
        )


    return pic,table , fig

@app.callback([Output('ttest','children'),
               Output('team1graph','figure'),
               Output('team2graph','figure')], 
     [Input('submit-val2','n_clicks')],
     state=[State('1players','value'),
            State('2players','value')])

def getT2(n_clicks,players1,players2):
    team1 = players1.split(", ")
    team2 = players2.split(", ")

    player_names = team1 + team2

    links = formatLinks(player_names, 2021)
    points = []
    for link in links: 
        player_data, pic = getPlayerData(link)
        df = getFantasyPoints(player_data)
        points.append(list(df['FPoints'].values))

    ppp = points[:len(team1)]
    ppp2 = points[len(team1):]
    x = pd.DataFrame(ppp).sum()
    y = pd.DataFrame(ppp2).sum()
    stat, pval = ttest_ind(x, y)
    alpha = 0.10
    if pval < alpha:
        congrats = 'Unfortunately your'
        reject = 'was statistically different.'
        proceed = 'You may still offer the trade but it will not be automatically processed.'
    else:
        congrats = 'Congrats! Your'
        reject = 'was not statistically different.'
        proceed = 'Should your trade be accepted it will be automatically processed.'


    fig = go.Scatter(x=x.index,y=x,name='Points')
    fig2 = go.Scatter(x=x.index,y=x.rolling(5,min_periods=1).mean(),name='Moving Average',line=dict(color='rgba(0,100,80,1)'))
    fig3 = go.Scatter(
        x=list(x.index)+list(x.index)[::-1],
        y=list(x.rolling(5,min_periods=1).quantile(0.67))+list(x.rolling(5,min_periods=1).quantile(0.33)),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0)'),
        hoverinfo="skip",
        showlegend=False)
    line = {'data': [fig,fig2,fig3],
            'layout': {
                'xaxis' :{'title': 'Game'},
                'yaxis' :{'title': 'Fantasy Points'},
                'title' : 'Team 1 Fantasy Points',
                'height':350
            }}
    figure = go.Figure(line)

    fig = go.Scatter(x=y.index,y=y,name='Points')
    fig2 = go.Scatter(x=y.index,y=y.rolling(5,min_periods=1).mean(),name='Moving Average',line=dict(color='rgba(0,100,80,1)'))
    fig3 = go.Scatter(
        x=list(y.index)+list(y.index)[::-1],
        y=list(y.rolling(5,min_periods=1).quantile(0.67))+list(y.rolling(5,min_periods=1).quantile(0.33)),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0)'),
        hoverinfo="skip",
        showlegend=False)
    line = {'data': [fig,fig2,fig3],
            'layout': {
                'xaxis' :{'title': 'Game'},
                'yaxis' :{'title': 'Fantasy Points'},
                'title' : 'Team 2 Fantasy Points',
                'height':350
            }}
    figure2 = go.Figure(line)


    return '''{} simulated trade of {} for {} {} The pvalue was determined to be {}. {}'''.format(
        congrats,players1,players2,reject,str(round(pval,2)),proceed), figure, figure2




# if __name__ == '__main__':
#     app.run_server(debug=True)
