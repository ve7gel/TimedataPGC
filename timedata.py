#!/usr/bin/env python3
"""
This is a Polyglot v2 NodeServer to provide various time based data for the ISY994 written in Python3
by Gordon Larsen
MIT License

"""
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface

import time
import sys
from datetime import datetime, timedelta
import calendar
from math import trunc

from suntime import Sun, SunTimeException
from utils import utils

"""
Import the polyglot interface module. This is in pypy so you can just install it
normally. Replace pip with pip3 if you are using python3.

"""

LOGGER = polyinterface.LOGGER
"""
polyinterface has a LOGGER that is created by default and logs to:
logs/debug.log
You can use LOGGER.info, LOGGER.warning, LOGGER.debug, LOGGER.error levels as needed.
"""


class TimeData(polyinterface.Controller):

    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super(TimeData, self).__init__(polyglot)
        self.name = 'ISY Time Data'
        self.address = 'timedata'
        self.primary = self.address
        self.loglevelsetting = 10
        self.loglevel = {
            0: 'None',
            10: 'Debug',
            20: 'Info',
            30: 'Error',
            40: 'Warning',
            50: 'Critical'
        }

        self.latitude = ''
        self.longitude = ''
        self.hemisphere = 'north' # Default to northern hemisphere

    def start(self):
        """
        Optional.
        Polyglot v2 Interface startup done. Here is where you start your integration.
        This will run, once the NodeServer connects to Polyglot and gets it's config.
        In this example I am calling a discovery method. While this is optional,
        this is where you should start. No need to Super this method, the parent
        version does nothing.
        """
        # This grabs the server.json data and checks profile_version is up to date

        LOGGER.info('Started Time Data NodeServer')
        serverdata = utils.get_server_data(LOGGER)
        LOGGER.debug("Server data: {}".format(serverdata))
        utils.update_version(LOGGER)
        utils.profile_zip(LOGGER)
        self.poly.installprofile()
        self.check_params()
        self.installSunNode()
        if self.latitude == '' or self.longitude == '':
            return

        self.getNodeUpdates()
        self.displaySunriseSunsetData_today()
        self.displaySunriseSunsetData_tomorrow()

    def shortPoll(self):
        self.getNodeUpdates()

    def longPoll(self):
        LOGGER.debug("In longPoll, Lat: {}, Lon: {}".format(self.latitude,self.longitude))
        if self.latitude == '' or self.longitude == '':
            return

        self.displaySunriseSunsetData_today()
        self.displaySunriseSunsetData_tomorrow()

    def query(self, command=None):
        """
        Optional.
        By default a query to the control node reports the FULL driver set for ALL
        nodes back to ISY. If you override this method you will need to Super or
        issue a reportDrivers() to each node manually.
        """
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def getNodeUpdates(self):
        if self.hemisphere == '':
            return

        today = datetime.now()

        timestruct = time.localtime()

        LOGGER.debug("Whole timestruct is {}".format(timestruct))

        self.setDriver('GV0', timestruct.tm_hour)
        self.setDriver('GV1', timestruct.tm_min)
        self.setDriver('GV2', timestruct.tm_mday)
        self.setDriver('GV3', timestruct.tm_mon)
        self.setDriver('GV4', timestruct.tm_year)
        self.setDriver('GV5', timestruct.tm_wday)
        # GV6
        weeknum = int(datetime.strftime(today, '%U')) + 1
        self.setDriver('GV6', weeknum)
        self.setDriver('GV7', timestruct.tm_yday)
        # GV8 - odd or even day?
        oe = int(timestruct.tm_mday) % 2
        self.setDriver('GV8', oe)
        # GV9
        minutesinyear = (int(timestruct.tm_yday) - 1) * 24 * 60
        minutesinyear = minutesinyear + int(timestruct.tm_hour) * 60 + int(timestruct.tm_min)
        self.setDriver('GV9', minutesinyear)

        localseason = self.season(datetime.now(), self.hemisphere)
        self.setDriver('GV10', localseason)
        # GV11
        # leapyear = leapYear(str(year) + '-' + str(month) + '-' + str(day))
        if calendar.isleap(int(timestruct.tm_year)):
            leapyear = 1
        else:
            leapyear = 0

        self.setDriver('GV11', leapyear)
        # GV12
        LOGGER.debug("UTC offset: {}".format(self.currenttz(timestruct.tm_isdst)))
        # self.setDriver('GV12', -time.timezone / 3600)
        self.setDriver('GV12', self.currenttz(timestruct.tm_isdst))

        self.setDriver('GV13', timestruct.tm_isdst)

        epochdays = trunc(round(datetime.now().timestamp()/(3600 * 24),0))
        self.setDriver('GV15', epochdays)

        hoursytd = timestruct.tm_yday
        hoursytd = hoursytd - 1
        hoursytd = hoursytd * 24 + timestruct.tm_hour
        self.setDriver('GV14', hoursytd)
        
        LOGGER.debug(
            "Stripped date string is {0}-{1}-{2} {3}:{4}, weekday {5}, days since epoch: {6}, hours this year: {7}".format(timestruct.tm_year, timestruct.tm_mon,
                                                                        timestruct.tm_mday, timestruct.tm_hour,
                                                                        timestruct.tm_min, timestruct.tm_wday, epochdays, hoursytd))
        LOGGER.debug(
            "Day of week {0}, Week number {1}, Day of Year {2}".format(timestruct.tm_wday, weeknum, timestruct.tm_yday))
        LOGGER.debug(
            "Minutes in year to now {0}, hemisphere {4}, season {1}, leap year {2}, isDST {3}".format(minutesinyear,
                                                                                                      localseason,
                                                                                                      leapyear,
                                                                                                      timestruct.tm_isdst,
                                                                                                      self.hemisphere))
    def displaySunriseSunsetData_today(self):
        # Sunrise and sunset calculations
        s = datetime.now()
        w_day = timedelta(days = 1)

        sundt, sun_sr, sun_ss = self.getsunrise_sunset(self.latitude, self.longitude, datetime.date(s))
        LOGGER.debug("In getsunrise_sunset, sun_sr:{0}, sun_ss:{1}".format(sun_sr, sun_ss))

        LOGGER.debug('On {} the sun rose  at {} and set at {}.'.format(sundt, sun_sr.strftime('%H:%M'), sun_ss.strftime('%H:%M')))
        self.nodes['sundata'].setDriver('ST', format(sun_sr.strftime('%-H')) )
        self.nodes['sundata'].setDriver('GV0', format(sun_sr.strftime('%-M')) )
        self.nodes['sundata'].setDriver('GV1', format(sun_ss.strftime('%-H')) )
        self.nodes['sundata'].setDriver('GV2', format(sun_ss.strftime('%-M')) )

    def displaySunriseSunsetData_tomorrow(self):
        # Sunrise and sunset calculations
        today = datetime.now()
        y = today.year
        m = today.month
        d = today.day

        s = datetime( y, m, d )
        LOGGER.debug("Today's date: {}".format( s ))
        s += timedelta( days=1 )
        LOGGER.debug("Tomorrow's date: {}".format( s ))

        sundt, sun_sr, sun_ss = self.getsunrise_sunset(self.latitude, self.longitude, datetime.date(s))
        LOGGER.debug('On {} the sun rises  at {} and sets at {}.'.format(sundt, sun_sr.strftime('%H:%M'), sun_ss.strftime('%H:%M')))

        self.nodes['sundata'].setDriver('GV3', format(sun_sr.strftime('%-H')) )
        self.nodes['sundata'].setDriver('GV4', format(sun_sr.strftime('%-M')) )
        self.nodes['sundata'].setDriver('GV5', format(sun_ss.strftime('%-H')) )
        self.nodes['sundata'].setDriver('GV6', format(sun_ss.strftime('%-M')) )

    def getsunrise_sunset(self, latitude, longitude, sundt):
        LOGGER.debug("Latitude: {0}, Longitude: {1}".format(float(self.latitude),float(self.longitude)))
        sun = Sun(float(latitude), float(longitude))
        sun_sr = sun.get_local_sunrise_time(sundt)
        sun_ss = sun.get_local_sunset_time(sundt)

        return sundt, sun_sr, sun_ss

    def currenttz(self, dst):
        if dst == 0:
            return -time.timezone / 3600
        elif dst == 1:
            return -time.altzone / 3600
        else:
            return 0

    def season(self, date, hemisphere):
        """
            date is a datetime object
            hemisphere is either 'north' or 'south', dependent on long/lat.
            https://stackoverflow.com/questions/16139306/determine-season-given-timestamp-in-python-using-datetime
        """
        md = date.month * 100 + date.day
        LOGGER.debug("md: {}".format(md))
        if (md > 320) and (md < 621):
            s = 0  # spring
        elif (md > 620) and (md < 923):
            s = 1  # summer
        elif (md > 922) and (md < 1223):
            s = 2  # fall
        else:
            s = 3  # winter

        if hemisphere != 'north':
            if s < 2:
                s += 2
            else:
                s -= 2

        return s

    def delete(self):
        LOGGER.info('Timedata Nodeserver deleted')

    def stop(self):
        LOGGER.info('Timedata NodeServer stopped.')

    def check_params(self):
        self.set_configuration(self.polyConfig)

        LOGGER.info("Setting configuration")
        LOGGER.debug("polyConfig: {}".format(self.polyConfig))
        #if float(self.latitude) >= 0:
        #    self.hemisphere = 'north'
        self.addCustomParam({
            'Latitude': self.latitude,
            'Longitude': self.longitude,
        })
        if 'Hemisphere' in self.polyConfig['customData']:
            self.hemisphere = self.polyConfig['customData']['Hemisphere']

        else:
            self.saveCustomData({'Hemisphere':self.hemisphere})

        if 'Loglevel' in self.polyConfig['customData']:
            self.loglevelsetting = self.polyConfig['customData']['Loglevel']
            self.setDriver('GV16', self.loglevelsetting)
            LOGGER.setLevel(self.loglevelsetting)
            LOGGER.info("Loglevel set to: {}".format(self.loglevel[self.loglevelsetting]))
            self.setDriver('GV16', self.loglevelsetting)

        else:
            self.saveCustomData({
                'Loglevel': self.loglevelsetting,  # set default loglevel to 'Info'
            })
            LOGGER.setLevel(self.loglevelsetting)
            LOGGER.info("Loglevel set to 10 (Debug)")
            self.setDriver('GV16', self.loglevelsetting)

        # Remove all existing notices
        LOGGER.info("remove all notices")
        self.removeNoticesAll()

        # Add a notice?
        if self.latitude == '':
            self.addNotice( "Latitude setting is required." )
        if self.longitude == '':
            self.addNotice( "Longitude setting is required." )

    def set_configuration(self, config):
        LOGGER.info("Checking existing configuration values")

        if 'Latitude' in config['customParams']:
            self.latitude = config['customParams']['Latitude']
        else:
            self.latitude = ''

        if 'Longitude' in config['customParams']:
            self.longitude = config['customParams']['Longitude']
        else:
            self.longitude = ''

        LOGGER.debug('polyConfig[params]: {}'.format(self.polyConfig['customParams']))

    def installSunNode(self):
        LOGGER.debug("Adding Sunrise/Sunset node")
        self.addNode(SunData(self, self.address, 'sundata', 'Sunrise and Sunset'))

    def remove_notices_all(self, command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self, command):
        LOGGER.info('update_profile:')
        utils.update_version(LOGGER)
        utils.profile_zip(LOGGER)
        st = self.poly.installprofile()
        return st

    def set_log_level(self, command):
        LOGGER.debug("Received command {} in 'set_log_level'".format(command))
        self.loglevelsetting = int(command.get('value'))
        LOGGER.setLevel(self.loglevelsetting)
        self.saveCustomData({
            'Loglevel': self.loglevelsetting,
        })
        LOGGER.info("Set Logging Level to {}".format(self.loglevel[self.loglevelsetting]))
        self.setDriver('GV16', self.loglevelsetting)

    id = 'ISYCalendar'

    commands = {
        'QUERY': query,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all,
        'LOG_LEVEL': set_log_level
    }

    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 0},
        {'driver': 'GV1', 'value': 0, 'uom': 0},
        {'driver': 'GV2', 'value': 0, 'uom': 0},
        {'driver': 'GV3', 'value': 0, 'uom': 25},
        {'driver': 'GV4', 'value': 0, 'uom': 0},
        {'driver': 'GV5', 'value': 0, 'uom': 25},
        {'driver': 'GV6', 'value': 0, 'uom': 0},
        {'driver': 'GV7', 'value': 0, 'uom': 0},
        {'driver': 'GV8', 'value': 0, 'uom': 25},
        {'driver': 'GV9', 'value': 0, 'uom': 0},
        {'driver': 'GV10', 'value': 0, 'uom': 25},
        {'driver': 'GV11', 'value': 0, 'uom': 2},
        {'driver': 'GV12', 'value': 0, 'uom': 0},
        {'driver': 'GV13', 'value': 0, 'uom': 2},
        {'driver': 'GV14', 'value': 0, 'uom': 0},
        {'driver': 'GV15', 'value': 0, 'uom': 0},
        {'driver': 'GV16', 'value': 0, 'uom': 25},
    ]
    """
        <st id="ST" editor="bool" />
        <st id="GV0" editor="I_HOUR" />
        <st id="GV1" editor="I_MINUTE" />
        <st id="GV2" editor="I_DOM" />
        <st id="GV3" editor="I_MONTH" />
        <st id="GV4" editor="I_NONE" />
        <st id="GV5" editor="I_WEEKDAY" />
        <st id="GV6" editor="I_WOY" />
        <st id="GV7" editor="I_DOY" />
        <st id="GV8" editor="ODDEVEN" />
        <st id="GV9" editor="I_NONE" />
        <st id="GV10" editor="SEASON" />
        <st id="GV11" editor="bool" />
        <st id="GV12" editor="I_TZ" />
        <st id="GV13" editor="bool" />
        <st id="GV14" editor="I_HOUR" />
        <st id="GV15" editor="I_HOUR" />
        <st id="GV16" editor="LOGLEVEL" />
    """
class SunData(polyinterface.Node):
    id = "sundata"

    def __init__ (self, controller, primary, address, name):

        super(SunData, self).__init__(controller, primary, address, name)

    def query(self):
        self.reportDrivers()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 0 }, # Sunrise hour today
        {'driver': 'GV0', 'value': 0, 'uom': 0 },  # Sunrise minute today
        {'driver': 'GV1', 'value': 0, 'uom': 0}, # Sunset hour today
        {'driver': 'GV2', 'value': 0, 'uom': 0},  # Sunset minute today
        {'driver': 'GV3', 'value': 0, 'uom': 0},  # Sunrise hour tomorrow
        {'driver': 'GV4', 'value': 0, 'uom': 0},  # Sunrise minute tomorrow
        {'driver': 'GV5', 'value': 0, 'uom': 0},  # Sunset hour tomorrow
        {'driver': 'GV6', 'value': 0, 'uom': 0},  # Sunset minute tomorrow
    ]

    commands = {
        'QUERY': query
    }


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('TimeData')
        """
        Instantiates the Interface to Polyglot.
        The name doesn't really matter unless you are starting it from the
        command line then you need a line Template=N
        where N is the slot number.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = TimeData(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit...")
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
        polyglot.stop()
    except Exception as err:
        LOGGER.error('Excption: {0}'.format(err), exc_info=True)
    sys.exit(0)
