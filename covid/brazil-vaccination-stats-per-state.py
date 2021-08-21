#!/usr/bin/python3

import numpy as np
import pandas as pd
import git, json, hashlib, requests, os
from datetime import datetime

pd.set_option('display.max_colwidth', -1)

file = 'cases-brazil-states.csv'

UFnames = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA':
        'Bahia', 'CE': 'Ceará', 'ES': 'Espirito Santo', 'GO': 'Goiás', 'MA':
        'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG':
        'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE':
        'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 
        'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul', 
        'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins', 
        'DF': 'Federal District', 'TOTAL': 'Brazil'
        }



UFs = {
        'AC': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Bandeira_do_Acre.svg/180px-Bandeira_do_Acre.svg.png',
        'AL': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Bandeira_de_Alagoas.svg/180px-Bandeira_de_Alagoas.svg.png',
        'AP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Bandeira_do_Amap%C3%A1.svg/180px-Bandeira_do_Amap%C3%A1.svg.png',
        'AM': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Bandeira_do_Amazonas.svg/180px-Bandeira_do_Amazonas.svg.png',
        'BA': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Bandeira_da_Bahia.svg/180px-Bandeira_da_Bahia.svg.png',
        'CE': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Bandeira_do_Cear%C3%A1.svg/180px-Bandeira_do_Cear%C3%A1.svg.png',
        'ES': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Bandeira_do_Esp%C3%ADrito_Santo.svg/180px-Bandeira_do_Esp%C3%ADrito_Santo.svg.png', 
        'GO': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Flag_of_Goi%C3%A1s.svg/180px-Flag_of_Goi%C3%A1s.svg.png', 
        'MA': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Bandeira_do_Maranh%C3%A3o.svg/180px-Bandeira_do_Maranh%C3%A3o.svg.png', 
        'MT': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Bandeira_de_Mato_Grosso.svg/180px-Bandeira_de_Mato_Grosso.svg.png', 
        'MS': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Bandeira_de_Mato_Grosso_do_Sul.svg/180px-Bandeira_de_Mato_Grosso_do_Sul.svg.png', 
        'MG': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Bandeira_de_Minas_Gerais.svg/180px-Bandeira_de_Minas_Gerais.svg.png', 
        'PA': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Bandeira_do_Par%C3%A1.svg/180px-Bandeira_do_Par%C3%A1.svg.png', 
        'PB': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Bandeira_da_Para%C3%ADba.svg/180px-Bandeira_da_Para%C3%ADba.svg.png', 
        'PR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Bandeira_do_Paran%C3%A1.svg/180px-Bandeira_do_Paran%C3%A1.svg.png', 
        'PE': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Bandeira_de_Pernambuco.svg/180px-Bandeira_de_Pernambuco.svg.png', 
        'PI': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Bandeira_do_Piau%C3%AD.svg/180px-Bandeira_do_Piau%C3%AD.svg.png', 
        'RJ': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Bandeira_do_estado_do_Rio_de_Janeiro.svg/180px-Bandeira_do_estado_do_Rio_de_Janeiro.svg.png', 
        'RN': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Bandeira_do_Rio_Grande_do_Norte.svg/180px-Bandeira_do_Rio_Grande_do_Norte.svg.png', 
        'RS': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Bandeira_do_Rio_Grande_do_Sul.svg/180px-Bandeira_do_Rio_Grande_do_Sul.svg.png', 
        'RO': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Bandeira_de_Rond%C3%B4nia.svg/180px-Bandeira_de_Rond%C3%B4nia.svg.png', 
        'RR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Bandeira_de_Roraima.svg/180px-Bandeira_de_Roraima.svg.png', 
        'SC': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Bandeira_de_Santa_Catarina.svg/180px-Bandeira_de_Santa_Catarina.svg.png', 
        'SP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Bandeira_do_estado_de_S%C3%A3o_Paulo.svg/180px-Bandeira_do_estado_de_S%C3%A3o_Paulo.svg.png', 
        'SE': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Bandeira_de_Sergipe.svg/180px-Bandeira_de_Sergipe.svg.png', 
        'TO': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Bandeira_do_Tocantins.svg/180px-Bandeira_do_Tocantins.svg.png', 
        'DF': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Bandeira_do_Distrito_Federal_%28Brasil%29.svg/180px-Bandeira_do_Distrito_Federal_%28Brasil%29.svg.png',
        'TOTAL': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/210px-Flag_of_Brazil.svg.png'
        }

with git.Git().custom_environment(GIT_SSH_COMMAND='home/j3r3mias/.ssh/id_rsa'):
    repo = git.Repo('.', search_parent_directories = True)
    origin = repo.remote(name = 'origin')
    origin.pull()

print(f' [+] Dowloading file..')
r = requests.get('https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv')
h = hashlib.md5(r.content).hexdigest()
print(f'     [+] Hash: {h}')

if os.path.exists(file):
    with open(file, 'r') as f:
        data = f.read().encode()
        hb = hashlib.md5(data).hexdigest()
        print(f'     [+] Hash of the current file: {hb}')

    if h != hb:
        print(f'     [+] The new file is different. Saving..')
        with open(file, 'w') as f:
            f.write(r.content.decode())
    else:
        print(f"     [+] The file didn't change")
        # exit()
else:
    print(f'     [+] File doesnt exist. Saving..')
    with open(file, 'w') as f:
        f.write(r.content.decode())

print(f' [+] Open population info file..')
population = pd.read_csv('brazil-population-per-state.csv')
population = population.append(population.sum(numeric_only = True), ignore_index = True)
population.loc[population.index[-1], 'state'] = 'TOTAL'

print(f' [+] Generate new calculated data..')
df = pd.read_csv(file)

# Population uptaded (deaths removed)
df = pd.merge(df, population, left_on = 'state', right_on = 'state', how = 'outer')
df['population_minus_deaths'] = df['population'] - df['deaths']

print(f'     [+] Full vaccinated people..')
df['full_vaccinated'] = df['vaccinated_second'].fillna(0) + df['vaccinated_single'].fillna(0)
df['full_vaccinated_per_100_inhabitants'] = df['vaccinated_second_per_100_inhabitants'].fillna(0) + df['vaccinated_single_per_100_inhabitants'].fillna(0)
df = df[df['full_vaccinated_per_100_inhabitants'] != 0]
df['percentages_full_vaccinated_calculated'] = df['full_vaccinated'].fillna(0) / df['population_minus_deaths'] * 100.

print(f'     [+] First or single dose..')
df['first_or_single_dose_vaccinated'] = df['vaccinated'].fillna(0) + df['vaccinated_single'].fillna(0)
df['first_or_single_dose_vaccinated_per_100_inhabitants'] = df['vaccinated_per_100_inhabitants'].fillna(0) + df['vaccinated_single_per_100_inhabitants'].fillna(0)
df = df[df['first_or_single_dose_vaccinated_per_100_inhabitants'] != 0]
df['percentages_first_or_single_dose_vaccinated_calculated'] = df['first_or_single_dose_vaccinated'].fillna(0) / df['population_minus_deaths'] * 100.



print(f'     [+] Not fully vaccinated people..')
not_fully_vaccinated = df.loc[:, ['date', 'state', 'percentages_full_vaccinated_calculated']]
not_fully_vaccinated['full_vaccinated_per_100_calculated'] = 100 - not_fully_vaccinated['percentages_full_vaccinated_calculated']
not_fully_vaccinated['date'] = pd.to_datetime(not_fully_vaccinated['date'])
not_fully_vaccinated.set_index(['date'], inplace = True)

not_fully_vaccinated_per_state = not_fully_vaccinated[['state', 'full_vaccinated_per_100_calculated']].groupby(['state', 'date']).sum().unstack('state')
not_fully_vaccinated_per_state.columns = not_fully_vaccinated_per_state.columns.droplevel(0)
not_fully_vaccinated_per_state = not_fully_vaccinated_per_state.fillna(100)

not_fully_vaccinated_per_state.index = not_fully_vaccinated_per_state.index.strftime('%Y-%m-%d')

print(f'         [+] Saving new CSV..')
transposed_not_fully_vaccinated_per_state = not_fully_vaccinated_per_state.T
transposed_not_fully_vaccinated_per_state['names'] = transposed_not_fully_vaccinated_per_state.index.map(UFnames)
transposed_not_fully_vaccinated_per_state['flags'] = transposed_not_fully_vaccinated_per_state.index.map(UFs)
cols = list(transposed_not_fully_vaccinated_per_state.columns)
cols = [cols[-2]] + [cols[-1]] + cols[:-2]
transposed_not_fully_vaccinated_per_state = transposed_not_fully_vaccinated_per_state[cols]

transposed_not_fully_vaccinated_per_state.to_csv('brazil-not-fully-vaccinated-per-state.csv',
        float_format = '%.2f', date_format = '%Y-%m-%d')

print(f'         [+] Building new JSON..')
datadicts = {"data": []}
for g in not_fully_vaccinated_per_state.columns:
    state = {}
    state['name'] = g
    data = []
    for d, v in not_fully_vaccinated_per_state[g].iteritems():
        data.append({'x' : d, 'y' : f'{v:.2f}'})
    state['data'] = data
    datadicts['data'].append(state)

print(f'         [+] Saving new JSON..')
jsondata = json.dumps(datadicts)
with open('brazil-not-fully-vaccinated-per-state.json', 'w') as f:
    f.write(jsondata)

print(f'     [+] Vaccinated people with single or first dose..')
single_or_first_dose_vaccinated = df.loc[:, ['date', 'state', 'percentages_first_or_single_dose_vaccinated_calculated']]
single_or_first_dose_vaccinated['date'] = pd.to_datetime(single_or_first_dose_vaccinated['date'])
single_or_first_dose_vaccinated.set_index(['date'], inplace = True)

single_or_first_dose_vaccinated_per_state = single_or_first_dose_vaccinated[['state', 'percentages_first_or_single_dose_vaccinated_calculated']].groupby(['state', 'date']).sum().unstack('state')
single_or_first_dose_vaccinated_per_state.columns = single_or_first_dose_vaccinated_per_state.columns.droplevel(0)
single_or_first_dose_vaccinated_per_state = single_or_first_dose_vaccinated_per_state.fillna(0)

single_or_first_dose_vaccinated_per_state.index = single_or_first_dose_vaccinated_per_state.index.strftime('%Y-%m-%d')

print(f'         [+] Saving new CSV..')
transposed_single_or_first_dose_vaccinated_per_state = single_or_first_dose_vaccinated_per_state.T
transposed_single_or_first_dose_vaccinated_per_state['names'] = transposed_single_or_first_dose_vaccinated_per_state.index.map(UFnames)
transposed_single_or_first_dose_vaccinated_per_state['flags'] = transposed_single_or_first_dose_vaccinated_per_state.index.map(UFs)
cols = list(transposed_single_or_first_dose_vaccinated_per_state.columns)
cols = [cols[-2]] + [cols[-1]] +  cols[:-2]
transposed_single_or_first_dose_vaccinated_per_state = transposed_single_or_first_dose_vaccinated_per_state[cols]
transposed_single_or_first_dose_vaccinated_per_state.to_csv('brazil-single-or-first-dose-vaccinated-per-state.csv',
        float_format = '%.2f', date_format = '%Y-%m-%d')

print(f'         [+] Building new JSON..')
datadicts = {"data": []}
for g in single_or_first_dose_vaccinated_per_state.columns:
    state = {}
    state['name'] = g
    data = []
    for d, v in single_or_first_dose_vaccinated_per_state[g].iteritems():
        data.append({'x' : d, 'y' : f'{v:.2f}'})
    state['data'] = data
    datadicts['data'].append(state)

print(f'         [+] Saving new JSON..')
jsondata = json.dumps(datadicts)
with open('brazil-single-or-first-dose-vaccinated-per-state.json', 'w') as f:
    f.write(jsondata)

print(f'     [+] Fully vaccinated people..')
fully_vaccinated = df.loc[:, ['date', 'state', 'percentages_full_vaccinated_calculated']]
fully_vaccinated['full_vaccinated_per_100_calculated'] = fully_vaccinated['percentages_full_vaccinated_calculated']
fully_vaccinated['date'] = pd.to_datetime(fully_vaccinated['date'])
fully_vaccinated.set_index(['date'], inplace = True)

fully_vaccinated_per_state = fully_vaccinated[['state', 'full_vaccinated_per_100_calculated']].groupby(['state', 'date']).sum().unstack('state')
fully_vaccinated_per_state.columns = fully_vaccinated_per_state.columns.droplevel(0)
fully_vaccinated_per_state = fully_vaccinated_per_state.fillna(0)

fully_vaccinated_per_state.index = fully_vaccinated_per_state.index.strftime('%Y-%m-%d')

print(f'         [+] Saving new CSV..')
transposed_fully_vaccinated_per_state = fully_vaccinated_per_state.T
transposed_fully_vaccinated_per_state['names'] = transposed_fully_vaccinated_per_state.index.map(UFnames)
transposed_fully_vaccinated_per_state['flags'] = transposed_fully_vaccinated_per_state.index.map(UFs)
cols = list(transposed_fully_vaccinated_per_state.columns)
cols = [cols[-2]] + [cols[-1]] + cols[:-2]
transposed_fully_vaccinated_per_state = transposed_fully_vaccinated_per_state[cols]

transposed_fully_vaccinated_per_state.to_csv('brazil-fully-vaccinated-per-state.csv',
        float_format = '%.3f', date_format = '%Y-%m-%d')

print(f' [+] Send the new data to github..')
author = repo.config_reader().get_value('user', 'name')
message = f'New covid files in {datetime.today().strftime("%d-%m-%Y-%H-%M")}.'
try:
    repo.git.commit('-am', message, author = author)
    origin.push()
except:
    print(f'     [+] The files are up to date..')
