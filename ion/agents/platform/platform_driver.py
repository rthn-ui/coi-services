#!/usr/bin/env python

"""
@package ion.agents.platform.platform_driver
@file    ion/agents/platform/platform_driver.py
@author  Carlos Rueda
@brief   Base class for platform drivers
         PRELIMINARY
"""

__author__ = 'Carlos Rueda'
__license__ = 'Apache 2.0'


from pyon.public import log


class DriverEvent(object):
    """
    Base class for driver events.
    """
    def __init__(self, ts):
        self._ts = ts


class AttributeValueDriverEvent(DriverEvent):
    """
    Event to notify the retrieved value for a platform attribute.
    """
    def __init__(self, ts, platform_id, attr_id, value):
        DriverEvent.__init__(self, ts)
        self._platform_id = platform_id
        self._attr_id = attr_id
        self._value = value

    def __str__(self):
        return "%s(platform_id=%r, attr_id=%r, value=%r, ts=%r)" % (
            self.__class__.__name__, self._platform_id, self._attr_id,
            self._value, self._ts)


class AlarmDriverEvent(DriverEvent):
    """
    Event to notify an alarm.
    """
    def __init__(self, ts, alarm_type, alarm_instance):
        DriverEvent.__init__(self, ts)
        self._alarm_type = alarm_type
        self._alarm_instance = alarm_instance

    def __str__(self):
        return "%s(alarm_type=%r, alarm_instance=%s, ts=%r)" % (
            self.__class__.__name__, self._alarm_type, self._alarm_instance,
            self._ts)


class PlatformDriver(object):
    """
    A platform driver handles a particular platform in a platform network.
    """

    def __init__(self, platform_id, driver_config, parent_platform_id=None):
        """
        @param platform_id ID of my associated platform.
        @param driver_config Driver configuration.
        @param parent_platform_id Platform ID of my parent, if any.
                    This is mainly used for diagnostic purposes
        """

        log.debug("%r: PlatformDriver constructor called", platform_id)

        self._platform_id = platform_id
        self._driver_config = driver_config
        self._parent_platform_id = parent_platform_id

        self._send_event = None

        # The dictionary defining the platform topology. If this dictionary is
        # not given, then other mechanism (eg., direct access to the external
        # platform system) is used to retrieve the information.
        self._topology = None

        # similar to _topology -- under initial testing -- may be merged
        self._agent_device_map = None
        self._agent_streamconfig_map = None

        # The root NNode defining the platform network rooted at the platform
        # identified by self._platform_id. This _nnode is constructed by the
        # driver based on _topology (if given) or other source of information.
        self._nnode = None

    def set_topology(self, topology, agent_device_map=None,
                     agent_streamconfig_map=None):
        """
        Sets the platform topology.
        """
        log.debug("set_topology: topology=%s", str(topology))
        log.debug("set_topology: agent_device_map=%s", str(agent_device_map))
        self._topology = topology
        self._agent_device_map = agent_device_map
        self._agent_streamconfig_map = agent_streamconfig_map

    def set_event_listener(self, evt_recv):
        """
        (to support similar setting in instrument-agent:
          driver_client.start_messaging(self.evt_recv)
        )
        Sets the listener of events generated by this driver.
        """
        self._send_event = evt_recv

    def ping(self):
        """
        To be implemented by subclass.
        Verifies communication with external platform returning "PONG" if
        this verification completes OK.

        @retval "PONG"
        @raise PlatformConnectionException
        """
        raise NotImplemented()

    def go_active(self):
        """
        To be implemented by subclass.
        Main task here is to determine the topology of platforms
        rooted here then assigning the corresponding definition to self._nnode.

        @raise PlatformConnectionException
        """
        raise NotImplemented()

    def get_metadata(self):
        """
        To be implemented by subclass.
        Returns the metadata associated to the platform.

        @raise PlatformConnectionException
        """
        raise NotImplemented()

    def get_attribute_values(self, attr_names, from_time):
        """
        To be implemented by subclass.
        Returns the values for specific attributes since a given time.

        @param attr_names [attrName, ...] desired attributes
        @param from_time NTP v4 compliant string; time from which the values are requested

        @retval {attrName : [(attrValue, timestamp), ...], ...}
                dict indexed by attribute name with list of (value, timestamp)
                pairs. Timestamps are NTP v4 compliant strings
        """
        raise NotImplemented()

    def set_attribute_values(self, attrs):
        """
        To be implemented by subclass.
        Sets values for writable attributes in this platform.

        @param attrs 	[(attrName, attrValue), ...] 	List of attribute values

        @retval {platform_id: {attrName : [(attrValue, timestamp), ...], ...}}
                dict with a single entry for the requested platform ID and value
                as a list of (value,timestamp) pairs for each attribute indicated
                in the input. Returned timestamps are NTP v4 8-byte strings
                indicating the time when the value was set.
        """
        raise NotImplemented()

    def get_ports(self):
        """
        To be implemented by subclass.
        Returns information about the ports associated to the platform.

        @raise PlatformConnectionException
        """
        raise NotImplemented()

    def set_up_port(self, port_id, attributes):
        """
        To be implemented by subclass.
        Sets up a port in this platform.

        @param port_id      Port ID
        @param attributes   Attribute dictionary

        @retval The resulting configuration of the port.

        @raise PlatformConnectionException
        """
        raise NotImplemented()

    def get_subplatform_ids(self):
        """
        Gets the IDs of the subplatforms of this driver's associated
        platform. This is based on self._nnode, which should have been
        assigned by a call to go_active.
        """
        assert self._nnode is not None, "go_active should have been called first"
        return self._nnode.subplatforms.keys()

    def start_resource_monitoring(self):
        """
        To be implemented by subclass.
        Starts greenlets to periodically retrieve values of the attributes
        associated with my platform, and do corresponding event notifications.
        """
        raise NotImplemented()

    def stop_resource_monitoring(self):
        """
        To be implemented by subclass.
        Stops all the monitoring greenlets.
        """
        raise NotImplemented()

    def destroy(self):
        """
        Stops all activity done by the driver. In this base class,
        this method calls self.stop_resource_monitoring()
        """
        self.stop_resource_monitoring()

    def _notify_driver_event(self, driver_event):
        """
        Convenience method for subclasses to send a driver event to
        corresponding platform agent.

        @param driver_event a DriverEvent object.
        """
        log.debug("platform driver=%r: notify driver_event=%s",
            self._platform_id, driver_event)

        assert isinstance(driver_event, DriverEvent)

        if self._send_event:
            self._send_event(driver_event)
        else:
            log.warn("self._send_event not set to notify driver_event=%s",
                     str(driver_event))

    def start_alarm_dispatch(self, params):
        """
        To be implemented by subclass.
        Starts the dispatch of alarms received from the platform network to do
        corresponding event notifications.
        """
        raise NotImplemented()

    def stop_alarm_dispatch(self):
        """
        To be implemented by subclass.
        Stops the dispatch of alarms received from the platform network.
        """
        raise NotImplemented()
