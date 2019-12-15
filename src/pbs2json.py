import re
import json
import datetime
import os.path
import argparse

def get_sec(s):
    l = s.split(':')
    return int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='''This program parses Torque\'s accounting logs  
                                                 to produce a JSON file with of all finished jobs''')
    parser.add_argument('-sd','--sdate',help='Start date YYYYMMDD format', required=False)
    parser.add_argument('-ed','--edate',help='End date YYYYMMDD formatx', required=False)
    parser.add_argument('-u','--user',help='Username', required=False)
    parser.add_argument('-g','--group',help='Group', required=False)
    args = parser.parse_args()
    return args

def give_final_format(accdict):
    accdict.update({'resources_used.walltime' : str(get_sec(accdict['resources_used.walltime']))})
    accdict.update({'Resource_List.cput' : str(get_sec(accdict['Resource_List.cput']))})
    accdict.update({'resources_used.mem' : str(int(re.findall('^(.*)kb', accdict['resources_used.mem'])[0])/(1024*1024))})

    if "gb" in accdict.get('Resource_List.mem', ''):
        accdict.update({'Resource_List.mem' : re.findall('^(.*)gb', accdict['Resource_List.mem'])[0]})
    elif "mb" in accdict.get('Resource_List.mem', ''):
        accdict.update({'Resource_List.mem' : str(int(re.findall('^(.*)mb', accdict['Resource_List.mem'])[0])/1024)})
    else:
        accdict.update({'Resource_List.mem' : str(int(re.findall('^(.*)b', accdict['Resource_List.mem'])[0])/(1024*1024))})
    return accdict

def write_dictionary_to_json_file(my_json_file, full_info_list):
    with open(my_json_file, 'w') as json.file:
        json.dump(full_info_list, json.file, indent=4)
        
def main():
    args = parse_command_line_arguments()
    current_year = datetime.datetime.today().strftime('%Y')
    
    #
    # If no command line argument is provided we will parse the whole
    # current year. If start and end dates are provided it will parse only
    # files containing information in that date range.
    #
    # Output files will also have slighly different name. If no CLA is provided:
    #
    # JSON filename = acct_2018
    # JSON filename = acct_20180201_20181002
    #
    if args.sdate is not None and args.edate is not None:
        sdate = datetime.datetime.strptime(args.sdate, '%Y%m%d')
        edate = datetime.datetime.strptime(args.edate, '%Y%m%d')
        json_file_header = '../files/acct' + '_' + args.sdate + '-' + args.edate
        if args.user == None and args.group == None:
            my_json_file = json_file_header + '.json'
        elif not args.user == None:
            my_json_file = json_file_header + '_' + args.user + '.json'
        elif not args.group == None:
            my_json_file = json_file_header + '_' + args.group + '.json'
    else:
        sdate = datetime.datetime.strptime(current_year + '0101', '%Y%m%d')
        edate = datetime.datetime.strptime(current_year + '1231', '%Y%m%d')
        my_json_file = '../files/acct_' + current_year + '.json'
        
    step  = datetime.timedelta(days=1)
    
    # This is what will eventually be dumped into a JSON file
    full_info_list = []

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event_file = open('../files/event.log', 'a')

    while sdate <= edate:
        accounting_file_name = sdate.strftime('%Y%m%d')
        accounting_file_directory  = '../files/accounting/'
        accounting_file = accounting_file_directory + accounting_file_name
        if os.path.isfile(accounting_file):
            try:
                fh = open(accounting_file)
                for line in fh:
                    try:
                        # Get lines for finished jobs
                        if re.search(";E;", line):
                            line_split = line.split()[1:]
                            # Create a dictionary with file name, job identifier and the username
                            partial_line_info_dictionary1 = {'filename': accounting_file_name,
                                                             'job identifier': re.findall('E;(.*)\.', line_split[0])[0],
                                                             'username': re.findall('user\=(.*)',line_split[0])[0]}
                            
                            # Create a dictionary with the rest of the information of the job
                            partial_line_info_dictionary2 = {item[0]:item[1] for item in ([re.split('\=(.*)', item) 
                                                                             for item in line.split()][2:])}
                            full_line_info_dictionary = {**partial_line_info_dictionary1, **partial_line_info_dictionary2}
                            
                            # Filter only the keys we are interested in
                            accounting_dictionary_keys = ['job identifier',
                                                          'username',
                                                          'group',
                                                          'queue',
                                                          'qtime',
                                                          'start',
                                                          'end', 
                                                          'Resource_List.cput',
                                                          'Resource_List.mem',
                                                          'total_execution_slots',
                                                          'unique_node_count',
                                                          'Exit_status',
                                                          'resources_used.mem',
                                                          'resources_used.walltime']
                            
                            # Create dictionary based on the the keys we are interested in
                            accounting_dictionary = {key:full_line_info_dictionary[key] for key in full_line_info_dictionary
                                                                                        for key in accounting_dictionary_keys}
                            formatted_accounting_dictionary = give_final_format(accounting_dictionary)
                            
                            # Append job info to the list based on the CLA passed
                            if args.user == None and args.group == None:
                               full_info_list.append(formatted_accounting_dictionary)
                            elif formatted_accounting_dictionary['username'] == args.user and args.group == None:
                               full_info_list.append(formatted_accounting_dictionary)
                            elif formatted_accounting_dictionary['group'] == args.group and args.user == None:
                               full_info_list.append(formatted_accounting_dictionary)
                    except:
                        event_file.write('%s Line could not be parsed: %s\n' % (now, line))
                        #print('Line could not be parsed:\n', line)
            except:
                event_file.write('%s Something went wrong with file: %s\n' % (now, accounting_file_name))
                #print('Something went wrong with file', accounting_file_name)
        else:
            event_file.write('%s File does not exist: %s\n' % (now, accounting_file_name))
            #print('File', accounting_file_name, 'does not exist')
                
        # Add one day
        sdate += step    
                
    # Write the JSON file
    write_dictionary_to_json_file(my_json_file, full_info_list)

main()
