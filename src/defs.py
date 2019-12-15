import json
import argparse
import os.path
import sys
import pandas as pd
import numpy as np
import subprocess
import re
import decimal
import datetime

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='This program processes JSON files created by pbs2json.py')
    parser.add_argument('-f','--file',help='File to process', required=False)
    parser.add_argument('-sd','--sdate',help='Start date YYYYMMDD format', required=False)
    parser.add_argument('-ed','--edate',help='End date YYYYMMDD format', required=False)
    parser.add_argument('-u','--user',help='Username', required=False)
    parser.add_argument('-g','--group',help='Group', required=False)
    parser.add_argument('-i','--interactive',help='Interactive mode', required=False)
    args = parser.parse_args()
    return args

def process_json(jsonfile):
    if os.path.isfile(jsonfile):
        df = pd.read_json(jsonfile)
        df = df.rename(columns={'resources_used.walltime': 'walltime'})
        df = df.rename(columns={'Resource_List.mem': 'memory'})
        df['ratio'] = np.divide(df['memory'], df['unique_node_count'])
        df['wait_time'] = np.subtract(df['start'], df['qtime'])
        df['spectral_power'] = np.multiply(df['ratio'], df['walltime'])
        df['cputime'] = np.multiply(df['walltime'], df['total_execution_slots'])
        conditions = [(df['memory'] <= 128), 
                      (df['memory'] > 128) & (df['memory'] <= 256),
                      (df['memory'] > 256)]
        choices = [1,1.2,1.3]
        df['factor'] = np.select(conditions, choices)
        df['credits'] = np.multiply(df['factor'], df['cputime'])
        return df
    else:
        print(jsonfile, 'file does not exist')
        # During dev stage we just terminate the program
        sys.exit()

def process_user_json(jsonfile):
    if os.path.isfile(jsonfile):
        df = pd.read_json(jsonfile)
        return df
    else:
        print(jsonfile, 'file does not exist')
        # During dev stage we just terminate the program
        sys.exit()

def totals_per_user(username, jsonfile, df, user_textfile):
    df_user = df[df['username'] == username]
    series_per_user = df_user[['cputime', 'memory']].sum()
    cost_per_cpu_hour = 0.06
    computing_hours = round(float(repr(series_per_user['cputime']))/3600)
    euros = round(cost_per_cpu_hour * computing_hours)
    memory = round(float(repr(series_per_user['memory'])))

    # Create a dictionary to dump to a JSON file later
    user_totals_dictionary = {'username': username, \
                              'euros': euros, \
                              'computing_hours': computing_hours, \
                              'memory': memory}
    # Writing to text file
    f = open(user_textfile, "a")
    f.write("%12s %10i %10i %10i\n" % (username, euros, computing_hours, memory))
    f.close()

    return user_totals_dictionary

def totals_per_group(group, jsonfile, df, filename):
    df_user = df[df['group'] == group]
    series_per_group = df_group[['cputime', 'memory']].sum()
    cost_per_cpu_hour = 0.06
    computing_hours = round(float(repr(series_per_group['cputime']))/3600)
    euros = round(cost_per_cpu_hour * computing_hours)
    memory = round(float(repr(series_per_group['memory'])))

    f = open(filename, "a")
    f.write("%12s %10i %10i %10i\n" % (group, euros, computing_hours, memory))
    f.close()

def list_posible_files():
    list_dir_files = subprocess.Popen(('ls', '../files'), stdout=subprocess.PIPE)
    filter_files = subprocess.check_output('grep acct', shell = True, stdin=list_dir_files.stdout).decode('utf-8').strip()
    file_list = filter_files.splitlines()
    return file_list

def active_user_list():
    list_sys_users = subprocess.Popen(('ypcat', 'passwd'), stdout=subprocess.PIPE)
    filter_users = subprocess.check_output('grep -v "*"', shell = True, stdin=list_sys_users.stdout).decode('utf-8').strip()
    user_list = [re.findall(r"^\w+", item)[0] for item in filter_users.splitlines()]
    return user_list

def cores_per_job(interval_list):
    list = [[interval_list[i+1],len(df[(df.total_execution_slots > interval_list[i]) & (df.total_execution_slots <= interval_list[i+1])])] for i in range(len(interval_list)-1)]
    return list

def mem_per_job(interval_list):
    list = [[interval_list[i+1],len(df[(df.memory > interval_list[i]) & (df.memory <= interval_list[i+1])])] for i in range(len(interval_list)-1)]
    return list
