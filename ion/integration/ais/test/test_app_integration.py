#!/usr/bin/env python

"""
@file ion/integration/test_app_integration.py
@test ion.integration.app_integration_service
@author David Everett
"""

from twisted.trial import unittest

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from twisted.internet import defer

from ion.core.object import object_utils
from ion.core.messaging.message_client import MessageClient
from ion.core.exception import ReceivedApplicationError
from ion.core.data.storage_configuration_utility import COMMIT_INDEXED_COLUMNS, COMMIT_CACHE
from ion.services.coi.datastore_bootstrap.ion_preload_config import MYOOICI_USER_ID, ROOT_USER_ID, ANONYMOUS_USER_ID

from ion.core.data import store
from ion.services.coi.datastore import ION_DATASETS_CFG, PRELOAD_CFG, ION_AIS_RESOURCES_CFG

from ion.test.iontest import IonTestCase

from ion.integration.ais.app_integration_service import AppIntegrationServiceClient

# import GPB type identifiers for AIS
from ion.integration.ais.ais_object_identifiers import AIS_REQUEST_MSG_TYPE, \
                                                       AIS_RESPONSE_MSG_TYPE, \
                                                       AIS_RESPONSE_ERROR_TYPE
from ion.integration.ais.ais_object_identifiers import REGISTER_USER_REQUEST_TYPE, \
                                                       UPDATE_USER_PROFILE_REQUEST_TYPE, \
                                                       REGISTER_USER_RESPONSE_TYPE, \
                                                       GET_USER_PROFILE_REQUEST_TYPE, \
                                                       GET_USER_PROFILE_RESPONSE_TYPE, \
                                                       FIND_DATA_RESOURCES_REQ_MSG_TYPE, \
                                                       GET_DATA_RESOURCE_DETAIL_REQ_MSG_TYPE, \
                                                       CREATE_DOWNLOAD_URL_REQ_MSG_TYPE, \
                                                       GET_RESOURCES_OF_TYPE_REQUEST_TYPE, \
                                                       GET_RESOURCES_OF_TYPE_RESPONSE_TYPE, \
                                                       GET_RESOURCE_TYPES_RESPONSE_TYPE, \
                                                       GET_RESOURCE_REQUEST_TYPE, \
                                                       GET_RESOURCE_RESPONSE_TYPE, \
                                                       SUBSCRIBE_DATA_RESOURCE_REQ_TYPE, \
<<<<<<< HEAD
                                                       SUBSCRIBE_DATA_RESOURCE_RSP_TYPE, \
                                                       FIND_DATA_SUBSCRIPTIONS_REQ_TYPE, \
                                                       FIND_DATA_SUBSCRIPTIONS_RSP_TYPE, \
                                                       DELETE_SUBSCRIPTION_REQ_TYPE
=======
                                                       SUBSCRIBE_DATA_RESOURCE_RSP_TYPE
>>>>>>> dd66528c9aaeb804ba2f8479ca5593b7f64896b9

# Create CDM Type Objects
datasource_type = object_utils.create_type_identifier(object_id=4502, version=1)
dataset_type = object_utils.create_type_identifier(object_id=10001, version=1)
group_type = object_utils.create_type_identifier(object_id=10020, version=1)
dimension_type = object_utils.create_type_identifier(object_id=10018, version=1)
variable_type = object_utils.create_type_identifier(object_id=10024, version=1)
bounded_array_type = object_utils.create_type_identifier(object_id=10021, version=1)
array_structure_type = object_utils.create_type_identifier(object_id=10025, version=1)

attribute_type = object_utils.create_type_identifier(object_id=10017, version=1)
stringArray_type = object_utils.create_type_identifier(object_id=10015, version=1)
float32Array_type = object_utils.create_type_identifier(object_id=10013, version=1)
int32Array_type = object_utils.create_type_identifier(object_id=10009, version=1)

#
# ResourceID for testing create download URL response
#
TEST_RESOURCE_ID = '01234567-8abc-def0-1234-567890123456'


class AppIntegrationTest(IonTestCase):
   
    """
    Testing Application Integration Service.
    """

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

        store.Store.kvs.clear()
        store.IndexStore.kvs.clear()
        store.IndexStore.indices.clear()

        services = [
            {'name':'app_integration','module':'ion.integration.ais.app_integration_service','class':'AppIntegrationService'},
            {'name':'index_store_service','module':'ion.core.data.index_store_service','class':'IndexStoreService',
                'spawnargs':{'indices':COMMIT_INDEXED_COLUMNS}},
            {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{PRELOAD_CFG:{ION_DATASETS_CFG:True, ION_AIS_RESOURCES_CFG:True},
                          COMMIT_CACHE:'ion.core.data.store.IndexStore'}},
            {'name':'association_service', 'module':'ion.services.dm.inventory.association_service', 'class':'AssociationService'},
            {'name':'dataset_controller', 'module':'ion.services.dm.inventory.dataset_controller', 'class':'DatasetControllerClient'},
            {'name':'resource_registry1','module':'ion.services.coi.resource_registry.resource_registry','class':'ResourceRegistryService',
             'spawnargs':{'datastore_service':'datastore'}},
            {'name':'identity_registry','module':'ion.services.coi.identity_registry','class':'IdentityRegistryService'}
        ]
        log.debug('AppIntegrationTest.setUp(): spawning processes')
        sup = yield self._spawn_processes(services)
        log.debug('AppIntegrationTest.setUp(): spawned processes')

        self.sup = sup

        self.aisc = AppIntegrationServiceClient(proc=sup)

    @defer.inlineCallbacks
    def tearDown(self):
        log.info('Tearing Down Test Container')

        store.Store.kvs.clear()
        store.IndexStore.kvs.clear()
        store.IndexStore.indices.clear()

        yield self._shutdown_processes()
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_findDataResources(self):

        log.debug('Testing findDataResources.')

        #
        # Send a message with no bounds
        #
        
        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # Use the message client to create a message object
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        #reqMsg.message_parameters_reference.minLatitude  = 30
        #reqMsg.message_parameters_reference.maxLatitude  = 45
        #reqMsg.message_parameters_reference.minLongitude = -75
        #reqMsg.message_parameters_reference.maxLongitude = -70
        #reqMsg.message_parameters_reference.minVertical  = 20
        #reqMsg.message_parameters_reference.maxVertical  = 30
        #reqMsg.message_parameters_reference.posVertical  = 'down'
        #reqMsg.message_parameters_reference.minTime      = '2011-03-01T00:00:00Z'
        #reqMsg.message_parameters_reference.maxTime      = '2011-03-05T00:02:00Z'

        
        log.debug('Calling findDataResources to get list of resources.')
        rspMsg = yield self.aisc.findDataResources(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResources failed: " + rspMsg.error_str)


        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        log.debug('findDataResources returned: ' + str(numResReturned) + ' resources.')

        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)

        #
        # Send a message with bounds
        #
        
        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # Use the message client to create a message object
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.minLatitude  = 30
        reqMsg.message_parameters_reference.maxLatitude  = 45
        reqMsg.message_parameters_reference.minLongitude = -75
        reqMsg.message_parameters_reference.maxLongitude = -70
        reqMsg.message_parameters_reference.minVertical  = 20
        reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2011-03-01T00:00:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2011-03-05T00:02:00Z'

        
        log.debug('Calling findDataResources to get list of resources.')
        rspMsg = yield self.aisc.findDataResources(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResources failed: " + rspMsg.error_str)

        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        log.debug('findDataResources returned: ' + str(numResReturned) + ' resources.')

        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)

        #
        # Send a message with bounds
        #
        
        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # Use the message client to create a message object
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.minLatitude  = -50
        #reqMsg.message_parameters_reference.maxLatitude  = 45
        reqMsg.message_parameters_reference.minLongitude = -70
        #reqMsg.message_parameters_reference.maxLongitude = -70
        reqMsg.message_parameters_reference.minVertical  = 10
        #reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2008-08-01T00:50:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2008-08-01T15:50:00Z'

        
        log.debug('Calling findDataResources to get list of resources.')
        rspMsg = yield self.aisc.findDataResources(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResources failed: " + rspMsg.error_str)

        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        log.debug('findDataResources returned: ' + str(numResReturned) + ' resources.')

        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)


    @defer.inlineCallbacks
    def test_findDataResourcesByUser(self):

        log.debug('Testing findDataResourcesByUser.')

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        #
        # Send a request without a resourceID to test that the appropriate error
        # is returned.
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        #reqMsg.message_parameters_reference.user_ooi_id  = 'Dr. Chew'
        reqMsg.message_parameters_reference.minLatitude  = 40.2216682434
        reqMsg.message_parameters_reference.maxLatitude  = 40.2216682434
        reqMsg.message_parameters_reference.minLongitude = -74.13
        reqMsg.message_parameters_reference.maxLongitude = -73.50
        reqMsg.message_parameters_reference.minVertical  = 20
        reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2010-07-26T00:02:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2010-07-26T00:02:00Z'

        log.debug('Calling findDataResourcesByUser to without ooi_user_id: should fail.')
        rspMsg = yield self.aisc.findDataResourcesByUser(reqMsg)
        if rspMsg.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('rspMsg to GPB w/missing user_ooi_ID is not an AIS_RESPONSE_ERROR_TYPE GPB')
        

        #
        # Send a request with a temporal bounds covered by data time 
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        #reqMsg.message_parameters_reference.user_ooi_id  = '621F69FC-37C3-421F-8AE9-4D762A2718C9'
        reqMsg.message_parameters_reference.user_ooi_id  = ANONYMOUS_USER_ID
        reqMsg.message_parameters_reference.minLatitude  = -50
        reqMsg.message_parameters_reference.maxLatitude  = -40
        reqMsg.message_parameters_reference.minLongitude = 20
        reqMsg.message_parameters_reference.maxLongitude = 30
        reqMsg.message_parameters_reference.minVertical  = 20
        reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2008-08-1T10:00:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2008-08-1T11:00:00Z'

        log.debug('Calling findDataResourcesByUser to get list of resources.')
        rspMsg = yield self.aisc.findDataResourcesByUser(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResourcesByUser failed: " + rspMsg.error_str)

        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        if numResReturned == 0:
            self.fail('findDataResourcesByUser returned zero resources.')
        
        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)

        #
        # Send a request with temporal bounds that covers data time
        # Data Start Time: 2008-08-01T00:50:00Z
        # Data End Time:   2008-08-01T23:50:00Z
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id  = ANONYMOUS_USER_ID
        reqMsg.message_parameters_reference.minLatitude  = -50
        reqMsg.message_parameters_reference.maxLatitude  = -40
        reqMsg.message_parameters_reference.minLongitude = 20
        reqMsg.message_parameters_reference.maxLongitude = 30
        reqMsg.message_parameters_reference.minVertical  = 20
        reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2007-01-1T00:02:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2009-08-1T00:02:00Z'

        log.debug('Calling findDataResourcesByUser to get list of resources.')
        rspMsg = yield self.aisc.findDataResourcesByUser(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResourcesByUser failed: " + rspMsg.error_str)

        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        if numResReturned == 0:
            self.fail('findDataResourcesByUser returned zero resources.')
        
        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)

        #
        # Send a request with a temporal bounds minTime covered by data time, but
        # temporal bounds maxTime > dataTime (should still return data)
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id  = ANONYMOUS_USER_ID
        reqMsg.message_parameters_reference.minLatitude  = -50
        reqMsg.message_parameters_reference.maxLatitude  = -40
        reqMsg.message_parameters_reference.minLongitude = 20
        reqMsg.message_parameters_reference.maxLongitude = 30
        reqMsg.message_parameters_reference.minVertical  = 20
        reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2008-01-1T00:02:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2010-01-1T11:00:00Z'

        log.debug('Calling findDataResourcesByUser to get list of resources.')
        rspMsg = yield self.aisc.findDataResourcesByUser(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResourcesByUser failed: " + rspMsg.error_str)
        
        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        if numResReturned == 0:
            self.fail('findDataResourcesByUser returned zero resources.')
        
        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)

        #
        # Send a request with a temporal bounds maxTime covered by data time, but
        # temporal bounds minTime < dataTime (should still return data)
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id  = ANONYMOUS_USER_ID
        reqMsg.message_parameters_reference.minLatitude  = -50
        reqMsg.message_parameters_reference.maxLatitude  = -40
        reqMsg.message_parameters_reference.minLongitude = 20
        reqMsg.message_parameters_reference.maxLongitude = 30
        reqMsg.message_parameters_reference.minVertical  = 20
        reqMsg.message_parameters_reference.maxVertical  = 30
        reqMsg.message_parameters_reference.posVertical  = 'down'
        reqMsg.message_parameters_reference.minTime      = '2007-01-1T10:00:00Z'
        reqMsg.message_parameters_reference.maxTime      = '2008-08-1T11:00:00Z'

        log.debug('Calling findDataResourcesByUser to get list of resources.')
        rspMsg = yield self.aisc.findDataResourcesByUser(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResourcesByUser failed: " + rspMsg.error_str)
        
        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        if numResReturned == 0:
            self.fail('findDataResourcesByUser returned zero resources.')

        self.__validateDataResourceSummary(rspMsg.message_parameters_reference[0].dataResourceSummary)


    @defer.inlineCallbacks
    def test_getDataResourceDetail(self):

        log.debug('Testing getDataResourceDetail.')

        #
        # Create a message client
        #
        mc = MessageClient(proc=self.test_sup)

        #
        # Send a request without a resourceID to test that the appropriate error
        # is returned.
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(GET_DATA_RESOURCE_DETAIL_REQ_MSG_TYPE)

        log.debug('Calling getDataResourceDetail without resource ID.')
        rspMsg = yield self.aisc.getDataResourceDetail(reqMsg)
        if rspMsg.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('rspMsg to GPB w/missing resource ID is not an AIS_RESPONSE_ERROR_TYPE GPB')
        
        #
        # In order to test getDataResourceDetail, we need a dataset resource
        # ID.  So, first use findDataResources to get the instances of data
        # resources that match some test criteria, and the first resource ID
        # out of the results.
        #
        log.debug('DHE: AppIntegrationService! instantiating FindResourcesMsg.\n')
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id = 'Dr. Chew'
        #reqMsg.message_parameters_reference.minLatitude = 40.2216682434
        #reqMsg.message_parameters_reference.maxLatitude = 40.2216682434
        #reqMsg.message_parameters_reference.minLongitude = -74.13
        #reqMsg.message_parameters_reference.maxLongitude = -73.50
        
        log.debug('Calling findDataResources.')
        rspMsg = yield self.aisc.findDataResources(reqMsg)

        if len(rspMsg.message_parameters_reference) > 0:
            if len(rspMsg.message_parameters_reference[0].dataResourceSummary) > 0:
                dsID = rspMsg.message_parameters_reference[0].dataResourceSummary[0].data_resource_id
        
                #
                # Now create a request message to get the metadata details about the
                # source (i.e., where the dataset came from) of a particular dataset
                # resource ID.
                #
                reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
                reqMsg.message_parameters_reference = reqMsg.CreateObject(GET_DATA_RESOURCE_DETAIL_REQ_MSG_TYPE)
                reqMsg.message_parameters_reference.data_resource_id = dsID

                log.debug('Calling getDataResourceDetail.')
                rspMsg = yield self.aisc.getDataResourceDetail(reqMsg)
                log.debug('getDataResourceDetail returned:\n' + \
                    str('resource_id: ') + \
                    str(rspMsg.message_parameters_reference[0].data_resource_id) + \
                    str('\n'))

                dSource = rspMsg.message_parameters_reference[0].source
                log.debug('Source Metadata for Dataset:\n')
                for property in dSource.property:
                    log.debug('  Property: ' + property)
                for station_id in dSource.station_id:
                    log.debug('  Station_ID: ' + station_id)
 
                log.debug('  RequestType: ' + str(dSource.request_type))
                log.debug('  Base URL: ' + dSource.base_url)
                log.debug('  Max Ingest Millis: ' + str(dSource.max_ingest_millis))

                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('title'):
                    #self.fail('response to findDataResources has no title field')
                    log.error('response to findDataResources has no title field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('institution'):
                    #self.fail('response to findDataResources has no institution field')
                    log.error('response to findDataResources has no institution field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('source'):
                    #self.fail('response to findDataResources has no source field')
                    log.error('response to findDataResources has no source field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('references'):
                    #self.fail('response to findDataResources has no references field')
                    log.error('response to findDataResources has no references field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_time_coverage_start'):
                    self.fail('response to findDataResources has no ion_time_coverage_start field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_time_coverage_end'):
                    self.fail('response to findDataResources has no ion_time_coverage_end field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('summary'):
                    #self.fail('response to findDataResources has no summary field')
                    log.error('response to findDataResources has no summary field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('comment'):
                    #self.fail('response to findDataResources has no comment field')
                    log.error('response to findDataResources has no comment field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_lat_min'):
                    self.fail('response to findDataResources has no ion_geospatial_lat_min field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_lat_max'):
                    self.fail('response to findDataResources has no ion_geospatial_lat_max field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_lon_min'):
                    self.fail('response to findDataResources has no ion_geospatial_lon_min field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_lon_max'):
                    self.fail('response to findDataResources has no ion_geospatial_lon_max field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_vertical_min'):
                    self.fail('response to findDataResources has no ion_geospatial_vertical_min field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_vertical_max'):
                    self.fail('response to findDataResources has no ion_geospatial_vertical_max field')
                if not rspMsg.message_parameters_reference[0].dataResourceSummary.IsFieldSet('ion_geospatial_vertical_positive'):
                    self.fail('response to findDataResources has no ion_geospatial_vertical_positive field')

                log.debug('Minimum Metadata Variables:\n')
                for var in rspMsg.message_parameters_reference[0].variable:
                    log.debug('  Variable:\n')
                    log.debug('    standard_name: ' + var.standard_name + '\n')
                    log.debug('    long_name: ' + var.long_name + '\n')
                    log.debug('    units: ' + var.units + '\n')
                    for attrib in var.other_attributes:
                        log.debug('    Other Attributes:\n')
                        log.debug('      ' + str(attrib) + str('\n'))


        
    @defer.inlineCallbacks
    def test_createDownloadURL(self):

        log.debug('Testing createDownloadURL')

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        #
        # Send a request without a resourceID to test that the appropriate error
        # is returned.
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(CREATE_DOWNLOAD_URL_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id = 'Dr. Chew'

        log.debug('Calling createDownloadURL without resource ID.')
        rspMsg = yield self.aisc.createDownloadURL(reqMsg)
        if rspMsg.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('rspMsg to GPB w/missing resource ID is not an AIS_RESPONSE_ERROR_TYPE GPB')
        
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(CREATE_DOWNLOAD_URL_REQ_MSG_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id = 'Dr. Chew'
        reqMsg.message_parameters_reference.data_resource_id = TEST_RESOURCE_ID

        log.debug('Calling createDownloadURL.')
        rspMsg = yield self.aisc.createDownloadURL(reqMsg)
        downloadURL = rspMsg.message_parameters_reference[0].download_url
        log.debug('DHE: createDownloadURL returned:\n' + downloadURL)
        if TEST_RESOURCE_ID not in downloadURL:
            self.fail("createDownloadURL response does not contain resourceID")


    @defer.inlineCallbacks
    def test_registerUser(self):

        # Create a message client
        mc = MessageClient(proc=self.test_sup)

        # create the register_user request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS RegisterUser request')
        msg.message_parameters_reference = msg.CreateObject(REGISTER_USER_REQUEST_TYPE)
        
        # fill in the certificate and key
        msg.message_parameters_reference.certificate = """-----BEGIN CERTIFICATE-----
MIIEMzCCAxugAwIBAgICBQAwDQYJKoZIhvcNAQEFBQAwajETMBEGCgmSJomT8ixkARkWA29yZzEX
MBUGCgmSJomT8ixkARkWB2NpbG9nb24xCzAJBgNVBAYTAlVTMRAwDgYDVQQKEwdDSUxvZ29uMRsw
GQYDVQQDExJDSUxvZ29uIEJhc2ljIENBIDEwHhcNMTAxMTE4MjIyNTA2WhcNMTAxMTE5MTAzMDA2
WjBvMRMwEQYKCZImiZPyLGQBGRMDb3JnMRcwFQYKCZImiZPyLGQBGRMHY2lsb2dvbjELMAkGA1UE
BhMCVVMxFzAVBgNVBAoTDlByb3RlY3ROZXR3b3JrMRkwFwYDVQQDExBSb2dlciBVbndpbiBBMjU0
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6QhsWxhUXbIxg+1ZyEc7d+hIGvchVmtb
g0kKLmivgoVsA4U7swNDRH6svW242THta0oTf6crkRx7kOKg6jma2lcAC1sjOSddqX7/92ChoUPq
7LWt2T6GVVA10ex5WAeB/o7br/Z4U8/75uCBis+ru7xEDl09PToK20mrkcz9M4HqIv1eSoPkrs3b
2lUtQc6cjuHRDU4NknXaVMXTBHKPM40UxEDHJueFyCiZJFg3lvQuSsAl4JL5Z8pC02T8/bODBuf4
dszsqn2SC8YDw1xrujvW2Bd7Q7BwMQ/gO+dZKM1mLJFpfEsR9WrjMeg6vkD2TMWLMr0/WIkGC8u+
6M6SMQIDAQABo4HdMIHaMAwGA1UdEwEB/wQCMAAwDgYDVR0PAQH/BAQDAgSwMBMGA1UdJQQMMAoG
CCsGAQUFBwMCMBgGA1UdIAQRMA8wDQYLKwYBBAGCkTYBAgEwagYDVR0fBGMwYTAuoCygKoYoaHR0
cDovL2NybC5jaWxvZ29uLm9yZy9jaWxvZ29uLWJhc2ljLmNybDAvoC2gK4YpaHR0cDovL2NybC5k
b2Vncmlkcy5vcmcvY2lsb2dvbi1iYXNpYy5jcmwwHwYDVR0RBBgwFoEUaXRzYWdyZWVuMUB5YWhv
by5jb20wDQYJKoZIhvcNAQEFBQADggEBAEYHQPMY9Grs19MHxUzMwXp1GzCKhGpgyVKJKW86PJlr
HGruoWvx+DLNX75Oj5FC4t8bOUQVQusZGeGSEGegzzfIeOI/jWP1UtIjzvTFDq3tQMNvsgROSCx5
CkpK4nS0kbwLux+zI7BWON97UpMIzEeE05pd7SmNAETuWRsHMP+x6i7hoUp/uad4DwbzNUGIotdK
f8b270icOVgkOKRdLP/Q4r/x8skKSCRz1ZsRdR+7+B/EgksAJj7Ut3yiWoUekEMxCaTdAHPTMD/g
Mh9xL90hfMJyoGemjJswG5g3fAdTP/Lv0I6/nWeH/cLjwwpQgIEjEAVXl7KHuzX5vPD/wqQ=
-----END CERTIFICATE-----"""
        msg.message_parameters_reference.rsa_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA6QhsWxhUXbIxg+1ZyEc7d+hIGvchVmtbg0kKLmivgoVsA4U7swNDRH6svW24
2THta0oTf6crkRx7kOKg6jma2lcAC1sjOSddqX7/92ChoUPq7LWt2T6GVVA10ex5WAeB/o7br/Z4
U8/75uCBis+ru7xEDl09PToK20mrkcz9M4HqIv1eSoPkrs3b2lUtQc6cjuHRDU4NknXaVMXTBHKP
M40UxEDHJueFyCiZJFg3lvQuSsAl4JL5Z8pC02T8/bODBuf4dszsqn2SC8YDw1xrujvW2Bd7Q7Bw
MQ/gO+dZKM1mLJFpfEsR9WrjMeg6vkD2TMWLMr0/WIkGC8u+6M6SMQIDAQABAoIBAAc/Ic97ZDQ9
tFh76wzVWj4SVRuxj7HWSNQ+Uzi6PKr8Zy182Sxp74+TuN9zKAppCQ8LEKwpkKtEjXsl8QcXn38m
sXOo8+F1He6FaoRQ1vXi3M1boPpefWLtyZ6rkeJw6VP3MVG5gmho0VaOqLieWKLP6fXgZGUhBvFm
yxUPoNgXJPLjJ9pNGy4IBuQDudqfJeqnbIe0GOXdB1oLCjAgZlTR4lFA92OrkMEldyVp72iYbffN
4GqoCEiHi8lX9m2kvwiQKRnfH1dLnnPBrrwatu7TxOs02HpJ99wfzKRy4B1SKcB0Gs22761r+N/M
oO966VxlkKYTN+soN5ID9mQmXJkCgYEA/h2bqH9mNzHhzS21x8mC6n+MTyYYKVlEW4VSJ3TyMKlR
gAjhxY/LUNeVpfxm2fY8tvQecWaW3mYQLfnvM7f1FeNJwEwIkS/yaeNmcRC6HK/hHeE87+fNVW/U
ftU4FW5Krg3QIYxcTL2vL3JU4Auu3E/XVcx0iqYMGZMEEDOcQPcCgYEA6sLLIeOdngUvxdA4KKEe
qInDpa/coWbtAlGJv8NueYTuD3BYJG5KoWFY4TVfjQsBgdxNxHzxb5l9PrFLm9mRn3iiR/2EpQke
qJzs87K0A/sxTVES29w1PKinkBkdu8pNk10TxtRUl/Ox3fuuZPvyt9hi5c5O/MCKJbjmyJHuJBcC
gYBiAJM2oaOPJ9q4oadYnLuzqms3Xy60S6wUS8+KTgzVfYdkBIjmA3XbALnDIRudddymhnFzNKh8
rwoQYTLCVHDd9yFLW0d2jvJDqiKo+lV8mMwOFP7GWzSSfaWLILoXcci1ZbheJ9607faxKrvXCEpw
xw36FfbgPfeuqUdI5E6fswKBgFIxCu99gnSNulEWemL3LgWx3fbHYIZ9w6MZKxIheS9AdByhp6px
lt1zeKu4hRCbdtaha/TMDbeV1Hy7lA4nmU1s7dwojWU+kSZVcrxLp6zxKCy6otCpA1aOccQIlxll
Vc2vO7pUIp3kqzRd5ovijfMB5nYwygTB4FwepWY5eVfXAoGBAIqrLKhRzdpGL0Vp2jwtJJiMShKm
WJ1c7fBskgAVk8jJzbEgMxuVeurioYqj0Cn7hFQoLc+npdU5byRti+4xjZBXSmmjo4Y7ttXGvBrf
c2bPOQRAYZyD2o+/MHBDsz7RWZJoZiI+SJJuE4wphGUsEbI2Ger1QW9135jKp6BsY2qZ
-----END RSA PRIVATE KEY-----"""

        # try to register this user for the first time
        reply = yield self.aisc.registerUser(msg)
        log.debug('registerUser returned:\n'+str(reply))
        log.debug('registerUser returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        if reply.message_parameters_reference[0].ObjectType != REGISTER_USER_RESPONSE_TYPE:
            self.fail('response does not contain an OOI_ID GPB')
        if reply.message_parameters_reference[0].user_already_registered != False:
            self.fail("response does not indicate user wasn't already registered")
        if reply.message_parameters_reference[0].user_is_admin != True:
            self.fail("response does not indicate user is administrator")
        if reply.message_parameters_reference[0].user_is_early_adopter != True:
            self.fail("response does not indicate user is an early adopter")
        FirstOoiId = reply.message_parameters_reference[0].ooi_id
        log.info("test_registerUser: first time registration received GPB = "+str(reply.message_parameters_reference[0]))
            
        # try to re-register this user for a second time
        reply = yield self.aisc.registerUser(msg)
        log.debug('registerUser returned:\n'+str(reply))
        log.debug('registerUser returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        if reply.message_parameters_reference[0].ObjectType != REGISTER_USER_RESPONSE_TYPE:
            self.fail('response does not contain an OOI_ID GPB')
        if reply.message_parameters_reference[0].user_already_registered != True:
            self.fail("response does not indicate user was already registered")
        if reply.message_parameters_reference[0].user_is_admin != True:
            self.fail("response does not indicate user is administrator")
        if reply.message_parameters_reference[0].user_is_early_adopter != True:
            self.fail("response does not indicate user is an early adopter")
        if FirstOoiId != reply.message_parameters_reference[0].ooi_id:
            self.fail("re-registration did not return the same OoiId as registration")
        log.info("test_registerUser: re-registration received GPB = "+str(reply.message_parameters_reference[0]))
        
        # try to send registerUser the wrong GPB
        # create a bad request GPBs
        msg = yield mc.create_instance(AIS_RESPONSE_MSG_TYPE, MessageName='AIS bad request')
        reply = yield self.aisc.registerUser(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB is not an AIS_RESPONSE_ERROR_TYPE GPB')

        # try to send registerUser incomplete GPBs
        # create a bad GPB request w/o payload
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS bad request')
        reply = yield self.aisc.registerUser(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to registerUser is not an AIS_RESPONSE_ERROR_TYPE GPB')
        # create a bad GPB request w/o certificate
        msg.message_parameters_reference = msg.CreateObject(REGISTER_USER_REQUEST_TYPE)
        reply = yield self.aisc.registerUser(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to registerUser is not an AIS_RESPONSE_ERROR_TYPE GPB')
        # create a bad GPB request w/o key
        msg.message_parameters_reference.certificate = "dumming certificate"
        reply = yield self.aisc.registerUser(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to registerUser is not an AIS_RESPONSE_ERROR_TYPE GPB')
            
    @defer.inlineCallbacks
    def test_updateUserProfile_getUser(self):

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # comment these tests out until updateUserProfile is added to the policy service
        # test for authentication policy failure
        # create the update Email request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS updateUserProfile request')
        msg.message_parameters_reference = msg.CreateObject(UPDATE_USER_PROFILE_REQUEST_TYPE)
        msg.message_parameters_reference.user_ooi_id = "ANONYMOUS"
        msg.message_parameters_reference.email_address = "some_person@some_place.some_domain"
        try:
            reply = yield self.aisc.updateUserProfile(msg)
            self.fail('updateUserProfile did not raise exception for ANONYMOUS ooi_id')
        except ReceivedApplicationError, ex:
            log.info("updateUserProfile correctly raised exception for ANONYMOUS ooi_id")
            
        # create the getUser request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS updateUserProfile request')
        msg.message_parameters_reference = msg.CreateObject(GET_USER_PROFILE_REQUEST_TYPE)
        msg.message_parameters_reference.user_ooi_id = "ANONYMOUS"
        try:
            reply = yield self.aisc.getUser(msg)
            self.fail('getUser did not raise exception for ANONYMOUS ooi_id')
        except ReceivedApplicationError, ex:
            log.info("getUser correctly raised exception for ANONYMOUS ooi_id")
        
        # create the register_user request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS RegisterUser request')
        msg.message_parameters_reference = msg.CreateObject(REGISTER_USER_REQUEST_TYPE)
        
        # fill in the certificate and key
        msg.message_parameters_reference.certificate = """-----BEGIN CERTIFICATE-----
MIIEMzCCAxugAwIBAgICBQAwDQYJKoZIhvcNAQEFBQAwajETMBEGCgmSJomT8ixkARkWA29yZzEX
MBUGCgmSJomT8ixkARkWB2NpbG9nb24xCzAJBgNVBAYTAlVTMRAwDgYDVQQKEwdDSUxvZ29uMRsw
GQYDVQQDExJDSUxvZ29uIEJhc2ljIENBIDEwHhcNMTAxMTE4MjIyNTA2WhcNMTAxMTE5MTAzMDA2
WjBvMRMwEQYKCZImiZPyLGQBGRMDb3JnMRcwFQYKCZImiZPyLGQBGRMHY2lsb2dvbjELMAkGA1UE
BhMCVVMxFzAVBgNVBAoTDlByb3RlY3ROZXR3b3JrMRkwFwYDVQQDExBSb2dlciBVbndpbiBBMjU0
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6QhsWxhUXbIxg+1ZyEc7d+hIGvchVmtb
g0kKLmivgoVsA4U7swNDRH6svW242THta0oTf6crkRx7kOKg6jma2lcAC1sjOSddqX7/92ChoUPq
7LWt2T6GVVA10ex5WAeB/o7br/Z4U8/75uCBis+ru7xEDl09PToK20mrkcz9M4HqIv1eSoPkrs3b
2lUtQc6cjuHRDU4NknXaVMXTBHKPM40UxEDHJueFyCiZJFg3lvQuSsAl4JL5Z8pC02T8/bODBuf4
dszsqn2SC8YDw1xrujvW2Bd7Q7BwMQ/gO+dZKM1mLJFpfEsR9WrjMeg6vkD2TMWLMr0/WIkGC8u+
6M6SMQIDAQABo4HdMIHaMAwGA1UdEwEB/wQCMAAwDgYDVR0PAQH/BAQDAgSwMBMGA1UdJQQMMAoG
CCsGAQUFBwMCMBgGA1UdIAQRMA8wDQYLKwYBBAGCkTYBAgEwagYDVR0fBGMwYTAuoCygKoYoaHR0
cDovL2NybC5jaWxvZ29uLm9yZy9jaWxvZ29uLWJhc2ljLmNybDAvoC2gK4YpaHR0cDovL2NybC5k
b2Vncmlkcy5vcmcvY2lsb2dvbi1iYXNpYy5jcmwwHwYDVR0RBBgwFoEUaXRzYWdyZWVuMUB5YWhv
by5jb20wDQYJKoZIhvcNAQEFBQADggEBAEYHQPMY9Grs19MHxUzMwXp1GzCKhGpgyVKJKW86PJlr
HGruoWvx+DLNX75Oj5FC4t8bOUQVQusZGeGSEGegzzfIeOI/jWP1UtIjzvTFDq3tQMNvsgROSCx5
CkpK4nS0kbwLux+zI7BWON97UpMIzEeE05pd7SmNAETuWRsHMP+x6i7hoUp/uad4DwbzNUGIotdK
f8b270icOVgkOKRdLP/Q4r/x8skKSCRz1ZsRdR+7+B/EgksAJj7Ut3yiWoUekEMxCaTdAHPTMD/g
Mh9xL90hfMJyoGemjJswG5g3fAdTP/Lv0I6/nWeH/cLjwwpQgIEjEAVXl7KHuzX5vPD/wqQ=
-----END CERTIFICATE-----"""
        msg.message_parameters_reference.rsa_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA6QhsWxhUXbIxg+1ZyEc7d+hIGvchVmtbg0kKLmivgoVsA4U7swNDRH6svW24
2THta0oTf6crkRx7kOKg6jma2lcAC1sjOSddqX7/92ChoUPq7LWt2T6GVVA10ex5WAeB/o7br/Z4
U8/75uCBis+ru7xEDl09PToK20mrkcz9M4HqIv1eSoPkrs3b2lUtQc6cjuHRDU4NknXaVMXTBHKP
M40UxEDHJueFyCiZJFg3lvQuSsAl4JL5Z8pC02T8/bODBuf4dszsqn2SC8YDw1xrujvW2Bd7Q7Bw
MQ/gO+dZKM1mLJFpfEsR9WrjMeg6vkD2TMWLMr0/WIkGC8u+6M6SMQIDAQABAoIBAAc/Ic97ZDQ9
tFh76wzVWj4SVRuxj7HWSNQ+Uzi6PKr8Zy182Sxp74+TuN9zKAppCQ8LEKwpkKtEjXsl8QcXn38m
sXOo8+F1He6FaoRQ1vXi3M1boPpefWLtyZ6rkeJw6VP3MVG5gmho0VaOqLieWKLP6fXgZGUhBvFm
yxUPoNgXJPLjJ9pNGy4IBuQDudqfJeqnbIe0GOXdB1oLCjAgZlTR4lFA92OrkMEldyVp72iYbffN
4GqoCEiHi8lX9m2kvwiQKRnfH1dLnnPBrrwatu7TxOs02HpJ99wfzKRy4B1SKcB0Gs22761r+N/M
oO966VxlkKYTN+soN5ID9mQmXJkCgYEA/h2bqH9mNzHhzS21x8mC6n+MTyYYKVlEW4VSJ3TyMKlR
gAjhxY/LUNeVpfxm2fY8tvQecWaW3mYQLfnvM7f1FeNJwEwIkS/yaeNmcRC6HK/hHeE87+fNVW/U
ftU4FW5Krg3QIYxcTL2vL3JU4Auu3E/XVcx0iqYMGZMEEDOcQPcCgYEA6sLLIeOdngUvxdA4KKEe
qInDpa/coWbtAlGJv8NueYTuD3BYJG5KoWFY4TVfjQsBgdxNxHzxb5l9PrFLm9mRn3iiR/2EpQke
qJzs87K0A/sxTVES29w1PKinkBkdu8pNk10TxtRUl/Ox3fuuZPvyt9hi5c5O/MCKJbjmyJHuJBcC
gYBiAJM2oaOPJ9q4oadYnLuzqms3Xy60S6wUS8+KTgzVfYdkBIjmA3XbALnDIRudddymhnFzNKh8
rwoQYTLCVHDd9yFLW0d2jvJDqiKo+lV8mMwOFP7GWzSSfaWLILoXcci1ZbheJ9607faxKrvXCEpw
xw36FfbgPfeuqUdI5E6fswKBgFIxCu99gnSNulEWemL3LgWx3fbHYIZ9w6MZKxIheS9AdByhp6px
lt1zeKu4hRCbdtaha/TMDbeV1Hy7lA4nmU1s7dwojWU+kSZVcrxLp6zxKCy6otCpA1aOccQIlxll
Vc2vO7pUIp3kqzRd5ovijfMB5nYwygTB4FwepWY5eVfXAoGBAIqrLKhRzdpGL0Vp2jwtJJiMShKm
WJ1c7fBskgAVk8jJzbEgMxuVeurioYqj0Cn7hFQoLc+npdU5byRti+4xjZBXSmmjo4Y7ttXGvBrf
c2bPOQRAYZyD2o+/MHBDsz7RWZJoZiI+SJJuE4wphGUsEbI2Ger1QW9135jKp6BsY2qZ
-----END RSA PRIVATE KEY-----"""

        # try to register this user for the first time
        reply = yield self.aisc.registerUser(msg)
        log.debug('registerUser returned:\n'+str(reply))
        log.debug('registerUser returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        if reply.message_parameters_reference[0].ObjectType != REGISTER_USER_RESPONSE_TYPE:
            self.fail('response does not contain an OOI_ID GPB')
        FirstOoiId = reply.message_parameters_reference[0].ooi_id
        log.info("test_registerUser: first time registration received GPB = "+str(reply.message_parameters_reference[0]))
        
        # create the update Profile request GPBs for setting the email address
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS updateUserProfile request')
        msg.message_parameters_reference = msg.CreateObject(UPDATE_USER_PROFILE_REQUEST_TYPE)
        msg.message_parameters_reference.user_ooi_id = FirstOoiId
        msg.message_parameters_reference.email_address = "some_person@some_place.some_domain"
        try:
            reply = yield self.aisc.updateUserProfile(msg)
        except ReceivedApplicationError, ex:
            self.fail('updateUserProfile incorrectly raised exception for an authenticated ooi_id')
        log.debug('updateUserProfile returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')

        # create the update Profile request GPBs for setting the profile
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS updateUserProfile request')
        msg.message_parameters_reference = msg.CreateObject(UPDATE_USER_PROFILE_REQUEST_TYPE)
        msg.message_parameters_reference.user_ooi_id = FirstOoiId
        msg.message_parameters_reference.profile.add()
        msg.message_parameters_reference.profile[0].name = "ProfileItem_1_Name"
        msg.message_parameters_reference.profile[0].value = "ProfileItem_1_Value"
        msg.message_parameters_reference.profile.add()
        msg.message_parameters_reference.profile[1].name = "ProfileItem_2_Name"
        msg.message_parameters_reference.profile[1].value = "ProfileItem_2_Value"
        try:
            reply = yield self.aisc.updateUserProfile(msg)
        except ReceivedApplicationError, ex:
            self.fail('updateUserProfile incorrectly raised exception for an authenticated ooi_id')
        log.debug('updateUserProfile returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
            
        # test that the email & profile got set
        # create the getUser request GPBs for getting the email/profile
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS getUser request')
        msg.message_parameters_reference = msg.CreateObject(GET_USER_PROFILE_REQUEST_TYPE)
        msg.message_parameters_reference.user_ooi_id = FirstOoiId
        try:
            reply = yield self.aisc.getUser(msg)
        except ReceivedApplicationError, ex:
            self.fail('getUser incorrectly raised exception for an authenticated ooi_id')
        log.debug('getUser returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response from getUser is not an AIS_RESPONSE_MSG_TYPE GPB')
        self.assertEqual(reply.message_parameters_reference[0].email_address, "some_person@some_place.some_domain")
        self.assertEqual(reply.message_parameters_reference[0].profile[0].name, "ProfileItem_1_Name")
        self.assertEqual(reply.message_parameters_reference[0].profile[0].value, "ProfileItem_1_Value")
        self.assertEqual(reply.message_parameters_reference[0].profile[1].name, "ProfileItem_2_Name")
        self.assertEqual(reply.message_parameters_reference[0].profile[1].value, "ProfileItem_2_Value")


        # try to send updateUserProfile the wrong GPB
        # create a bad request GPBs
        msg = yield mc.create_instance(AIS_RESPONSE_MSG_TYPE, MessageName='AIS bad request')
        reply = yield self.aisc.updateUserProfile(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to updateUserProfile is not an AIS_RESPONSE_ERROR_TYPE GPB')

        # try to send updateUserProfile incomplete GPBs
        # create a bad GPB request w/o payload
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS bad request')
        reply = yield self.aisc.updateUserProfile(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to updateUserProfile to is not an AIS_RESPONSE_ERROR_TYPE GPB')
        # create a bad GPB request w/o ooi_id
        msg.message_parameters_reference = msg.CreateObject(UPDATE_USER_PROFILE_REQUEST_TYPE)
        reply = yield self.aisc.updateUserProfile(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to updateUserProfile is not an AIS_RESPONSE_ERROR_TYPE GPB')
        # create a bad GPB request w/o emsil address
        msg.message_parameters_reference.user_ooi_id = "Some-ooi_id"
        reply = yield self.aisc.updateUserProfile(msg)
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad GPB to updateUserProfile is not an AIS_RESPONSE_ERROR_TYPE GPB')

    @defer.inlineCallbacks
    def test_getResourceTypes(self):

        ResourceTypes = ['datasets', 'identities', 'datasources', 'epucontrollers']
        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # create the empty request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS getResourceTypes request')
        reply = yield self.aisc.getResourceTypes(msg)
        log.debug('getResourceTypes returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResourceTypes returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCE_TYPES_RESPONSE_TYPE:
            self.fail('response to getResourceTypes is not a GET_RESOURCE_TYPES_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('resource_types_list'):
            self.fail('response to getResourceTypes has no resource_types_list field')
        if len(ResourceTypes) != len(reply.message_parameters_reference[0].resource_types_list):
            self.fail('response to getResourceTypes has incorrect number of resource types')
        for Type in reply.message_parameters_reference[0].resource_types_list:
            if Type not in ResourceTypes:
                self.fail('response to getResourceTypes has unexpected resource type [%s]'%Type)
 
    @defer.inlineCallbacks
    def test_getResourcesOfType(self):

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # create the getResourcesOfType request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS getResourcesOfType request')
        msg.message_parameters_reference = msg.CreateObject(GET_RESOURCES_OF_TYPE_REQUEST_TYPE)
        
        msg.message_parameters_reference.resource_type = "datasets"
        reply = yield self.aisc.getResourcesOfType(msg)
        log.debug('getResourcesOfType returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResourcesOfType returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCES_OF_TYPE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCES_OF_TYPE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('column_names'):
            self.fail('response to getResourcesOfType has no column_names field')
        if not reply.message_parameters_reference[0].IsFieldSet('resources'):
            self.fail('response to getResourcesOfType has no resources field')
        
        msg.message_parameters_reference.resource_type = "identities"
        reply = yield self.aisc.getResourcesOfType(msg)
        log.debug('getResourcesOfType returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResourcesOfType returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCES_OF_TYPE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCES_OF_TYPE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('column_names'):
            self.fail('response to getResourcesOfType has no column_names field')
        if not reply.message_parameters_reference[0].IsFieldSet('resources'):
            self.fail('response to getResourcesOfType has no resources field')
        
        msg.message_parameters_reference.resource_type = "datasources"
        reply = yield self.aisc.getResourcesOfType(msg)
        log.debug('getResourcesOfType returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResourcesOfType returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCES_OF_TYPE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCES_OF_TYPE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('column_names'):
            self.fail('response to getResourcesOfType has no column_names field')
        if not reply.message_parameters_reference[0].IsFieldSet('resources'):
            self.fail('response to getResourcesOfType has no resources field')
        
        msg.message_parameters_reference.resource_type = "epucontrollers"
        reply = yield self.aisc.getResourcesOfType(msg)
        log.debug('getResourcesOfType returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResourcesOfType returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCES_OF_TYPE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCES_OF_TYPE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('column_names'):
            self.fail('response to getResourcesOfType has no column_names field')
        if not reply.message_parameters_reference[0].IsFieldSet('resources'):
            self.fail('response to getResourcesOfType has no resources field')

    @defer.inlineCallbacks
    def test_getResource(self):

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # create the getResources request GPBs
        msg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE, MessageName='AIS getResource request')
        msg.message_parameters_reference = msg.CreateObject(GET_RESOURCE_REQUEST_TYPE)
        
        msg.message_parameters_reference.ooi_id = "agentservices_epu_controller"  #epu controller
        reply = yield self.aisc.getResource(msg)
        log.debug('getResource returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResource returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('resource'):
            self.fail('response to getResourcesOfType has no resource field')
        
        msg.message_parameters_reference.ooi_id = "3319A67F-81F3-424F-8E69-4F28C4E047F1"  #data set
        reply = yield self.aisc.getResource(msg)
        log.debug('getResource returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResource returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('resource'):
            self.fail('response to getResourcesOfType has no resource field')
        
        msg.message_parameters_reference.ooi_id = "A3D5D4A0-7265-4EF2-B0AD-3CE2DC7252D8"   #anonymous identity
        reply = yield self.aisc.getResource(msg)
        log.debug('getResource returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResource returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('resource'):
            self.fail('response to getResourcesOfType has no resource field')
        
        msg.message_parameters_reference.ooi_id = "3319A67F-91F3-424F-8E69-4F28C4E047F2"  #data source
        reply = yield self.aisc.getResource(msg)
        log.debug('getResource returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_MSG_TYPE:
            self.fail('response is not an AIS_RESPONSE_MSG_TYPE GPB')
        log.debug('getResource returned:\n'+str(reply.message_parameters_reference[0]))
        if reply.message_parameters_reference[0].ObjectType != GET_RESOURCE_RESPONSE_TYPE:
            self.fail('response to getResourcesOfType is not a GET_RESOURCE_RESPONSE_TYPE GPB')           
        if not reply.message_parameters_reference[0].IsFieldSet('resource'):
            self.fail('response to getResourcesOfType has no resource field')
        
        msg.message_parameters_reference.ooi_id = "bogus-ooi_id"  #non-existant item
        reply = yield self.aisc.getResource(msg)
        log.debug('getResource returned:\n'+str(reply))
        if reply.MessageType != AIS_RESPONSE_ERROR_TYPE:
            self.fail('response to bad ooi_id is not an AIS_RESPONSE_ERROR_TYPE GPB')

    @defer.inlineCallbacks
    def test_createDataResourceSubscription(self):
        log.debug('Testing createDataResourcesSubscription.')

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        #
        # Send a request without a resourceID to test that the appropriate error
        # is returned.
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(SUBSCRIBE_DATA_RESOURCE_REQ_TYPE)
        reqMsg.message_parameters_reference.subscriptionInfo.user_ooi_id  = 'Dr. Chew'
        reqMsg.message_parameters_reference.subscriptionInfo.data_src_id  = 'TestDataSourceID'
        reqMsg.message_parameters_reference.subscriptionInfo.subscription_type = reqMsg.message_parameters_reference.subscriptionInfo.SubscriptionType.EMAIL
        reqMsg.message_parameters_reference.subscriptionInfo.email_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_script_path  = '/home/test_path'
        
        log.debug('Calling createDataResourceSubscription.')
        rspMsg = yield self.aisc.createDataResourceSubscription(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail('ERROR rspMsg to createDataResourceSubscription')
        else:
            log.debug('POSITIVE rspMsg to createDataResourceSubscription')

    @defer.inlineCallbacks
    def test_findDataResourceSubscriptions(self):
        log.debug('Testing findDataResourceSubscriptions.')

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        #
        #
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_SUBSCRIPTIONS_REQ_TYPE)
        reqMsg.message_parameters_reference.user_ooi_id  = ANONYMOUS_USER_ID
        reqMsg.message_parameters_reference.dataBounds.minLatitude  = -50
        reqMsg.message_parameters_reference.dataBounds.maxLatitude  = -40
        reqMsg.message_parameters_reference.dataBounds.minLongitude = 20
        reqMsg.message_parameters_reference.dataBounds.maxLongitude = 30
        reqMsg.message_parameters_reference.dataBounds.cminVertical  = 20
        reqMsg.message_parameters_reference.dataBounds.maxVertical  = 30
        reqMsg.message_parameters_reference.dataBounds.posVertical  = 'down'
        reqMsg.message_parameters_reference.dataBounds.minTime      = '2008-08-1T10:00:00Z'
        reqMsg.message_parameters_reference.dataBounds.maxTime      = '2008-08-1T11:00:00Z'

        
        log.debug('Calling findDataResourceSubscriptions.')
        rspMsg = yield self.aisc.findDataResourceSubscriptions(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail('ERROR rspMsg to findDataResourceSubscriptions')
        else:
            log.debug('POSITIVE rspMsg to findDataResourceSubscriptions')

    @defer.inlineCallbacks
    def test_updateDataResourceSubscription(self):
        log.debug('Testing updateDataResourceSubscription.')

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # first create a subscription to be updated
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(SUBSCRIBE_DATA_RESOURCE_REQ_TYPE)
        reqMsg.message_parameters_reference.subscriptionInfo.user_ooi_id  = 'Dr. Chew'
        reqMsg.message_parameters_reference.subscriptionInfo.data_src_id  = 'TestDataSourceID'
        reqMsg.message_parameters_reference.subscriptionInfo.subscription_type = reqMsg.message_parameters_reference.subscriptionInfo.SubscriptionType.EMAIL
        reqMsg.message_parameters_reference.subscriptionInfo.email_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_script_path  = '/home/test_path'
        
        log.debug('Calling createDataResourceSubscription.')
        rspMsg = yield self.aisc.createDataResourceSubscription(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail('ERROR rspMsg to createDataResourceSubscription')
        else:
            log.debug('POSITIVE rspMsg to createDataResourceSubscription')
            
        # noow update the subscription created above
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(SUBSCRIBE_DATA_RESOURCE_REQ_TYPE)
        reqMsg.message_parameters_reference.subscriptionInfo.user_ooi_id  = 'Dr. Chew'
        reqMsg.message_parameters_reference.subscriptionInfo.data_src_id  = 'TestDataSourceID'
        reqMsg.message_parameters_reference.subscriptionInfo.subscription_type = reqMsg.message_parameters_reference.subscriptionInfo.SubscriptionType.EMAIL
        reqMsg.message_parameters_reference.subscriptionInfo.email_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_script_path  = '/home/test_path/something_added'
        
        log.debug('Calling updateDataResourceSubscription.')
        rspMsg = yield self.aisc.updateDataResourceSubscription(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail('ERROR rspMsg to updateDataResourceSubscription')
        else:
            log.debug('POSITIVE rspMsg to updateDataResourceSubscription')

    @defer.inlineCallbacks
    def test_deleteDataResourceSubscription(self):
        log.debug('Testing deleteDataResourceSubscriptions.')

        # Create a message client
        mc = MessageClient(proc=self.test_sup)
        
        # create a subscription to be deleted
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(SUBSCRIBE_DATA_RESOURCE_REQ_TYPE)
        reqMsg.message_parameters_reference.subscriptionInfo.user_ooi_id  = 'Dr. Chew'
        reqMsg.message_parameters_reference.subscriptionInfo.data_src_id  = 'TestDataSourceID'
        reqMsg.message_parameters_reference.subscriptionInfo.subscription_type = reqMsg.message_parameters_reference.subscriptionInfo.SubscriptionType.EMAIL
        reqMsg.message_parameters_reference.subscriptionInfo.email_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_script_path  = '/home/test_path'
        
        log.debug('Calling createDataResourceSubscription.')
        rspMsg = yield self.aisc.createDataResourceSubscription(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail('ERROR rspMsg to createDataResourceSubscription')
        else:
            log.debug('POSITIVE rspMsg to createDataResourceSubscription')
            
        # now delete the subscription created above
        reqMsg = yield mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(DELETE_SUBSCRIPTION_REQ_TYPE)
        reqMsg.message_parameters_reference.subscriptionInfo.user_ooi_id  = 'Dr. Chew'
        reqMsg.message_parameters_reference.subscriptionInfo.data_src_id  = 'TestDataSourceID'
        reqMsg.message_parameters_reference.subscriptionInfo.subscription_type = reqMsg.message_parameters_reference.subscriptionInfo.SubscriptionType.EMAIL
        reqMsg.message_parameters_reference.subscriptionInfo.email_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_alerts_filter  = reqMsg.message_parameters_reference.subscriptionInfo.AlertsFilter.UPDATES
        reqMsg.message_parameters_reference.subscriptionInfo.dispatcher_script_path  = '/home/test_path'

        log.debug('Calling deleteDataResourceSubscriptions.')
        rspMsg = yield self.aisc.deleteDataResourceSubscription(reqMsg)
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail('ERROR rspMsg to deleteDataResourceSubscription')
        else:
            log.debug('POSITIVE rspMsg to deleteDataResourceSubscription')

    @defer.inlineCallbacks
    def test_createDataResource_success(self):
        raise unittest.SkipTest('This will be the test for a normal successful createDataResource')

    @defer.inlineCallbacks
    def test_createDataResource_failInputs(self):
        raise unittest.SkipTest('This will be the test createDataResource when bad inputs are supplied')

    @defer.inlineCallbacks
    def test_createDataResource_failSource(self):
        raise unittest.SkipTest('This will be the test createDataResource when create source fails')
    
    @defer.inlineCallbacks
    def test_createDataResource_failSet(self):
        raise unittest.SkipTest('This will be the test createDataResource when create dataset fails')
    
    @defer.inlineCallbacks
    def test_createDataResource_failAssociation(self):
        raise unittest.SkipTest('This will be the test createDataResource when association fails')
    
    @defer.inlineCallbacks
    def test_createDataResource_failScheduling(self):
        raise unittest.SkipTest('This will be the test createDataResource when scheduling fails')
        
    def __validateDataResourceSummary(self, dataResourceSummary):
        log.debug('__validateDataResourceSummary()')
        
        i = 0
        while i < len(dataResourceSummary):
            if not dataResourceSummary[i].IsFieldSet('user_ooi_id'):
                self.fail('response to findDataResources has no user_ooi_id field')
            if not dataResourceSummary[i].IsFieldSet('data_resource_id'):
                self.fail('response to findDataResources has no resource_id field')
            if not dataResourceSummary[i].IsFieldSet('title'):
                #self.fail('response to findDataResources has no title field')
                log.error('response to findDataResources has no title field')
            if not dataResourceSummary[i].IsFieldSet('institution'):
                #self.fail('response to findDataResources has no institution field')
                log.error('response to findDataResources has no institution field')
            if not dataResourceSummary[i].IsFieldSet('source'):
                #self.fail('response to findDataResources has no source field')
                log.error('response to findDataResources has no source field')
            if not dataResourceSummary[i].IsFieldSet('references'):
                #self.fail('response to findDataResources has no references field')
                log.error('response to findDataResources has no references field')
            if not dataResourceSummary[i].IsFieldSet('ion_time_coverage_start'):
                self.fail('response to findDataResources has no ion_time_coverage_start field')
            if not dataResourceSummary[i].IsFieldSet('ion_time_coverage_end'):
                self.fail('response to findDataResources has no ion_time_coverage_end field')
            if not dataResourceSummary[i].IsFieldSet('summary'):
                #self.fail('response to findDataResources has no summary field')
                log.error('response to findDataResources has no summary field')
            if not dataResourceSummary[i].IsFieldSet('comment'):
                #self.fail('response to findDataResources has no comment field')
                log.error('response to findDataResources has no comment field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_lat_min'):
                self.fail('response to findDataResources has no ion_geospatial_lat_min field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_lat_max'):
                self.fail('response to findDataResources has no ion_geospatial_lat_max field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_lon_min'):
                self.fail('response to findDataResources has no ion_geospatial_lon_min field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_lon_max'):
                self.fail('response to findDataResources has no ion_geospatial_lon_max field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_vertical_min'):
                self.fail('response to findDataResources has no ion_geospatial_vertical_min field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_vertical_max'):
                self.fail('response to findDataResources has no ion_geospatial_vertical_max field')
            if not dataResourceSummary[i].IsFieldSet('ion_geospatial_vertical_positive'):
                self.fail('response to findDataResources has no ion_geospatial_vertical_positive field')
            if not dataResourceSummary[i].IsFieldSet('download_url'):
                self.fail('response to findDataResources has no download_url field')
            i = i + 1                



