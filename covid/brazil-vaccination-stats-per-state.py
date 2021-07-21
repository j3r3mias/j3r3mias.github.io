#!/usr/bin/python3

import numpy as np
import pandas as pd
import git, json, hashlib, requests, os
from datetime import datetime

file = 'cases-brazil-states.csv'

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
        exit()
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

print(f'         [+] Saving new CSV..')
not_fully_vaccinated_per_state.to_csv('brazil-not-fully-vaccinated-per-state.csv',
        float_format = '%.3f')

print(f'         [+] Building new JSON..')
datadicts = {"data": []}
for g in not_fully_vaccinated_per_state.columns:
    state = {}
    state['name'] = g
    data = []
    for d, v in not_fully_vaccinated_per_state[g].iteritems():
        data.append({'x' : datetime.strftime(d, '%Y-%m-%d'), 'y' : f'{v:.2f}'})
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

print(f'         [+] Saving new CSV..')
single_or_first_dose_vaccinated_per_state.to_csv('brazil-single-or-first-dose-vaccinated-per-state.csv',
        float_format = '%.3f')

print(f'         [+] Building new JSON..')
datadicts = {"data": []}
for g in single_or_first_dose_vaccinated_per_state.columns:
    state = {}
    state['name'] = g
    data = []
    for d, v in single_or_first_dose_vaccinated_per_state[g].iteritems():
        data.append({'x' : datetime.strftime(d, '%Y-%m-%d'), 'y' : f'{v:.2f}'})
    state['data'] = data
    datadicts['data'].append(state)

print(f'         [+] Saving new JSON..')
jsondata = json.dumps(datadicts)
with open('brazil-single-or-first-dose-vaccinated-per-state.json', 'w') as f:
    f.write(jsondata)

print(f' [+] Send the new data to github..')
author = repo.config_reader().get_value('user', 'name')
message = f'New covid files in {datetime.today().strftime("%d-%m-%Y-%H-%M")}.'
try:
    repo.git.commit('-am', message, author = author)
    origin.push()
except:
    print(f'     [+] The files are up to date..')