# What is this?

You will find two different Python scripts under *src* directory.

## pbs2json.py

*pbs2json.py* script takes the lines corresponding to finished jobs from Torque's accounting logs and creates a JSON file with specific information about the jobs

A typical Torque accounting log file name looks like this:

`YYYYMMDD`

A typical finished job line looks like this:

~~~~
09/12/2016 20:11:56;E;12334.server;user=dilasgoi group=scicomp jobname=JOB2.0194LDFA 
queue=p-slow-small ctime=1473500781 qtime=1473500781 etime=1473500781 start=1473506777 
owner=dilasgoi@atlas-001 exec_host=cn089/8 Resource_List.cput=200:00:00 Resource_List.mem=1gb 
Resource_List.ncpus=1 Resource_List.neednodes=1:ppn=1 Resource_List.nodect=1 Resource_List.nodes=1:ppn=1 
session=20136 total_execution_slots=1 unique_node_count=1 end=1473703916 Exit_status=0 
resources_used.cput=54:39:13 resources_used.mem=379804kb resources_used.vmem=794444kb
resources_used.walltime=54:45:47
~~~~

After parsing and reformatting we get something like this:

~~~~
[
    {
        "job identifier": "12334",
        "username": "dilasgoi",
        "group": "scicomp",
        "queue": "p-slow-small",
        "qtime": "1473500781",
        "start": "1473506777",
        "end": "1473703916",
        "Resource_List.cput": "720000",
        "Resource_List.mem": "1",
        "total_execution_slots": "1",
        "unique_node_count": "1",
        "Exit_status": "0",
        "resources_used.mem": "379804kb",
        "resources_used.walltime": "23342"
    }
]

~~~~

### Usage

~~~~
Usage: pbs2json.py [-h] [-sd SDATE] [-ed EDATE] [-u USER] [-g GROUP]

optional arguments:
  -h, --help            show this help message and exit
  -sd SDATE, --sdate SDATE Start date YYYYMMDD format
  -ed EDATE, --edate EDATE End date YYYYMMDD format
  -u USER, --user USER  Username
  -g GROUP, --group GROUP Group
		
~~~~

Example:

`python pbs2json.py -sd 20160101 -ed 20160102 -u dilasgoi`

The script can also create JSON files per user o per group. Providing dates is not mandatory anymore. If no date range is provided the program will scan the whole current year. It also assumes that user belongs to only one group.

## pdprocess.py

*pdprocess.py* script postprocesses JSON files produced by *pbs2json.py* script with [Pandas](https://pandas.pydata.org/).

### Usage

~~~~
usage: pdprocess.py [-h] [-f FILE] [-sd SDATE] [-ed EDATE] [-u USER] [-g GROUP]

This program processes JSON files created by pbs2json.py

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  File to process
  -sd SDATE, --sdate SDATE Start date YYYYMMDD format
  -ed EDATE, --edate EDATE End date YYYYMMDD format
  -u USER, --user USER  Username
  -g GROUP, --group GROUP Group

~~~~

File and start and end dates are not mandatory anymore. If no command line arguments are provided the program expects a file called files/acct_2018.json to exists. 



