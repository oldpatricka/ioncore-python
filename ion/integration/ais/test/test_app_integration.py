#!/usr/bin/env python

"""
@file ion/integration/test_app_integration.py
@test ion.integration.app_integration_service
@author David Everett
"""

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from twisted.internet import defer

#from ion.integration.r1integration_service import R1IntegrationServiceClient
from ion.integration.ais.app_integration_service import AppIntegrationServiceClient
from ion.core.messaging.message_client import MessageClient
from ion.test.iontest import IonTestCase

from ion.core.object import object_utils

addresslink_type = object_utils.create_type_identifier(object_id=20003, version=1)
person_type = object_utils.create_type_identifier(object_id=20001, version=1)


class AppIntegrationTest(IonTestCase):
    """
    Testing Application Integration Service.
    """

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        services = [
            {'name':'app_integration','module':'ion.integration.ais.app_integration_service','class':'AppIntegrationService'},
            {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{'servicename':'datastore'}},
            {'name':'resource_registry1','module':'ion.services.coi.resource_registry_beta.resource_registry','class':'ResourceRegistryService',
             'spawnargs':{'datastore_service':'datastore'}},
        ]
        sup = yield self._spawn_processes(services)

        self.sup = sup

        self.aisc = AppIntegrationServiceClient(proc=sup)
        #self.aisc = R1IntegrationServiceClient(proc=sup)
        #self.rc = ResourceClient(proc=sup)

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_app_integration(self):

        # Create a message client
        mc = MessageClient(proc=self.test_sup)

        # Use the message client to create a message object
        ### DHE: This is temporary; we won't be passing addresslink_type here, but we will need to pass a GPB
        log.debug('DHE: test_app_integration! instantiating addressbook resource.\n')        
        ab_msg = yield mc.create_instance(addresslink_type, MessageName='addressbook message')
        log.debug('DHE: test_app_integration! addressbook instantiated.\n')        
        
        #ab is a message instance of type addresslink 
        ab_msg.title = 'An addressbook object for testing'

        # Add a new entry in the list (repeated) persons of the addressbook
        ab_msg.person.add()

        # Make a new person object to go in the list
        ab_msg.person[0] = ab_msg.CreateObject(person_type)
        ab_msg.person[0].name = 'david'
        ab_msg.person[0].id = 59
        ab_msg.person[0].email = 'stringgggg'
        ab_msg.person[0].phone.add()
        ab_msg.person[0].phone[0].number = '401 789 6224'
        
        log.info('AddressBook! \n' + str(ab_msg))        
        
        log.debug('DHE: Calling findDateResource!!...')
        #outcome1 = yield self.aisc.createDataResource(ab_msg)
        outcome1 = yield self.aisc.findDataResources(ab_msg)
        log.debug('DHE: findDataResources returned:\n'+str(outcome1))
        