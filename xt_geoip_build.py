#!/usr/bin/python3
import argparse
import os
import struct
import csv
import sys
import ipaddress
import gzip
import zipfile

def wantBE(u32):
    return u32 is None or u32 == struct.pack('>I', 0x10000000)

def wantLE(u32):
    return u32 is None or u32 == struct.pack('<I', 0x10000000)

def collect(csv_file, ignore_first_row, start_ip_col, end_ip_col, country_code_col, existing_country_data):
    country = existing_country_data
    
    first_row = next(csv_file)

    if first_row == ['start_ip', 'end_ip', 'country', 'country_name', 'continent', 'continent_name']:
        sys.stdout.write(f"ipinfo.io country.csv format matched!\n")
        ignore_first_row = True
        start_ip_col = 0
        end_ip_col = 1
        country_code_col = 2
    elif len(first_row) == 3 and all('.' in field for field in first_row[:2]):
        sys.stdout.write(f"dbip-country-lite format matched!\n")
        start_ip_col = 0
        end_ip_col = 1
        country_code_col = 2
    elif first_row == ['ip_version', 'start_ip', 'end_ip', 'continent', 'country_code', 'country', 'state', 'city', 'zip', 'timezone', 'latitude', 'longitude', 'accuracy']:
        sys.stdout.write(f"ipapi.is csv format matched!\n")
        ignore_first_row = True
        start_ip_col = 1
        end_ip_col = 2
        country_code_col = 4

    if not ignore_first_row:
        csv_file = iter([first_row] + list(csv_file))

    line_num = 1

    for row in csv_file:
        line_num += 1

        if len(row) <= max(start_ip_col, end_ip_col, country_code_col):
            sys.stderr.write(f"\nError: Skipping row {line_num}: insufficient columns\n")
            continue

        start_ip, end_ip, country_code = row[start_ip_col], row[end_ip_col], row[country_code_col]
        if country_code not in country:
            country[country_code] = {
                'name': country_code,
                'pool_v4': [],
                'pool_v6': []
            }
        c = country[country_code]
        if ':' in start_ip:
            c['pool_v6'].append((ipaddress.IPv6Address(start_ip).packed, ipaddress.IPv6Address(end_ip).packed))
        else:
            c['pool_v4'].append((int(ipaddress.IPv4Address(start_ip)), int(ipaddress.IPv4Address(end_ip))))

        if line_num % 4096 == 0:
            sys.stderr.write(f"\r\033[2K{line_num} entries")
    sys.stderr.write(f"\r\033[2K{line_num} entries total\n")
    return country

def dump_one(target_dir, iso_code, country, u32):
    if country['pool_v4']:
        if wantLE(u32):
            file_path = os.path.join(target_dir, "LE", f"{iso_code.upper()}.iv4")
            with open(file_path, "wb") as f_le:
                for start, end in country['pool_v4']:
                    f_le.write(struct.pack('<II', start, end))

        if wantBE(u32):
            file_path = os.path.join(target_dir, "BE", f"{iso_code.upper()}.iv4")
            with open(file_path, "wb") as f_be:
                for start, end in country['pool_v4']:
                    f_be.write(struct.pack('>II', start, end))

    if country['pool_v6']:
        if wantLE(u32):
            file_path = os.path.join(target_dir, "LE", f"{iso_code.upper()}.iv6")
            with open(file_path, "wb") as f_le:
                for start, end in country['pool_v6']:
                    start_swapped = struct.pack('<IIII', *struct.unpack('>IIII', start))
                    end_swapped = struct.pack('<IIII', *struct.unpack('>IIII', end))
                    f_le.write(start_swapped + end_swapped)

        if wantBE(u32):
            file_path = os.path.join(target_dir, "BE", f"{iso_code.upper()}.iv6")
            with open(file_path, "wb") as f_be:
                for start, end in country['pool_v6']:
                    f_be.write(start + end)

def dump(target_dir, country, u32):
    for iso_code in sorted(country.keys()):
        dump_one(target_dir, iso_code, country[iso_code], u32)

def main():
    parser = argparse.ArgumentParser(description='Converter for MaxMind (legacy)/ipinfo.io/db-ip.com CSV database to binary, for xt_geoip')
    parser.add_argument('-D', default='.', dest='target_dir', help='Target directory')
    parser.add_argument('-n', action='store_true', dest='native_only', help='Native only')
    parser.add_argument('--ignore-first-row', action='store_true', help='Ignore first row of the CSV files')
    parser.add_argument('--start-ip-col', type=int, default=0, help='Column index for start IP')
    parser.add_argument('--end-ip-col', type=int, default=1, help='Column index for end IP')
    parser.add_argument('--country-code-col', type=int, default=4, help='Column index for country code')
    # country-code-col default = 4 is for compatibility with legacy maxmind/geoip formats
    parser.add_argument('csv_files', nargs='+', help='CSV files/gz/zip')
    args = parser.parse_args()

    if not os.path.isdir(args.target_dir):
        sys.stderr.write(f"Target directory {args.target_dir} does not exist.\n")
        sys.exit(1)

    le32 = struct.pack('<I', 0x10000000)
    be32 = struct.pack('>I', 0x10000000)
    u32 = None
    dbs = ['LE', 'BE']

    if args.native_only:
        u32 = struct.pack('=I', 0x10000000)
        if u32 == le32:
            dbs = ['LE']
        elif u32 == be32:
            dbs = ['BE']
        else:
            sys.stderr.write("Cannot determine endianness.\n")
            sys.exit(1)

    for db in dbs:
        dir_path = os.path.join(args.target_dir, db)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    country_data = {}
    for csv_file in args.csv_files:
        if csv_file.endswith('.csv.gz'):
            with gzip.open(csv_file, mode='rt', newline='', encoding='utf-8') as gzfile:
                csvreader = csv.reader(gzfile, delimiter=',', quotechar='"')
                country_data = collect(csvreader, args.ignore_first_row, args.start_ip_col, args.end_ip_col, args.country_code_col, country_data)
        elif csv_file.endswith('.csv.zip'):
            with zipfile.ZipFile(csv_file, 'r') as zipf:
                for file_name in zipf.namelist():
                    if file_name.endswith('.csv'):
                        with zipf.open(file_name) as csvfile:
                            csvreader = csv.reader(csvfile.read().decode('utf-8').splitlines(), delimiter=',', quotechar='"')
                            country_data = collect(csvreader, args.ignore_first_row, args.start_ip_col, args.end_ip_col, args.country_code_col, country_data)
        else:
            with open(csv_file, newline='', encoding='utf-8') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                country_data = collect(csvreader, args.ignore_first_row, args.start_ip_col, args.end_ip_col, args.country_code_col, country_data)

    dump(args.target_dir, country_data, u32)

if __name__ == "__main__":
    main()
