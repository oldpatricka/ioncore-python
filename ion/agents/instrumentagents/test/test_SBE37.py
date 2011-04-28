#!/usr/bin/env python
"""
@file ion/agents/instrumentagents/test/test_SBE37.py
@brief Test cases for the SBE37 driver.
@author Edward Hunter
"""

import re
import os

from twisted.internet import defer
from twisted.trial import unittest

import ion.util.ionlog
import ion.util.procutils as pu
from ion.test.iontest import IonTestCase
from ion.agents.instrumentagents.SBE37_driver import SBE37DriverClient
from ion.agents.instrumentagents.simulators.sim_SBE49 import Simulator
from ion.agents.instrumentagents.SBE37_driver import DriverException


log = ion.util.ionlog.getLogger(__name__)


def dump_dict(d,d2=None):
    print
    for (key,val) in d.iteritems():
        if d2:
            print key, ' ', val, ' ',d2.get(key,None)            
        else:
            print key, ' ', val


"""
List of mac addresses for machines which should run these tests. If no
mac address of a NIC on the machine running the tests matches one in this
list, the tests are skipped. This is to prevent the trial robot from
commanding the instrument hardware, forcing these tests to be run
intentionally. Add the mac address of your development machine as
returned by ifconfig to cause the tests to run for you locally.
"""

allowed_mac_addr_list = [
    '00:26:bb:19:83:33'         # Edward's Macbook
    ]

mac_addr_pattern = r'\b\w\w[:\-]\w\w[:\-]\w\w[:\-]\w\w[:\-]\w\w[:\-]\w\w\b'
mac_addr_re = re.compile(mac_addr_pattern,re.MULTILINE)
mac_addr_list = mac_addr_re.findall(os.popen('ifconfig').read())
RUN_TESTS = any([addr in allowed_mac_addr_list for addr in mac_addr_list])


# It is useful to be able to easily turn tests on and off
# during development. Also this will ensure tests do not run
# automatically. 
SKIP_TESTS = [
    'test_configure',
    'test_connect',
    'test_get_set',
    'test_execute',
    'dummy'
]


class TestSBE37(IonTestCase):
    
    # Increase the timeout so we can handle longer instrument interactions.
    timeout = 120
    
    # The instrument ID.
    instrument_id = '123'
    
    # Instrument and simulator configuration.
    
    simulator_port = 9000
    simulator_host = 'localhost'
    
    sbe_host = '137.110.112.119'
    sbe_port = 4001
    
    simulator_config = {
        'ipport':simulator_port, 
        'ipaddr':simulator_host
    }
    
    sbe_config = {
        'ipport':sbe_port, 
        'ipaddr':sbe_host
    }

    
    
    @defer.inlineCallbacks
    def setUp(self):
                

        yield self._start_container()
        
        self.simulator = Simulator(self.instrument_id,self.simulator_port)        
        simulator_ports = self.simulator.start()
        simulator_port = simulator_ports[0]
        self.assertNotEqual(simulator_port,0)
        if simulator_port != self.simulator_port:
            self.simulator_port = simulator_port
            
        
        services = [
            {'name':'SBE37_driver',
             'module':'ion.agents.instrumentagents.SBE37_driver',
             'class':'SBE37Driver',
             'spawnargs':{}}
            ]


        self.sup = yield self._spawn_processes(services)

        self.driver_pid = yield self.sup.get_child_id('SBE37_driver')

        self.driver_client = SBE37DriverClient(proc=self.sup,
                                               target=self.driver_pid)



    @defer.inlineCallbacks
    def tearDown(self):
        
        
        yield self.simulator.stop()        
        yield self._stop_container()



    @defer.inlineCallbacks
    def test_configure(self):
        """
        Test driver configure functions.
        """
        if not RUN_TESTS:
            raise unittest.SkipTest("Do not run this test automatically.")
        
        if 'test_configure' in SKIP_TESTS:
            raise unittest.SkipTest('Skipping during development.')

        params = self.sbe_config

        # We should begin in the unconfigured state.
        current_state = yield self.driver_client.get_state()
        self.assertEqual(current_state,'STATE_UNCONFIGURED')

        # Configure the driver and verify.
        reply = yield self.driver_client.configure(params)        
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
                
        self.assertEqual(success[0],'OK')
        self.assertEqual(result,params)
        self.assertEqual(current_state,'STATE_DISCONNECTED')


    
    @defer.inlineCallbacks
    def test_connect(self):
        """
        Test driver connect to device.
        """
        
        if not RUN_TESTS:
            raise unittest.SkipTest("Do not run this test automatically.")
        
        if 'test_connect' in SKIP_TESTS:
            raise unittest.SkipTest('Skipping during development.')

        params = self.sbe_config

        # We should begin in the unconfigured state.
        current_state = yield self.driver_client.get_state()
        self.assertEqual(current_state,'STATE_UNCONFIGURED')

        # Configure the driver and verify.
        reply = yield self.driver_client.configure(params)        
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'OK')
        self.assertEqual(result,params)
        self.assertEqual(current_state,'STATE_DISCONNECTED')


        # Establish connection to device and verify.
        try:
            reply = yield self.driver_client.connect()
        except:
            self.fail('Could not connect to the device.')
            
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_CONNECTED')

        
        # Dissolve the connection to the device.
        reply = yield self.driver_client.disconnect()
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_DISCONNECTED')

        
        
    @defer.inlineCallbacks
    def test_get_set(self):
        """
        Test driver get/set functions. 
        """

        if not RUN_TESTS:
            raise unittest.SkipTest("Do not run this test automatically.")
        
        if 'test_get_set' in SKIP_TESTS:
            raise unittest.SkipTest('Skipping during development.')


        params = self.sbe_config

        # We should begin in the unconfigured state.
        current_state = yield self.driver_client.get_state()
        self.assertEqual(current_state,'STATE_UNCONFIGURED')

        # Configure the driver and verify.
        reply = yield self.driver_client.configure(params)        
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        
        self.assertEqual(success[0],'OK')
        self.assertEqual(result,params)
        self.assertEqual(current_state,'STATE_DISCONNECTED')


        # Establish connection to device. This starts a loop of
        # wakeups to the device handled when the prompt returns.
        try:
            reply = yield self.driver_client.connect()
        except:
            self.fail('Could not connect to the device.')
        
        
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_CONNECTED')


        # Get all parameters and verify. Store the current config for later.
        params = [('all','all')]

        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        config = result
        config = dict(map(lambda x: (x[0],x[1][1]),config.items()))
      
        
        self.assertEqual(success[0],'OK')
        self.assertEqual(all(map(lambda x: x[1] != None,result.values())),True)
        self.assertEqual(current_state,'STATE_CONNECTED')

        
        # Get all pressure parameters and verify.        
        params = [('CHAN_PRESSURE','all')]

        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
                
        pressure_params = [
            ('CHAN_PRESSURE','PCALDATE'),
            ('CHAN_PRESSURE','PA0'),
            ('CHAN_PRESSURE','PA1'),
            ('CHAN_PRESSURE','PA2'),
            ('CHAN_PRESSURE','PTCA0'),
            ('CHAN_PRESSURE','PTCA1'),
            ('CHAN_PRESSURE','PTCA2'),
            ('CHAN_PRESSURE','PTCB0'),
            ('CHAN_PRESSURE','PTCB1'),
            ('CHAN_PRESSURE','PTCB2'),
            ('CHAN_PRESSURE','POFFSET')            
            ]
                
                
        self.assertEqual(success[0],'OK')
        self.assertEqual(pressure_params.sort(),result.keys().sort())
        self.assertEqual(all(map(lambda x: x[1] != None ,result.values())),True)
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        
        # Get a few parameters by name and verify.
        params = [
            ('CHAN_INSTRUMENT','NAVG'),
            ('CHAN_INSTRUMENT','INTERVAL'),
            ('CHAN_INSTRUMENT','OUTPUTSV'),
            ('CHAN_TEMPERATURE','TA0'),
            ('CHAN_CONDUCTIVITY','WBOTC')
            ]

        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'OK')
        self.assertEqual(params.sort(),result.keys().sort())
        self.assertEqual(all(map(lambda x: x[1] != None ,result.values())),True)
        self.assertEqual(current_state,'STATE_CONNECTED')
                        
                
        # Set a few parameters and verify.
        orig_params = {
            ('CHAN_INSTRUMENT','NAVG'):config[('CHAN_INSTRUMENT','NAVG')],
            ('CHAN_INSTRUMENT','INTERVAL'):config[('CHAN_INSTRUMENT','INTERVAL')],
            ('CHAN_INSTRUMENT','OUTPUTSV'):config[('CHAN_INSTRUMENT','OUTPUTSV')],
            ('CHAN_TEMPERATURE','TA0'):config[('CHAN_TEMPERATURE','TA0')],
            ('CHAN_CONDUCTIVITY','WBOTC'):config[('CHAN_CONDUCTIVITY','WBOTC')]            
        }
        new_params = {}
        new_params[('CHAN_INSTRUMENT','NAVG')] = orig_params[('CHAN_INSTRUMENT','NAVG')] + 1
        new_params[('CHAN_INSTRUMENT','INTERVAL')] = orig_params[('CHAN_INSTRUMENT','INTERVAL')] + 1
        new_params[('CHAN_INSTRUMENT','OUTPUTSV')] = not orig_params[('CHAN_INSTRUMENT','OUTPUTSV')]
        new_params[('CHAN_TEMPERATURE','TA0')] = 2*float(orig_params[('CHAN_TEMPERATURE','TA0')])
        new_params[('CHAN_CONDUCTIVITY','WBOTC')] = 2*float(orig_params[('CHAN_CONDUCTIVITY','WBOTC')])
        
        
        reply = yield self.driver_client.set(new_params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(new_params.keys().sort(),result.keys().sort())
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        # Get all parameters, verify the changes were made.        
        params = [('all','all')]

        reply = yield self.driver_client.get(params)
        get_current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertAlmostEqual(result[('CHAN_CONDUCTIVITY','WBOTC')][1],new_params[('CHAN_CONDUCTIVITY','WBOTC')],4)
        self.assertAlmostEqual(result[('CHAN_TEMPERATURE','TA0')][1],new_params[('CHAN_TEMPERATURE','TA0')],4)
        self.assertEqual(result[('CHAN_INSTRUMENT','NAVG')][1],new_params[('CHAN_INSTRUMENT','NAVG')])
        self.assertEqual(result[('CHAN_INSTRUMENT','INTERVAL')][1],new_params[('CHAN_INSTRUMENT','INTERVAL')])
        self.assertEqual(result[('CHAN_INSTRUMENT','OUTPUTSV')][1],new_params[('CHAN_INSTRUMENT','OUTPUTSV')])
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        # Restore original state.         
        reply = yield self.driver_client.set(orig_params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(orig_params.keys().sort(),result.keys().sort())
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        # Get parameters and make sure they match the original config.
        params = [('all','all')]

        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'OK')
        self.assertAlmostEqual(result[('CHAN_CONDUCTIVITY','WBOTC')][1],config[('CHAN_CONDUCTIVITY','WBOTC')],4)
        self.assertAlmostEqual(result[('CHAN_TEMPERATURE','TA0')][1],config[('CHAN_TEMPERATURE','TA0')],4)
        self.assertEqual(result[('CHAN_INSTRUMENT','NAVG')][1],config[('CHAN_INSTRUMENT','NAVG')])
        self.assertEqual(result[('CHAN_INSTRUMENT','INTERVAL')][1],config[('CHAN_INSTRUMENT','INTERVAL')])
        self.assertEqual(result[('CHAN_INSTRUMENT','OUTPUTSV')][1],config[('CHAN_INSTRUMENT','OUTPUTSV')])
        self.assertEqual(current_state,'STATE_CONNECTED')
        
                
        # Try getting bad parameters.This should fail for bad parameters but
        # succeed for the good ones.
        params = [
            ('I am a bad channel name','NAVG'),
            ('CHAN_INSTRUMENT','INTERVAL'),
            ('CHAN_INSTRUMENT','I am a bad parameter name'),
            ('CHAN_TEMPERATURE','TA0'),
            ('CHAN_CONDUCTIVITY','WBOTC')
            ]
        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'ERROR')
        self.assertEqual(result[('I am a bad channel name','NAVG')][0][0],'ERROR')
        self.assertEqual(result[('I am a bad channel name','NAVG')][1],None)
        self.assertEqual(result[('CHAN_INSTRUMENT','INTERVAL')][0][0],'OK')
        self.assertIsInstance(result[('CHAN_INSTRUMENT','INTERVAL')][1],int)
        self.assertEqual(result[('CHAN_INSTRUMENT','I am a bad parameter name')][0][0],'ERROR')
        self.assertEqual(result[('CHAN_INSTRUMENT','I am a bad parameter name')][1],None)
        self.assertEqual(result[('CHAN_TEMPERATURE','TA0')][0][0],'OK')
        self.assertIsInstance(result[('CHAN_TEMPERATURE','TA0')][1],float)
        self.assertEqual(result[('CHAN_CONDUCTIVITY','WBOTC')][0][0],'OK')
        self.assertIsInstance(result[('CHAN_CONDUCTIVITY','WBOTC')][1],float)
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        
        # Try setting bad parameters. This should fail for bad parameters but succeed for
        # valid ones.
        bad_params = new_params
        bad_params[('I am a bad channel','NAVG')] = bad_params[('CHAN_INSTRUMENT','NAVG')]
        del bad_params[('CHAN_INSTRUMENT','NAVG')]
        bad_params[('CHAN_TEMPERATURE','I am a bad parameter')] = bad_params[('CHAN_TEMPERATURE','TA0')]
        del bad_params[('CHAN_TEMPERATURE','TA0')]
        
        reply = yield self.driver_client.set(bad_params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'ERROR')
        self.assertEqual(result[('I am a bad channel','NAVG')][0],'ERROR')
        self.assertEqual(result[('CHAN_INSTRUMENT','INTERVAL')][0],'OK')
        self.assertEqual(result[('CHAN_INSTRUMENT','OUTPUTSV')][0],'OK')
        self.assertEqual(result[('CHAN_TEMPERATURE','I am a bad parameter')][0],'ERROR')
        self.assertEqual(result[('CHAN_CONDUCTIVITY','WBOTC')][0],'OK')

        # Get all parameters, verify the valid ones were set, and the invalid ones kept the
        # old values.
        params = [('all','all')]
        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result[('CHAN_INSTRUMENT','INTERVAL')][1],new_params[('CHAN_INSTRUMENT','INTERVAL')])
        self.assertEqual(result[('CHAN_INSTRUMENT','OUTPUTSV')][1],new_params[('CHAN_INSTRUMENT','OUTPUTSV')])
        self.assertAlmostEqual(result[('CHAN_CONDUCTIVITY','WBOTC')][1],new_params[('CHAN_CONDUCTIVITY','WBOTC')],4)
        self.assertEqual(result[('CHAN_INSTRUMENT','NAVG')][1],orig_params[('CHAN_INSTRUMENT','NAVG')])
        self.assertAlmostEqual(result[('CHAN_TEMPERATURE','TA0')][1],orig_params[('CHAN_TEMPERATURE','TA0')],4)
        self.assertEqual(current_state,'STATE_CONNECTED')

        # Restore the original configuration and verify.
        # This should set all the parameters in the driver.
        # In addition to restoring original, it tests that each parameter can be set.
        
        
        reply = yield self.driver_client.set(config) 
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'OK')
        self.assertEqual(config.keys().sort(),result.keys().sort())
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        
        # Dissolve the connection to the device.
        reply = yield self.driver_client.disconnect()
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_DISCONNECTED')

    
    
    @defer.inlineCallbacks
    def test_execute(self):
        """
        Test driver execute functions.
        """

        if not RUN_TESTS:
            raise unittest.SkipTest("Do not run this test automatically.")
        
        if 'test_execute' in SKIP_TESTS:
            raise unittest.SkipTest('Skipping during development.')

        params = self.sbe_config

        # We should begin in the unconfigured state.
        current_state = yield self.driver_client.get_state()
        self.assertEqual(current_state,'STATE_UNCONFIGURED')

        # Configure the driver and verify.
        reply = yield self.driver_client.configure(params)        
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'OK')
        self.assertEqual(result,params)
        self.assertEqual(current_state,'STATE_DISCONNECTED')


        # Establish connection to device and verify.
        try:
            reply = yield self.driver_client.connect()
        except:
            self.fail('Could not connect to the device.')
            
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_CONNECTED')

        # Make sure the parameters are in a reasonable state for sampling.
        # Set a few parameters and verify.
        params = {}
        params[('CHAN_INSTRUMENT','NAVG')] = 1
        params[('CHAN_INSTRUMENT','INTERVAL')] = 5
        params[('CHAN_INSTRUMENT','OUTPUTSV')] = True
        params[('CHAN_INSTRUMENT','OUTPUTSAL')] = True
        params[('CHAN_INSTRUMENT','TXREALTIME')] = True
        params[('CHAN_INSTRUMENT','STORETIME')] = True
        
        reply = yield self.driver_client.set(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(current_state,'STATE_CONNECTED')        

        # Get all the parameters and dump them to the screen if desired.
        params = [('all','all')]
        reply = yield self.driver_client.get(params)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(current_state,'STATE_CONNECTED')        

        # Comment this out for automated testing.
        # It is useful to examine the instrument parameters during
        # interactive testing.
        dump_dict(result)

        # Acquire a polled sample and verify result.
        channels = ['CHAN_INSTRUMENT']
        command = ['DRIVER_CMD_ACQUIRE_SAMPLE']
        timeout = 10
        reply = yield self.driver_client.execute(channels,command,timeout)
            
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        
        self.assertEqual(success[0],'OK')
        self.assertIsInstance(result.get('temperature',None),float)
        self.assertIsInstance(result.get('salinity',None),float)
        self.assertIsInstance(result.get('pressure',None),float)
        self.assertIsInstance(result.get('sound velocity',None),float)
        self.assertIsInstance(result.get('conductivity',None),float)
        self.assertIsInstance(result.get('time',None),tuple)
        self.assertIsInstance(result.get('date',None),tuple)
        self.assertEqual(current_state,'STATE_CONNECTED')
        
        
        # Test and verify autosample mode.
        channels = ['CHAN_INSTRUMENT']
        command = ['DRIVER_CMD_START_AUTO_SAMPLING']
        timeout = 10
        reply = yield self.driver_client.execute(channels,command,timeout)
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')

        # Wait for a few samples to arrive.
        yield pu.asleep(30)

        # Test and verify autosample exit and check sample data.
        channels = ['CHAN_INSTRUMENT']
        command = ['DRIVER_CMD_STOP_AUTO_SAMPLING','GETDATA']
        timeout = 10
        
        # If a timeout occurs in stop, reattempt until the test times out.
        # Note: if this times out the instrument will be stuck in autosample
        # mode and require manual reset.
        while True:
  
            reply = yield self.driver_client.execute(channels,command,timeout)
            current_state = yield self.driver_client.get_state()
            success = reply['success']
            result = reply['result']
            
            if success[0] == 'OK':
                # The command succeeded.
                break
                            
            elif success[1] == 'TIMEOUT':
                # The driver command timed out, try again.
                pass
            
            else:
                # Some other error occurred.
                self.fail('DRIVER_CMD_STOP_AUTO_SAMPLING failed with error:'+str(success))

        # We succeeded in completing the stop. Verify the samples recovered.
        self.assertEqual(success[0],'OK')
        for sample in result:
            self.assertIsInstance(sample.get('temperature'),float)
            self.assertIsInstance(sample.get('salinity'),float)
            self.assertIsInstance(sample.get('pressure',None),float)
            self.assertIsInstance(sample.get('sound velocity',None),float)
            self.assertIsInstance(sample.get('conductivity',None),float)
            self.assertIsInstance(sample.get('time',None),tuple)
            self.assertIsInstance(sample.get('date',None),tuple)
        self.assertEqual(current_state,'STATE_CONNECTED')
        

        # Dissolve the connection to the device.
        reply = yield self.driver_client.disconnect()
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_DISCONNECTED')
        
        
        
    """
    The following is for experimenting with error callbacks only and not
    intended as part of the unit test regime.
    @defer.inlineCallbacks
    def test_errors(self):

        #if not RUN_TESTS:
        #    raise unittest.SkipTest("Do not run this test automatically.")
        raise unittest.SkipTest("Do not run this test automatically.")


        params = self.sbe_config

        # We should begin in the unconfigured state.
        current_state = yield self.driver_client.get_state()
        self.assertEqual(current_state,'STATE_UNCONFIGURED')

        # Configure the driver and verify.
        reply = yield self.driver_client.configure(params)        
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']
        
        self.assertEqual(success[0],'OK')
        self.assertEqual(result,params)
        self.assertEqual(current_state,'STATE_DISCONNECTED')


        # Establish connection to device and verify.
        try:
            reply = yield self.driver_client.connect()
        except:
            self.fail('Could not connect to the device.')
            
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_CONNECTED')


        params = {
            'command':['DRIVER_CMD_TEST_ERRORS'],
            'channels':['CHAN_INSTRUMENT']
                }
        
        try:
            reply = yield self.driver_client.execute(params)
        except Exception, e:
            print '***exception'
            print e
            print '***type'
            print type(e)
            print '***dir'
            print dir(e)
            print '***message'
            print e.message
            print '***content'
            print e.msg_content
        else:
            print reply

        
        # Dissolve the connection to the device.
        reply = yield self.driver_client.disconnect()
        current_state = yield self.driver_client.get_state()
        success = reply['success']
        result = reply['result']

        self.assertEqual(success[0],'OK')
        self.assertEqual(result,None)
        self.assertEqual(current_state,'STATE_DISCONNECTED')
    """


