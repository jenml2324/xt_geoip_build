#!/usr/bin/python3
# Convert ipinfo.io csv data to xtables legacy format

import csv
import ipaddress
import sys
import os

script_name = os.path.basename(__file__)

if len(sys.argv) < 3:
    print(f"Usage: python3 {script_name} country.csv legacy.csv")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)

    # Skip header row in input file
    next(reader)
    
    for row in reader:
        start_ip = row[0]
        end_ip = row[1]
        country = row[2]
        country_name = row[3]

        # Convert start and end IPs to their integer representation
        start_int = int(ipaddress.ip_address(start_ip))
        end_int = int(ipaddress.ip_address(end_ip))

        writer.writerow([start_ip, end_ip, start_int, end_int, country, country_name])
