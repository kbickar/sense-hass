"""
Support for monitoring a Sense energy sensor.


"""
import logging
from datetime import timedelta

import requests.exceptions
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_API_KEY)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from sense_api import Senseable

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'

ACTIVE_NAME = 'Energy Usage'
ACTIVE_SOLAR_NAME = 'Solar Energy Generation'
DAILY_NAME = 'Daily Energy Usage'

ACTIVE_TYPE = 'active'
ACTIVE_SOLAR_TYPE = 'solar'
DAILY_TYPE = 'daily'

ICON = 'mdi:flash'

MIN_TIME_BETWEEN_DAILY_UPDATES = timedelta(seconds=150)
MIN_TIME_BETWEEN_ACTIVE_UPDATES = timedelta(seconds=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Sense sensor."""
    username = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)

    data = Senseable(username, password)

    @Throttle(MIN_TIME_BETWEEN_DAILY_UPDATES)
    def update_daily():
        """Update the daily power usage."""
        data.get_daily_usage()

    @Throttle(MIN_TIME_BETWEEN_ACTIVE_UPDATES)
    def update_active():
        """Update the active power usage."""
        data.get_realtime()

    update_daily()
    update_active()

    # Active power sensor
    add_devices(
        [Sense(data, ACTIVE_NAME, ACTIVE_TYPE, update_active),
         Sense(data, ACTIVE_SOLAR_NAME, ACTIVE_SOLAR_TYPE, update_active)])
    # Daily power sensor
    add_devices([Sense(data, DAILY_NAME, DAILY_TYPE, update_daily)])



class Sense(Entity):
    """Implementation of a Sense energy sensor."""

    def __init__(self, data, name, sensor_type, update_call):
        """Initialize the sensor."""
        self._name = name
        self._data = data
        self._sensor_type = sensor_type
        self.update_sensor = update_call
        self._state = None

        if sensor_type == ACTIVE_TYPE or sensor_type == ACTIVE_SOLAR_TYPE:
            self._unit_of_measurement = 'W'
        elif sensor_type == DAILY_TYPE:
            self._unit_of_measurement = 'kWh'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    def update(self):
        """Get the latest data, update state."""
        self.update_sensor()

        if self._sensor_type == ACTIVE_TYPE:
            self._state = round(self._data.active_power)
        elif self._sensor_type == ACTIVE_SOLAR_TYPE:
            self._state = round(self._data.active_solar_power)
        elif self._sensor_type == DAILY_TYPE:
            self._state = round(self._data.get_daily_usage(),1)

