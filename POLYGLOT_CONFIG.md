
# TimedataPGC NodeServer Configuration
- longPoll
    - used to periodically update sunrise/sunset tables, default 1 hour

- shortPoll 
    - data update interval, default 30 seconds

#### Configuration Parameters for TimedataPGC
'Latitude'
 - Enter latitude in the form 12.3456, negative is south
 
'Longitude'
 - Enter longitude in the form 123.4567, negative is west

'Timezone'
 - Enter time zone in the form 'America/Vancouver'. Note that this parameter is required in the PGC version of this NS, as PGC operates in UTC time.
 
 Note that parameters are currently case sensitive.