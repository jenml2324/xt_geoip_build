# xt_geoip_build
A Python implementation of the `xt_geoip_build` script that converts CSV GeoIP databases into the packed format used by the `xt_geoip` module of `xtables-addons`.

## Usage

```
usage: xt_geoip_build.py [-h] [-D TARGET_DIR] [-n] [--ignore-first-row] [--start-ip-col START_IP_COL] [--end-ip-col END_IP_COL] [--country-code-col COUNTRY_CODE_COL] csv_files/gz/zip [csv_files ...]
```

### Options

- `-D TARGET_DIR, --target-dir TARGET_DIR`: Specify the target directory for the output files (default is the current directory).
- `-n, --native-only`: Generate output only for the native endianness of the host system.
- `--ignore-first-row`: Ignore the first row of the CSV files.
- `--start-ip-col START_IP_COL`: Column index for the start IP (default is 0).
- `--end-ip-col END_IP_COL`: Column index for the end IP (default is 1).
- `--country-code-col COUNTRY_CODE_COL`: Column index for the country code (default is 4).

### Example with ipinfo.io - 'country.csv.gz'
Once you have downloaded the IP Country CSV database from ipinfo.io, you can execute the following command:
```bash
python3 xt_geoip_build.py -D /usr/share/xt_geoip /home/user/download/country.csv.gz
```

### Example with ipapi.is - 'geolocationDatabaseIPv4.csv'

The format of the ‘geolocationDatabaseIPv4.csv’ file is as follows:

```
ip_version,start_ip,end_ip,continent,country_code,country,state,city,zip,timezone,latitude,longitude,accuracy
4,193.12.111.24,193.12.111.31,EU,SE,Sweden,Stockholm,Stockholm,100 04,Europe/Stockholm,59.355596110016315,18.0615234375,2
```

In this example, the `start_ip`, `end_ip`, and `country_code` correspond to columns 1, 2, and 4, respectively. Additionally, the first row should be ignored. Therefore, the command to execute is:

```bash
python3 xt_geoip_build.py -D /usr/share/xt_geoip --ignore-first-row --start-ip-col 1 --end-ip-col 2 --country-code-col 4 geolocationDatabaseIPv4.csv
```

### ipinfo_io_country_csv_to_geoip_legacy_csv.py
This script converts `country.csv` from ipinfo.io into the Legacy CSV format supported by the original `xt_geoip_build`.

#### Usage
If you prefer to use the original `xt_geoip_build`, you can first convert the ipinfo.io CSV to the Legacy CSV format:

```bash
python3 ipinfo_io_country_csv_to_geoip_legacy_csv.py country.csv legacy.csv
```

Then execute the original build script:

```bash
perl /usr/lib/xtables-addons/xt_geoip_build -D /usr/share/xt_geoip legacy.csv
```

# Additional Information
I recommend using the database from ipinfo.io (You need an ipinfo.io account). It can be downloaded from:
- https://ipinfo.io/account/data-downloads > Free IP to Country (country.csv)
- Direct URL: https://ipinfo.io/data/free/country.csv.gz?token=$YOUR_IPINFO_IO_TOKEN

The following databases are also supported without manually specifying the column index:
- https://db-ip.com/db/download/ip-to-country-lite (dbip-country-lite-YYYY-MM.csv)
- https://mailfud.org/geoip-legacy/ (GeoIP-legacy.csv)
- https://ipapi.is/geolocation.html (geolocationDatabaseIPvX.csv)
