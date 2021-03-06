#!/usr/bin/env python

"""
@file ion/services/dm/distribution/pubsub_service.py
@package ion.services.dm.distribution.pubsub
@author Paul Hubbard
@author Michael Meisinger
@author David Stuebe
@brief service for publishing on data streams, and for subscribing to streams.
The service includes methods for defining topics, defining publishers, publishing,
and defining subscriptions. See the PubSubClient for API documentation.
"""

import time
import re
from twisted.internet import defer

from ion.core.exception import ApplicationError
from ion.core.process.process import ProcessFactory
from ion.core.process.service_process import ServiceProcess, ServiceClient
from ion.core import ioninit
import ion.util.ionlog
from ion.core.object import object_utils
from ion.core.messaging.message_client import MessageClient
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.services.coi.exchange.exchange_management import ExchangeManagementClient

from ion.services.dm.inventory.association_service import PREDICATE_OBJECT_QUERY_TYPE
from ion.services.dm.inventory.association_service import AssociationServiceClient
from ion.services.coi.datastore_bootstrap.ion_preload_config import TYPE_OF_ID, \
    TOPIC_RESOURCE_TYPE_ID, EXCHANGE_SPACE_RES_TYPE_ID, EXCHANGE_POINT_RES_TYPE_ID, \
    PUBLISHER_RES_TYPE_ID, SUBSCRIBER_RES_TYPE_ID, QUEUE_RES_TYPE_ID

# Global objects
CONF = ioninit.config(__name__)
log = ion.util.ionlog.getLogger(__name__)

# References to protobuf message/object definitions
XS_TYPE = object_utils.create_type_identifier(object_id=2313, version=1)
XP_TYPE = object_utils.create_type_identifier(object_id=2309, version=1)
TOPIC_TYPE = object_utils.create_type_identifier(object_id=2307, version=1)
PUBLISHER_TYPE = object_utils.create_type_identifier(object_id=2310, version=1)
SUBSCRIBER_TYPE = object_utils.create_type_identifier(object_id=2311, version=1)
QUEUE_TYPE = object_utils.create_type_identifier(object_id=2308, version=1)
BINDING_TYPE = object_utils.create_type_identifier(object_id=2314, version=1)

# Generic request and response wrapper message types
REQUEST_TYPE = object_utils.create_type_identifier(object_id=10, version=1)
RESPONSE_TYPE = object_utils.create_type_identifier(object_id=12, version=1)
IDREF_TYPE = object_utils.create_type_identifier(object_id=4, version=1)

# Query and response types
REGEX_TYPE = object_utils.create_type_identifier(object_id=2306, version=1)
IDLIST_TYPE = object_utils.create_type_identifier(object_id=2312, version=1)

# Resource GPB objects
XS_RES_TYPE = object_utils.create_type_identifier(object_id=2315, version=1)
XP_RES_TYPE = object_utils.create_type_identifier(object_id=2316, version=1)
TOPIC_RES_TYPE = object_utils.create_type_identifier(object_id=2317, version=1)
PUBLISHER_RES_TYPE = object_utils.create_type_identifier(object_id=2318, version=1)
SUBSCRIBER_RES_TYPE = object_utils.create_type_identifier(object_id=2319, version=1)
QUEUE_RES_TYPE = object_utils.create_type_identifier(object_id=2321, version=1)
BINDING_RES_TYPE = object_utils.create_type_identifier(object_id=2320, version=1)

# Query and association types
PREDICATE_REFERENCE_TYPE = object_utils.create_type_identifier(object_id=25, version=1)

class PSSException(ApplicationError):
    """
    Exception class for the pubsub service.
    """

#noinspection PyUnusedLocal
class PubSubService(ServiceProcess):
    """
    @brief Refactored pubsub service
    @see http://oceanobservatories.org/spaces/display/CIDev/Pubsub+controller
    @todo Add runtime dependency on exchange management service

    Nomenclature:
    - In AMQP, the hierarchy is xs.xn
    - Topic becomes the routing key
    - XP is a topic exchange
    - XS is hardwired to 'swapmeet' (place to exchange)
    - XP is 'science_data'

    e.g.
    swapmeet / science_data / test.pydap.org:coads.nc

    that last field is subject to argument/debate/refactoring.

    @note PSC uses 'Niemand' here and there as a placeholder name
    @note PSC uses the current timestamp, string format, as a placeholder description
    """
    declare = ServiceProcess.service_declare(name='pubsub',
                                          version='0.1.2',
                                          dependencies=['DataStoreService',
                                                        'ExchangeManagementService',
                                                        'ResourceRegistryService',
                                                        'AssociationService'])

    def __init__(self, *args, **kwargs):
        super(PubSubService, self).__init__(*args, **kwargs)

    def slc_init(self):
        self.ems = ExchangeManagementClient(proc=self)
        self.rclient = ResourceClient(proc=self)
        self.mc = MessageClient(proc=self)
        self.asc = AssociationServiceClient(proc=self)

    def _check_msg_type(self, request, expected_type):
        """
        @brief Simple helper routine to validate the GPB that arrives against what's expected.
        Raising the exception will filter all the way back to the service client.
        @param request Incoming message, GPB assumed
        @param expected_type Typedef from object utils
        """
        if request.MessageType != expected_type:
            log.error('Bad message type, throwing exception')
            raise PSSException('Bad message type!',
                               request.ResponseCodes.BAD_REQUEST)

    @defer.inlineCallbacks
    def _key_to_field(self, key_string, field_name):
        """
        """
        idref = yield self.mc.create_instance(IDREF_TYPE)
        idref.key = key_string

        resource = yield self.rclient.get_instance(idref)

        defer.returnValue(getattr(resource, field_name))


    def _key_to_idref(self, key_string, object):
        """
        From a CASref key, create a full-on casref and append into id_list array
        @param key_string String, from casref key, e.g. 5A1E33DC-0B69-410F-B151-B7AC1D7E7C5D
        @param object Reply object we are modifying (in-place)
        @retval None
        """
        my_ref = object.CreateObject(IDREF_TYPE)
        my_ref.key = key_string
        idx = len(object.id_list)
        object.id_list.add()
        log.debug('Adding %s to index %d' % (key_string, idx))
        object.id_list[idx] = my_ref

    def _obj_to_ref(self, object):
        """
        @brief Generate a casref/idref from an object, so that proto bufs requiring
        CASrefs will work. It's a one-liner, but worth calling out.
        @param object Yep, object to reference
        @retval Reference to object
        """
        return self.rclient.reference_instance(object)

    @defer.inlineCallbacks
    def _do_registry_query(self, regex, resource_typedef):
        """
        @brief Query registry, apply regex to result
        @param regex regex to search
        @param msg Message provides context for reply_ok
        @param resource_typedef Stuebe magic field to denote what we're listing
        @retval Array of key strings
        """
        log.debug('registry query stirs the surface of the lake')
        query = yield self.mc.create_instance(PREDICATE_OBJECT_QUERY_TYPE)
        pair = query.pairs.add()

        log.debug('creating object')
        pred_ref = query.CreateObject(PREDICATE_REFERENCE_TYPE)
        pred_ref.key = TYPE_OF_ID
        pair.predicate = pred_ref

        log.debug('creating idref')
        type_ref = query.CreateObject(IDREF_TYPE)
        type_ref.key = resource_typedef

        pair.object = type_ref

        log.debug('sending off the query')
        result = yield self.asc.get_subjects(query)

        # @todo Filtering here and not in the registry performs more slowly. Move to registry.
        log.debug('regex filtering %d registry entries' % len(result.idrefs))
        idlist = []
        p = re.compile(regex)
        for cur_ref in result.idrefs:
            if p.search(cur_ref.key):
                idlist.append(cur_ref.key)

        log.debug('Registry query and filter done, %d results from %d records' %
                  (len(idlist), len(result.idrefs)))
        defer.returnValue(idlist)

    @defer.inlineCallbacks
    def _do_registry_query_and_reply(self, regex, msg, resource_typedef):
        """
        @retval None, sends reply off via reply_ok or reply_error
        @gpb{Results,2312,1}
        """

        idlist = yield self._do_registry_query(regex, resource_typedef)

        # Create response message
        response = yield self.mc.create_instance(IDLIST_TYPE)

        log.debug('Converting keys to idrefs')
        for cur_key in idlist:
            self._key_to_idref(cur_key, response)

        log.debug('drqr done')
        yield self.reply_ok(msg, response)

    @defer.inlineCallbacks
    def _rev_find(self, search_value, resource_type, field_name):
        """
        Prototyping an implementation of reverse find that uses the registry and
        associations.
        @note To emulate the python dictionary, it raises KeyError if not found.
        """
        log.debug('Reverse searching for "%s" in "%s"' % (search_value, field_name))

        log.debug('Querying association service for list of references')
        idref_list = yield self._do_registry_query('.+', resource_type)

        # Now we have a list of topic IDREFS. Gotta pull and search same individually.
        for cur_ref in idref_list:
            cur_resource = yield self.rclient.get_instance(cur_ref)
            if search_value == getattr(cur_resource, field_name):
                defer.returnValue(cur_resource.ResourceIdentity)

        raise KeyError('%s not in registry', search_value)

    @defer.inlineCallbacks
    def op_declare_exchange_space(self, request, headers, msg):
        """
        @see PubSubClient.declare_exchange_space
        """
        log.debug('DXS starting')
        self._check_msg_type(request, XS_TYPE)

        # Already declared?
        try:
            key = yield self._rev_find(request.exchange_space_name, EXCHANGE_SPACE_RES_TYPE_ID,
                                      'exchange_space_name')
            log.info('Exchange space "%s" already created, returning %s' %
                     (request.exchange_space_name, key))
            response = yield self.mc.create_instance(IDLIST_TYPE)
            self._key_to_idref(key, response)
            yield self.reply_ok(msg, response)
            return
        except KeyError:
            log.debug('XS not found, will go ahead and create')

        log.debug('Calling EMS to create the exchange space "%s"...'
                % request.exchange_space_name)
        # For now, use timestamp as description
        description = str(time.time())
        xsid = yield self.ems.create_exchangespace(request.exchange_space_name, description)

        log.debug('EMS returns ID %s for name %s' %
                  (xsid.resource_reference.key, request.exchange_space_name))

        # Write ID into registry
        log.debug('Creating resource instance')
        registry_entry = yield self.rclient.create_instance(XS_RES_TYPE, 'Niemand')

        # Populate registry entry message
        log.debug('Populating resource instance')
        registry_entry.exchange_space_name = request.exchange_space_name
        registry_entry.exchange_space_id = xsid.resource_reference

        log.debug('Writing resource record')
        yield self.rclient.put_instance(registry_entry)
        log.debug('Getting resource ID')
        xs_resource_id = self._obj_to_ref(registry_entry)

        log.debug('Operation completed, creating response message')

        response = yield self.mc.create_instance(IDLIST_TYPE)
        log.debug('Populating return message')
        response.id_list.add()
        response.id_list[0] = xs_resource_id
        response.MessageResponseCode = response.ResponseCodes.OK

        log.debug('Responding...')
        yield self.reply_ok(msg, response)
        log.debug('DXS completed OK')

    @defer.inlineCallbacks
    def op_undeclare_exchange_space(self, request, headers, msg):
        """
        @see PubSubClient.undeclare_exchange_space
        """
        log.debug('UDXS starting')
        self._check_msg_type(request, REQUEST_TYPE)

        # @todo Call EMS to remove the XS
        # @todo Remove resource record too
        log.warn('Here is where we ask EMS to remove the XS')

        yield self.reply_ok(msg)

    @defer.inlineCallbacks
    def op_query_exchange_spaces(self, request, headers, msg):
        """
        @see PubSubClient.query_exchange_spaces
        """
        log.debug('qxs starting')
        self._check_msg_type(request, REGEX_TYPE)
        yield self._do_registry_query_and_reply(request.regex, msg,
                                                EXCHANGE_SPACE_RES_TYPE_ID)

    @defer.inlineCallbacks
    def op_declare_exchange_point(self, request, headers, msg):
        """
        @see PubSubClient.declare_exchange_point
        """

        log.debug('Starting DXP')
        self._check_msg_type(request, XP_TYPE)

        # Already declared?
        try:
            key = yield self._rev_find(request.exchange_point_name,
                                       EXCHANGE_POINT_RES_TYPE_ID,
                                       'exchange_point_name')
            log.info('Exchange point "%s" already created, returning %s' %
                     (request.exchange_point_name, key))
            response = yield self.mc.create_instance(IDLIST_TYPE)
            self._key_to_idref(key, response)
            yield self.reply_ok(msg, response)
            return
        except KeyError:
            log.debug('XP not found, will go ahead and create')

        xs_resource = yield self.rclient.get_instance(request.exchange_space_id)

        # Found XS ID, now call EMS
        description = str(time.time())
        xpid = yield self.ems.create_exchangename(request.exchange_point_name,
                                                  description,
                                                  xs_resource.exchange_space_name)

        log.debug('EMS completed, returned XP ID "%s"' %
                  xpid.resource_reference.key)

        xp_resource = yield self.rclient.create_instance(XP_RES_TYPE,
                                                         'Niemand')

        log.debug('creating xp resource and populating')

        xp_resource.exchange_space_name = xs_resource.exchange_space_name
        xp_resource.exchange_space_id = request.exchange_space_id
        xp_resource.exchange_point_id = xpid.resource_reference
        xp_resource.exchange_point_name = request.exchange_point_name

        log.debug('Saving XP to registry')
        yield self.rclient.put_instance(xp_resource)
        xp_resource_id = self._obj_to_ref(xp_resource)

        log.debug('Creating reply')
        reply = yield self.mc.create_instance(IDLIST_TYPE)
        reply.id_list.add()
        reply.id_list[0] = xp_resource_id

        log.debug('DXP responding')
        yield self.reply_ok(msg, reply)
        log.debug('DXP completed OK')

    @defer.inlineCallbacks
    def op_undeclare_exchange_point(self, request, headers, msg):
        """
        @see PubSubClient.declare_exchange_point
        """
        log.debug('UDXP starting')
        self._check_msg_type(request, REQUEST_TYPE)

        # @todo Look up XS via XPID, call EMS to remove same...
        log.warn('This is where the Actual Work Goes...')
        yield self.reply_ok(msg)

    @defer.inlineCallbacks
    def op_query_exchange_points(self, request, headers, msg):
        """
        @see PubSubClient.query_exchange_points
        """
        log.debug('Starting XP query')
        self._check_msg_type(request, REGEX_TYPE)
        yield self._do_registry_query_and_reply(request.regex,msg,
                                                EXCHANGE_POINT_RES_TYPE_ID)

    @defer.inlineCallbacks
    def op_declare_topic(self, request, headers, msg):
        """
        @see PubSubClient.declare_exchange_topic
        """
        log.debug('Declare topic starting')
        self._check_msg_type(request, TOPIC_TYPE)

        # Already declared?
        try:
            key = yield self._rev_find(request.topic_name,
                                       TOPIC_RESOURCE_TYPE_ID, 'topic_name')
            log.info('Topic "%s" already created, returning %s' %
                     (request.topic_name, key))
            response = yield self.mc.create_instance(IDLIST_TYPE)
            self._key_to_idref(key, response)
            yield self.reply_ok(msg, response)
            return
        except KeyError:
            log.debug('Topic not found, will go ahead and create')

        xs_res = yield self.rclient.get_instance(request.exchange_space_id)
        xp_res = yield self.rclient.get_instance(request.exchange_point_id)

        log.debug('Creating and populating the resource')
        topic_resource = yield self.rclient.create_instance(TOPIC_RES_TYPE,
                                                            'Niemand')
        topic_resource.exchange_space_name = xs_res.exchange_space_name
        topic_resource.exchange_point_name = xp_res.exchange_point_name
        topic_resource.topic_name = request.topic_name
        topic_resource.exchange_space_id = request.exchange_space_id
        topic_resource.exchange_point_id = request.exchange_point_id

        log.debug('Saving resource...')
        yield self.rclient.put_instance(topic_resource)

        log.debug('Creating reply')
        reply = yield self.mc.create_instance(IDLIST_TYPE)

        log.debug('Creating reference to resource for return value')
        # We return by reference, so create same
        topic_ref = self._obj_to_ref(topic_resource)

        reply.id_list.add()
        reply.id_list[0] = topic_ref

        yield self.reply_ok(msg, reply)

    @defer.inlineCallbacks
    def op_undeclare_topic(self, request, headers, msg):
        """
        @see PubSubClient.undeclare_topic
        """

        log.debug('UDT starting')
        self._check_msg_type(request, REQUEST_TYPE)

        # @todo Remove instance from resource registry
        yield self.reply_ok(msg)

    @defer.inlineCallbacks
    def op_query_topics(self, request, headers, msg):
        """
        @see PubSubClient.query_topics
        """
        log.debug('Topic query starting')
        self._check_msg_type(request, REGEX_TYPE)
        yield self._do_registry_query_and_reply(request.regex,msg,
                                                TOPIC_RESOURCE_TYPE_ID)

    @defer.inlineCallbacks
    def op_declare_publisher(self, request, headers, msg):
        """
        @see PubSubClient.declare_exchange_publisher
        """

        log.debug('Starting DP')
        self._check_msg_type(request, PUBLISHER_TYPE)

        # Already declared?
        try:
            key = yield self._rev_find(request.publisher_name,
                                       PUBLISHER_RES_TYPE_ID,
                                       'publisher_name')
            log.info('Publisher "%s" already created, returning %s' \
                    % (request.publisher_name, key))
            response = yield self.mc.create_instance(IDLIST_TYPE)
            self._key_to_idref(key, response)
            yield self.reply_ok(msg, response)
            return
        except KeyError:
            log.debug('XS not found, will go ahead and create')


        # Verify that IDs exist
        xs_res = yield self.rclient.get_instance(request.exchange_space_id)
        xp_res = yield self.rclient.get_instance(request.exchange_point_id)
        topic_res = yield self.rclient.get_instance(request.topic_id)

        xs_name = xs_res.exchange_space_name
        xp_name = xp_res.exchange_point_name
        topic_name = topic_res.topic_name

        log.debug('Publisher context is %s/%s/%s' % \
                  (xs_name, xp_name, topic_name))

        log.debug('Creating and populating the publisher resource...')
        publ_resource = yield self.rclient.create_instance(PUBLISHER_RES_TYPE,
                                                           'Niemand')
        publ_resource.exchange_space_id = request.exchange_space_id
        publ_resource.exchange_point_id = request.exchange_point_id
        publ_resource.topic_id = request.topic_id
        publ_resource.publisher_name = request.publisher_name
        publ_resource.credentials = request.credentials

        log.debug('Saving publisher resource....')
        yield self.rclient.put_instance(publ_resource)

        # Need a reference return value
        pub_ref = self._obj_to_ref(publ_resource)

        log.debug('Creating reply')
        reply = yield self.mc.create_instance(IDLIST_TYPE)
        reply.id_list.add()
        reply.id_list[0] = pub_ref

        yield self.reply_ok(msg, reply)

    @defer.inlineCallbacks
    def op_undeclare_publisher(self, request, headers, msg):
        """
        @see PubSubClient.undeclare_publisher
        """
        log.debug('UDP starting')
        self._check_msg_type(request, REQUEST_TYPE)
        # @todo Delete from registry
        log.warn('This is where the Actual Work Goes...')
        yield self.reply_ok(msg)

    @defer.inlineCallbacks
    def op_query_publishers(self, request, headers, msg):
        log.debug('QP starting')
        self._check_msg_type(request, REGEX_TYPE)
        yield self._do_registry_query_and_reply(request.regex, msg,
                                                PUBLISHER_RES_TYPE_ID)

    @defer.inlineCallbacks
    def op_subscribe(self, request, headers, msg):
        """
        @see PubSubClient.subscribe
        """
        log.debug('PSC subscribe starting')
        self._check_msg_type(request, SUBSCRIBER_TYPE)

        xs_res = yield self.rclient.get_instance(request.exchange_space_id)
        xp_res = yield self.rclient.get_instance(request.exchange_point_id)
        topic_res = yield self.rclient.get_instance(request.topic_id)

        xs_name = xs_res.exchange_space_name
        xp_name = xp_res.exchange_point_name
        topic_name = topic_res.topic_name

        # Save into registry
        log.debug('Saving subscription into registry')
        sub_resource = yield self.rclient.create_instance(SUBSCRIBER_RES_TYPE,
                                                          'Niemand')
        sub_resource.exchange_space_id = request.exchange_space_id
        sub_resource.exchange_point_id = request.exchange_point_id
        sub_resource.topic_id = request.topic_id
        sub_resource.queue_name = str(time.time()) # Hack!

        yield self.rclient.put_instance(sub_resource)

        sub_ref = self._obj_to_ref(sub_resource)

        reply = yield self.mc.create_instance(IDLIST_TYPE)
        reply.id_list.add()
        reply.id_list[0] = sub_ref

        yield self.reply_ok(msg, reply)

    @defer.inlineCallbacks
    def op_unsubscribe(self, request, headers, msg):
        """
        @see PubSubClient.unsubscribe
        """
        log.debug('Starting unsub')
        self._check_msg_type(request, REQUEST_TYPE)
        # @todo Call EMS, delete from registry
        log.warn('Theres a wee bit of code left to do here....')
        yield self.reply_ok(msg)

    @defer.inlineCallbacks
    def op_query_subscribers(self, request, headers, msg):
        log.debug('QS starting')
        self._check_msg_type(request, REGEX_TYPE)
        yield self._do_registry_query_and_reply(request.regex, msg,
                                                SUBSCRIBER_RES_TYPE_ID)

    @defer.inlineCallbacks
    def op_declare_queue(self, request, headers, msg):
        """
        @see PubSubClient.declare_queue
        """
        log.debug('DQ starting')
        self._check_msg_type(request, QUEUE_TYPE)

        xs_res = yield self.rclient.get_instance(request.exchange_space_id)
        xp_res = yield self.rclient.get_instance(request.exchange_point_id)
        topic_res = yield self.rclient.get_instance(request.topic_id)

        xs_name = xs_res.exchange_space_name
        xp_name = xp_res.exchange_point_name
        topic_name = topic_res.topic_name

        log.debug('Queue context is %s/%s/%s' %
                  (xs_name, xp_name, topic_name))

        description = str(time.time())

        log.debug('Calling EMS to make the q')
        yield self.ems.create_queue(request.queue_name,
                                    description, xs_name, xp_name)
        
        log.debug('Creating registry object')
        q_resource = yield self.rclient.create_instance(QUEUE_RES_TYPE,
                                                        'Niemand')

        q_resource.exchange_space_id = request.exchange_space_id
        q_resource.exchange_point_id = request.exchange_point_id
        q_resource.topic_id = request.topic_id
        q_resource.queue_name = request.queue_name

        log.debug('Saving q into registry')
        yield self.rclient.put_instance(q_resource)
        log.debug('Creating reference')
        q_ref = self._obj_to_ref(q_resource)

        reply = yield self.mc.create_instance(IDLIST_TYPE)
        reply.id_list.add()
        reply.id_list[0] = q_ref

        yield self.reply_ok(msg, reply)

    @defer.inlineCallbacks
    def op_undeclare_queue(self, request, headers, msg):
        """
        @see PubSubClient.undeclare_queue
        @note Possible error if queue declared more than once and then deleted once
        """
        log.debug('Undeclare_q starting')
        self._check_msg_type(request, REQUEST_TYPE)

        # @todo Delete from registry
        log.warn('This is where the Actual Work Goes...')
        yield self.reply_ok(msg)

    @defer.inlineCallbacks
    def op_add_binding(self, request, headers, msg):
        """
        @see PubSubClient.add_binding
        """
        log.debug('PSC AB starting')
        self._check_msg_type(request, BINDING_TYPE)

        log.debug('Looking up queue for binding....')
        try:
            q_id = yield self._rev_find(request.queue_name,
                                        QUEUE_RES_TYPE_ID, 'queue_name')
        except KeyError:
            log.exception('Unable to locate queue for binding!')
            raise PSSException('AB error in lookup',
                               request.ResponseCodes.BAD_REQUEST)

        q_entry = yield self.rclient.get_instance(q_id)
        xs_res = yield self.rclient.get_instance(q_entry.exchange_space_id)
        xp_res = yield self.rclient.get_instance(q_entry.exchange_point_id)
        topic_res = yield self.rclient.get_instance(q_entry.topic_id)

        xs_name = xs_res.exchange_space_name
        xp_name = xp_res.exchange_point_name
        topic_name = topic_res.topic_name

        log.debug('Ready for EMS with %s/%s/%s and %s' % \
                  (xs_name, xp_name, topic_name, request.queue_name))
        
        description = str(time.time())
        rc = yield self.ems.create_binding('NoName', description,
                                           xs_name, xp_name,
                                           request.queue_name, topic_name)

        b_resource = yield self.rclient.create_instance(BINDING_RES_TYPE,
                                                        'Niemand')
        b_resource.queue_name = request.queue_name
        b_resource.binding = request.binding
        b_resource.queue_id = self._obj_to_ref(q_entry)

        yield self.rclient.put_instance(b_resource)

        log.debug('Binding added')
        yield self.reply_ok(msg)

class PubSubClient(ServiceClient):
    """
    @brief PubSub service client, refactored to use protocol buffer messaging.
    """
    def __init__(self, proc=None, **kwargs):
        if not 'targetname' in kwargs:
            kwargs['targetname'] = 'pubsub'
        ServiceClient.__init__(self, proc, **kwargs)

    @defer.inlineCallbacks
    def declare_exchange_space(self, params):
        """
        @brief Declare an exchange space, ok to call more than once (idempotent)
        @param params GPB, 2313/1, with exchange_space_name set to the desired string
        @GPB{Input,2313,1}
        @GPB{Returns,2312,1}
        @retval XS ID, GPB 2312/1, if zero-length then an error occurred
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('declare_exchange_space', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def undeclare_exchange_space(self, params):
        """
        @brief Remove an exchange space by ID
        @param params Exchange space ID, GPB 10/1, in field resource_reference
        @retval Generic return GPB 11/1
        @GPB{Input,10,1}
        @GPB{Returns,11,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('undeclare_exchange_space', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def query_exchange_spaces(self, params):
        """
        @brief List exchange spaces that match a regular expression
        @param params GPB, 2306/1, with 'regex' filled in
        @retval GPB, 2312/1, maybe zero-length if no matches.
        @retval error return also possible
        @GPB{Input,2306,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('query_exchange_spaces', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def declare_exchange_point(self, params):
        """
        @brief Declare/create and exchange point, which is a topic-routed exchange
        @note Must have parent exchange space id before calling this
        @param params GPB 2309/1, with exchange_point_name and exchange_space_id filled in
        @retval GPB 2312/1, zero length if error.
        @GPB{Input,2309,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('declare_exchange_point', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def undeclare_exchange_point(self, params):
        """
        @brief Remove an exchange point by ID
        @param params Exchange point ID, GPB 10/1, in field resource_reference
        @retval Generic return GPB 11/1
        @GPB{Input,10,1}
        @GPB{Returns,11,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('undeclare_exchange_point', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def query_exchange_points(self, params):
        """
        @brief List exchange points that match a regular expression
        @param params GPB, 2306/1, with 'regex' filled in
        @retval GPB, 2312/1, maybe zero-length if no matches.
        @retval error return also possible
        @GPB{Input,2306,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('query_exchange_points', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def declare_topic(self, params):
        """
        @brief Declare/create a topic in a given xs.xp. A topic is usually a dataset name.
        @param params GPB 2307/1, with xs and xp_ids set
        @retval GPB 2312/1, zero-length if error
        @GPB{Input,2307,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('declare_topic', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def undeclare_topic(self, params):
        """
        @brief Remove a topic by ID
        @param params Topic ID, GPB 10/1, in field resource_reference
        @retval Generic return GPB 11/1
        @GPB{Input,10,1}
        @GPB{Returns,11,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('undeclare_topic', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def query_topics(self, params):
        """
        @brief List topics that match a regular expression
        @param params GPB, 2306/1, with 'regex' filled in
        @retval GPB, 2312/1, maybe zero-length if no matches.
        @retval error return also possible
        @GPB{Input,2306,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('query_topics', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def declare_publisher(self, params):
        """
        @brief Declare/create a publisher in a given xs.xp.topic.
        @param params GPB 2310/1, with xs, xp and topic_ids set
        @retval GPB 2312/1, zero-length if error
        @GPB{Input,2310,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('declare_publisher', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def undeclare_publisher(self, params):
        """
        @brief Remove a publisher by ID
        @param params Publisher ID, GPB 10/1, in field resource_reference
        @retval Generic return GPB 11/1
        @GPB{Input,10,1}
        @GPB{Returns,11,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('undeclare_publisher', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def query_publishers(self, params):
        """
        @brief List publishers that match a regular expression
        @param params GPB, 2306/1, with 'regex' filled in
        @retval GPB, 2312/1, maybe zero-length if no matches.
        @retval error return also possible
        @GPB{Input,2306,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('query_publishers', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def undeclare_publisher(self, params):
        """
        @brief Remove a publisher by ID
        @param params Publisher ID, GPB 10/1, in field resource_reference
        @retval Generic return GPB 11/1
        @GPB{Input,10,1}
        @GPB{Returns,11,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('undeclare_publisher', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def subscribe(self, params):
        """
        @brief The core operation, subscribe to a dataset/source by xs.xp.topic
        @note Not fully fleshed out yet, interface subject to change
        @param params GPB 2311/1
        @retval GPB 2312/1, zero-length if a problem
        @GPB{Input,2311,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('subscribe', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def unsubscribe(self, params):
        """
        @brief Remove a subscription by ID
        @param params Subscription ID, GPB 10/1, in field resource_reference
        @retval Generic return GPB 11/1
        @GPB{Input,10,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('unsubscribe', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def query_subscribers(self, params):
        """
        @brief List subscriber that match a regular expression
        @param params @GPB(2306, 1) with 'regex' filled in
        @retval GPB, 2312/1, maybe zero-length if no matches.
        @retval error return also possible
        @GPB{Input,2306,1}
        @GPB{Returns,2312,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('query_subscribers', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def declare_queue(self, params):
        """
        @brief Create a listener queue for a subscription
        @param GPB 2308/1
        @retval None
        @GPB{Input,2308,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('declare_queue', params)
        defer.returnValue(content)

    @defer.inlineCallbacks
    def undeclare_queue(self, params):
        """
        @brief Undeclare (remove) a queue
        @param GPB 10/1, queue ID
        @retval OK or error
        @GPB{Input,10,1}
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('undeclare_queue', params)
        defer.returnValue(content)


    @defer.inlineCallbacks
    def add_binding(self, params):
        """
        @brief Add a binding to an existing queue
        @param params GPB 2314/1
        @GPB{Input,2314,1}
        @retval None
        """
        yield self._check_init()

        (content, headers, msg) = yield self.rpc_send('add_binding', params)
        defer.returnValue(content)

        
# Spawn off the process using the module name
factory = ProcessFactory(PubSubService)
