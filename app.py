#=============================================================================#
#                                                                             #
#                 Product Pricing & Profit Margin Calculator                  #
#                                                                             #
#=============================================================================#

# Perform imports here:
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, ALL, State
import pandas as pd
from datetime import datetime
import plotly.express as px
import re
import json

# Launch the application:
app = dash.Dash(external_stylesheets = [dbc.themes.SUPERHERO])
app.config.suppress_callback_exceptions = True

#=============================================================================#
#                                                                             #
#                                 Layout                                      #
#                                                                             #
#=============================================================================#

#============================= Fixed Expenses ================================#

def add_input_group(input_list):
    inputs = []
    for i in input_list:
        inputs.append(
            dbc.InputGroup(
                    [
                        dbc.Label(i, width=7),
                        dbc.InputGroupAddon('$',
                                            id={'type': 'addon',
                                                'index': len(inputs)},
                                            addon_type='prepend'),
                        dbc.Input(id={'type': 'input',
                                      'index': len(inputs)},
                                  placeholder='Amount'),
                    ],
                    className='mb-5',
                )
        )
    return inputs

input_list = ['Material Expenses','Labor Expenses','Shipping Expenses',
              'Third-Party Market Fees','Other Expenses']

input_group = add_input_group(input_list)

#============================== Add/Remove Button ============================#

c = pd.read_csv('currencies.csv',sep=';')
cs = c['Currency Symbol'] + ' - ' + c['Country and Currency']
items = [
    dbc.DropdownMenuItem(s,
                         id={'type': 'dropdown',
                             'index': 'item-'+str(i+1)}) for i,s in enumerate(cs)
]

button = html.Div(
    [
        dbc.InputGroup(
                [dbc.Button('+', id='add-expense-button', className='mr-2'),
                 dbc.Button('-', id='remove-expense-button', className='mr-2'),
                 dbc.DropdownMenu(items, label = '$', id='dropdown-menu', addon_type='prepend'),
                 dbc.Input(placeholder='Expense', id='expense-name',),
                ], className='mb-5',
            )
    ]
)

#========================== Form - Calculation Outputs =======================#

total_expenses = dbc.FormGroup(
    [
        dbc.Label('Total Expenses', className='h4'),
        dbc.Card([
            dbc.Label(id='total-expenses', className='h1'),
        ],
            className='card text-center', body=True)
    ]
)

price_markup = html.Div(
    [
        html.H4('Price Markup'),
        dbc.InputGroup(
            [
                dbc.Input(id='price-markup', value=50, type='number'),
                dbc.InputGroupAddon('%', addon_type='prepend')
            ], style={'width': '7rem'}
        )
    ]
)

profit_margin = dbc.FormGroup(
    [
        dbc.Label('Profit Margin', className='h4'),
        dbc.Card(
            [
                dbc.Label(id='profit-margin', className='h1'),
            ], className='card text-center', body=True
        )
    ]
)

product_price = dbc.FormGroup(
    [
        dbc.Label('Profit Price', className='h4'),
        dbc.Card([
            dbc.Label(id='profit-price', className='h1'),
        ], className='card text-center', body=True)
    ]
)

form = dbc.Form(
    [
        price_markup,
        html.Br(),
        profit_margin,
        html.Br(),
        product_price,
        html.Br(),
        dbc.Button('Calculate', id='calculate-button',
                   size='lg', color='info', block=True)
    ]
)

#========================== Projection Graph =================================#

datelist = pd.date_range(datetime.today(), periods=12*2,freq='M').tolist()
markup = range(10,250,10)
fig = px.bar(x=datelist, y=markup)

#============================== App Layout ===================================#

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.H1('Product Pricing & Profit Margin Calculator')
            ], justify='center', align='centre'
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(id='expense-list', children=input_group,
                                 style=dict(height='525px',overflow='scroll')),
                        button,
                        total_expenses
                    ], width=4
                ),
                dbc.Col(form, width=2),
                dbc.Col(dcc.Graph(figure=fig), width=6),
            ], align='centre'
        )
    ], fluid = True
)

#=============================================================================#
#                                                                             #
#                                 Callback                                    #
#                                                                             #
#=============================================================================#

#============================== Add/Remove Button ============================#

# Use dash.callback_context to know which button was pressed.
@app.callback(
    Output('expense-list', 'children'),
    [
        Input('add-expense-button', 'n_clicks'),
        Input('remove-expense-button', 'n_clicks'),
        Input('expense-name','value'),
        Input('dropdown-menu', 'label')
    ],
    State('expense-list', 'children')
)
def add_remove_step(add_clicks, remove_clicks, text, current_currency, div_list):
    # Identify who was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        triggered_id = 'No clicks yet'
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Act
    if triggered_id == 'add-expense-button':
        div_list += [html.Div(
            # Index children using the next available index
            children=[
                dbc.InputGroup(
                    [
                        dbc.Label(text, width=7),
                        dbc.InputGroupAddon(current_currency,
                                            id={'type': 'addon',
                                                'index': len(div_list)}, addon_type='prepend'),
                        dbc.Input(id={'type': 'input',
                                      'index': len(div_list)},
                                  placeholder='Amount'),
                    ], className='mb-5',
                )
            ]
        )]
    elif len(div_list) > 0 and triggered_id == 'remove-expense-button':
        div_list = div_list[:-1]
    return div_list

#============================= Choose Currency ===========================#

@app.callback(
    [
        Output('dropdown-menu', 'label'),
        Output({'type': 'addon', 'index': ALL}, 'children')
    ],
    Input({'type': 'dropdown', 'index': ALL}, 'n_clicks'),
    State('expense-list', 'children')
)
def update_label(input, div_list):
    # use a dictionary to map ids back to the desired label
    id_lookup = {'item-'+str(i+1):s for (i, s) in enumerate(cs)}

    ctx = dash.callback_context

    if input is None:
        # if no currency has been clicked, return dollar:'$'
        return ['$',['$'] * len(div_list)]
    elif not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    else:
        # this gets the id of the currency that triggered the callback
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        dic = json.loads(triggered_id)
        #dic = ast.literal_eval(triggered_id)
        current_currency = re.findall('^(.*-)', id_lookup[dic['index']])[0][:-2]
        return [current_currency,[current_currency] * len(div_list)]


#============================= Calculation Outputs ===========================#

# Calculate values on click
@app.callback(
    [
        Output('profit-margin', 'children'),
        Output('profit-price', 'children'),
        Output('total-expenses', 'children'),
    ],
    [
        Input('calculate-button', 'n_clicks'),
        Input('price-markup', 'value'),
        Input('dropdown-menu', 'label'),
        Input({'type': 'input', 'index': ALL}, 'value')
    ]
)
def on_button_click(n, markup, current_currency, input):
    if n is None:
        return current_currency+'0', current_currency+'0', current_currency+'0'
    else:
        te = 0
        for i in input:
            if i is not None:
                te = te + float(i)
        pm = te*(markup/100)
        pp = te*(1 + markup/100)
        return '{0}{1:.2f}'.format(current_currency,pm),\
               '{0}{1:.2f}'.format(current_currency,pp),\
               '{0}{1:.2f}'.format(current_currency,te)

#=============================================================================#

if __name__ == '__main__':
    app.run_server()
