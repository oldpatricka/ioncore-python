#!/usr/bin/env python

"""
@author Dorian Raymer
@author Michael Meisinger
@brief ION Exchange manager for CC.
"""

from twisted.internet import defer

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from ion.core.messaging import messaging
from ion.core.messaging.messaging import MessageSpace, ProcessExchangeSpace, Consumer
from ion.util.state_object import BasicLifecycleObject

DEFAULT_EXCHANGE_SPACE = 'magnet.topic'

class ExchangeManager(BasicLifecycleObject):
    """
    Manager class for capability container exchange management.
    """

    def __init__(self, container):
        BasicLifecycleObject.__init__(self)
        self.container = container

        # Container broker connection / vhost parameters
        self.message_space = None

        # Default exchange space
        self.exchange_space = None

    # Life cycle

    def on_initialize(self, config, *args, **kwargs):
        """
        """
        self.config = config

        # Configure the broker connection
        hostname = self.config['broker_host']
        port = self.config['broker_port']
        virtual_host = self.config['broker_vhost']
        username = self.config['broker_username']
        password = self.config['broker_password']
        credfile = self.config['broker_credfile']
        heartbeat = int(self.config['broker_heartbeat'])

        if credfile:
            username, password = open(credfile).read().split()

        # Is a BrokerConnection instance (no action at this point)
        self.message_space = MessageSpace(self,
                                hostname=hostname,
                                port=port,
                                virtual_host=virtual_host,
                                username=username,
                                password=password,
                                heartbeat=heartbeat)

        return defer.succeed(None)

    @defer.inlineCallbacks
    def on_activate(self, *args, **kwargs):
        """
        @retval Deferred
        """
        # Initiate the broker connection
        yield self.message_space.activate()
        self.client = self.message_space.client
        self.exchange_space = ProcessExchangeSpace(
                message_space=self.message_space,
                name=DEFAULT_EXCHANGE_SPACE)

    @defer.inlineCallbacks
    def on_terminate(self, *args, **kwargs):
        """
        @retval Deferred
        """

        # Close the broker connection
        yield self.message_space.terminate()

    def on_error(self, *args, **kwargs):
        raise RuntimeError("Illegal state change for ExchangeManager")

    # API

    @defer.inlineCallbacks
    def configure_messaging(self, name, config):
        """
        """
        if config['name_type'] == 'worker':
            name_type_f = messaging.worker
        elif config['name_type'] == 'direct':
            name_type_f = messaging.direct
        elif config['name_type'] == 'fanout':
            name_type_f = messaging.fanout
        else:
            raise RuntimeError("Invalid name_type: "+config['name_type'])

        amqp_config = name_type_f(name)
        amqp_config.update(config)
        res = yield Consumer.name(self.exchange_space, amqp_config)
        yield self.exchange_space.store.put(name, amqp_config)
        defer.returnValue(res)

    @defer.inlineCallbacks
    def new_consumer(self, name_config):
        """
        @brief create consumer
        @retval Deferred that fires a consumer instance
        """
        consumer = yield Consumer.name(self.exchange_space, name_config)
        defer.returnValue(consumer)

    def send(self, to_name, message_data, exchange_space=None, **kwargs):
        """
        Sends a message
        """
        exchange_space = exchange_space or self.container.exchange_manager.exchange_space
        return exchange_space.send(to_name, message_data, **kwargs)

    def connectionLost(self, reason):
        """
        Event triggered by the messaging manager when the amqp client goes
        down.
        The relationship between the exchange manager and the messaging
        manager is not well defined, so it is only via 'the force' that the
        messaging manager will understand that it should notify the
        exchange manager of things like connectionLost
        """
        self.container.exchangeConnectionLost(reason)
