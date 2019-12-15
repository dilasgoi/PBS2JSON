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
                      (df['memory'] > 256) & (df['memory'] <= 512),
                      (df['memory'] > 512) & (df['memory'] <= 1024),
                      (df['memory'] > 1024)]
        choices = [1.0, 1.2, 1.3, 1.4, 1.5]
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
    else:
        print(jsonfile, 'file does not exist')
        # During dev stage we just terminate the program
        sys.exit()

def totals_per_user(username, jsonfile, df, user_textfile):    
    df_user = df[df['username'] == username]
    series_per_user = df_user[['cputime', 'memory', 'credits']].sum()
    cost_per_cpu_hour = 0.06
    computing_hours = round(float(repr(series_per_user['cputime']))/3600)
    corrected_hours = round(float(repr(series_per_user['credits']))/3600)
    euros = round(cost_per_cpu_hour * computing_hours)
    credits = round(cost_per_cpu_hour * corrected_hours)
    memory = round(float(repr(series_per_user['memory'])))

    # Create a dictionary to dump to a JSON file later
    user_totals_dictionary = {'username': username, \
                              'euros': euros, \
                              'credits': credits, \
                              'computing_hours': computing_hours, \
                              'memory': memory}
    # Writing to text file
    f = open(user_textfile, "a")
    # f.write("%12s %10i %10i %10i %10i \n" % (username, euros, credits, computing_hours, memory))
    f.write("%s;%i;%i;%i;%i \n" % (username, euros, credits, computing_hours, memory))
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
    
def main():

    args = parse_command_line_arguments()
    current_year = datetime.datetime.today().strftime('%Y')

    #############################################
    #                USER RELATED               #
    #############################################


    # List of users from yellow pages
    user_list = active_user_list()

    if args.interactive is not None:
        # List of available accounting files
        file_list = list_posible_files()
    
        count = 0;
        print('List of available accounting files:')
        for file in file_list:
            count += 1
            print(count,'-', file)
       
        selection = input('Enter selection: ')
        filename = file_list[int(selection) - 1]
        users_textfile = '../files/users_' + re.findall('_([0-9]*)', filename)[0] + '.csv'
    else:
        filename = 'acct_' + current_year + '.json'
        users_textfile = '../files/users_' + current_year + '.csv'
    users_jsonfile = '../files/users_' + current_year + '.json'
    
    

    
    # Check if user file exists
    exists_textfile = os.path.isfile(users_textfile)
    if exists_textfile:
        os.remove(users_textfile)
    exists_jsonfile = os.path.isfile(users_jsonfile)
    if exists_jsonfile:
        os.remove(users_jsonfile)
        
    # Header for text output
    header = ['username', 'euros', 'credits', 'cputime', 'memory']
    f = open(users_textfile, 'w')
    #f.write("%12s %10s %10s %10s %10s\n" % (header[0], header[1], header[2], header[3], header[4]))
    f.write("%s;%s;%s;%s;%s\n" % (header[0], header[1], header[2], header[3], header[4]))

    # Select file to process and get totals per user
    df = process_json('../files/' + filename)
    list_of_users_total = []
    for user in user_list:
        list_of_users_total.append(totals_per_user(user, filename, df, users_textfile))

    # User the list of dictionaries created above and dump to a valid JSON file
    with open(users_jsonfile, 'w') as json.file:
        json.dump(list_of_users_total, json.file, indent=4)


    #############################################
    #                JOB RELATED                #
    #############################################

    
    
main()
