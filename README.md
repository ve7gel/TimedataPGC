# Timedata Nodeserver
A Timedata node server for the Universal Devices ISY994

Copyright 2020 Gordon Larsen MIT License

#### Installation
Latitude and Longitude entries are required to determine sundata and hemisphere.
Timezone offset SHOULD be DST aware, but has not been tested for every timezone permutation.

Tested OK on Polisy and RPi


## Release Notes
- 2.1.1 28/02/202
    - a couple of user suggested changes to UOMs.
- 2.1.0 27/02/2020
    - add hours since epoch and hours YTD per user requests.  This will require delete/add of NS to install new drivers.
- 2.0.4 26/02/2020
    - remove some stray non-unix characters that crept into one of the profile files, keeping it from loading properly
- 2.0.3 25/02/2020
    - some changes to ranges, uoms and titles
- 2.0.2 22/02/2020
    - remove leading zeros from driver updates
- 2.0.1 19/02/2020
    - change sun driver UOMs
- 2.0.0 18/02/2020
    - added secondary node with sunrise/sunset info 
- 1.0.3 12/02/2020
    - update editors to include negative hours for timezone
- 1.0.2 12/02/2020
    - fix leapyear code
- 1.0.1 11/02/2020
    - fix incorrect editor for month
- 1.0.0 09/02/2020 
    - Initial release.
