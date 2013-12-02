import time

from unittest import TestCase
from mock import Mock, MagicMock, patch

from ..ad2 import AD2Factory, AD2
from ..devices import USBDevice
from ..messages import Message, RFMessage, LRRMessage, ExpanderMessage
from ..event.event import Event, EventHandler
from ..zonetracking import Zonetracker

class TestAD2Factory(TestCase):
    def setUp(self):
        self._attached = False
        self._detached = False

        with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2', 1, 'AD2')]):
            self._factory = AD2Factory()

    def tearDown(self):
        self._factory.stop()

    def attached_event(self, sender, args):
        self._attached = True

    def detached_event(self, sender, args):
        self._detached = True

    def test_find_all(self):
        with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2', 1, 'AD2')]):
            devices = AD2Factory.find_all()

            self.assertEquals(devices[0][2], 'AD2')

    def test_create_default_param(self):
        with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2', 1, 'AD2')]):
            device = AD2Factory.create()

            self.assertEquals(device._device.interface, ('AD2', 0))

    def test_create_with_param(self):
        with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2-1', 1, 'AD2'), (0, 0, 'AD2-2', 1, 'AD2')]):
            device = AD2Factory.create((0, 0, 'AD2-1', 1, 'AD2'))
            self.assertEquals(device._device.interface, ('AD2-1', 0))

            device = AD2Factory.create((0, 0, 'AD2-2', 1, 'AD2'))
            self.assertEquals(device._device.interface, ('AD2-2', 0))

    def test_events(self):
        self.assertEquals(self._attached, False)
        self.assertEquals(self._detached, False)

        # this is ugly, but it works.
        self._factory.stop()
        self._factory._detect_thread = AD2Factory.DetectThread(self._factory)
        self._factory.on_attached += self.attached_event
        self._factory.on_detached += self.detached_event

        with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2-1', 1, 'AD2'), (0, 0, 'AD2-2', 1, 'AD2')]):
            self._factory.start()

            with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2-2', 1, 'AD2')]):
                AD2Factory.find_all()
                time.sleep(1)
                self._factory.stop()

        self.assertEquals(self._attached, True)
        self.assertEquals(self._detached, True)

class TestAD2(TestCase):
    def setUp(self):
        self._panicked = False
        self._relay_changed = False
        self._power_changed = False
        self._alarmed = False
        self._bypassed = False
        self._battery = (False, 0)
        self._fire = (False, 0)
        self._armed = False
        self._got_config = False
        self._message_received = False
        self._rfx_message_received = False
        self._lrr_message_received = False

        self._device = Mock(spec=USBDevice)
        self._device.on_open = EventHandler(Event(), self._device)
        self._device.on_close = EventHandler(Event(), self._device)
        self._device.on_read = EventHandler(Event(), self._device)
        self._device.on_write = EventHandler(Event(), self._device)

        self._ad2 = AD2(self._device)

        self._ad2._zonetracker = Mock(spec=Zonetracker)
        self._ad2._zonetracker.on_fault = EventHandler(Event(), self._ad2._zonetracker)
        self._ad2._zonetracker.on_restore = EventHandler(Event(), self._ad2._zonetracker)

        self._ad2.on_panic += self.on_panic
        self._ad2.on_relay_changed += self.on_relay_changed
        self._ad2.on_power_changed += self.on_power_changed
        self._ad2.on_alarm += self.on_alarm
        self._ad2.on_bypass += self.on_bypass
        self._ad2.on_low_battery += self.on_battery
        self._ad2.on_fire += self.on_fire
        self._ad2.on_arm += self.on_arm
        self._ad2.on_disarm += self.on_disarm
        self._ad2.on_config_received += self.on_config
        self._ad2.on_message += self.on_message
        self._ad2.on_rfx_message += self.on_rfx_message
        self._ad2.on_lrr_message += self.on_lrr_message

        self._ad2.address_mask = int('ffffffff', 16)
        self._ad2.open()

    def tearDown(self):
        pass

    def on_panic(self, sender, args):
        self._panicked = args

    def on_relay_changed(self, sender, args):
        self._relay_changed = True

    def on_power_changed(self, sender, args):
        self._power_changed = args

    def on_alarm(self, sender, args):
        self._alarmed = args

    def on_bypass(self, sender, args):
        self._bypassed = args

    def on_battery(self, sender, args):
        self._battery = args

    def on_fire(self, sender, args):
        self._fire = args

    def on_arm(self, sender, args):
        self._armed = True

    def on_disarm(self, sender, args):
        self._armed = False

    def on_config(self, sender, args):
        self._got_config = True

    def on_message(self, sender, args):
        self._message_received = True

    def on_rfx_message(self, sender, args):
        self._rfx_message_received = True

    def on_lrr_message(self, sender, args):
        self._lrr_message_received = True

    def test_open(self):
        self._ad2.open()
        self._device.open.assert_any_calls()

    def test_close(self):
        self._ad2.open()

        self._ad2.close()
        self._device.close.assert_any_calls()

    def test_send(self):
        self._ad2.send('test')
        self._device.write.assert_called_with('test')

    def test_get_config(self):
        self._ad2.get_config()
        self._device.write.assert_called_with("C\r")

    def test_save_config(self):
        self._ad2.save_config()
        self._device.write.assert_any_calls()

    def test_reboot(self):
        self._ad2.reboot()
        self._device.write.assert_called_with('=')

    def test_fault(self):
        self._ad2.fault_zone(1)
        self._device.write.assert_called_with("L{0:02}{1}\r".format(1, 1))

    def test_fault_wireproblem(self):
        self._ad2.fault_zone(1, simulate_wire_problem=True)
        self._device.write.assert_called_with("L{0:02}{1}\r".format(1, 2))

    def test_clear_zone(self):
        self._ad2.clear_zone(1)
        self._device.write.assert_called_with("L{0:02}0\r".format(1))

    def test_message(self):
        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertIsInstance(msg, Message)

        self._ad2._on_read(self, '[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertTrue(self._message_received)

    def test_message_kpe(self):
        msg = self._ad2._handle_message('!KPE:[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertIsInstance(msg, Message)

        self._ad2._on_read(self, '[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertTrue(self._message_received)

    def test_expander_message(self):
        msg = self._ad2._handle_message('!EXP:07,01,01')
        self.assertIsInstance(msg, ExpanderMessage)

    def test_relay_message(self):
        self._ad2.open()
        msg = self._ad2._handle_message('!REL:12,01,01')
        self.assertIsInstance(msg, ExpanderMessage)
        self.assertEquals(self._relay_changed, True)

    def test_rfx_message(self):
        msg = self._ad2._handle_message('!RFX:0180036,80')
        self.assertIsInstance(msg, RFMessage)
        self.assertTrue(self._rfx_message_received)

    def test_panic(self):
        self._ad2.open()

        msg = self._ad2._handle_message('!LRR:012,1,ALARM_PANIC')
        self.assertEquals(self._panicked, True)

        msg = self._ad2._handle_message('!LRR:012,1,CANCEL')
        self.assertEquals(self._panicked, False)
        self.assertIsInstance(msg, LRRMessage)

    def test_config_message(self):
        self._ad2.open()

        msg = self._ad2._handle_message('!CONFIG>ADDRESS=18&CONFIGBITS=ff00&LRR=N&EXP=NNNNN&REL=NNNN&MASK=ffffffff&DEDUPLICATE=N')
        self.assertEquals(self._ad2.address, 18)
        self.assertEquals(self._ad2.configbits, int('ff00', 16))
        self.assertEquals(self._ad2.address_mask, int('ffffffff', 16))
        self.assertEquals(self._ad2.emulate_zone, [False for x in range(5)])
        self.assertEquals(self._ad2.emulate_relay, [False for x in range(4)])
        self.assertEquals(self._ad2.emulate_lrr, False)
        self.assertEquals(self._ad2.deduplicate, False)

        self.assertEquals(self._got_config, True)

    def test_power_changed_event(self):
        msg = self._ad2._handle_message('[0000000100000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._power_changed, False)   # Not set first time we hit it.

        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._power_changed, False)

        msg = self._ad2._handle_message('[0000000100000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._power_changed, True)

    def test_alarm_event(self):
        msg = self._ad2._handle_message('[0000000000100000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._alarmed, False)   # Not set first time we hit it.

        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._alarmed, False)

        msg = self._ad2._handle_message('[0000000000100000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._alarmed, True)

    def test_zone_bypassed_event(self):
        msg = self._ad2._handle_message('[0000001000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._bypassed, False)   # Not set first time we hit it.

        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._bypassed, False)

        msg = self._ad2._handle_message('[0000001000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._bypassed, True)

    def test_armed_away_event(self):
        msg = self._ad2._handle_message('[0100000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)   # Not set first time we hit it.

        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)

        msg = self._ad2._handle_message('[0100000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, True)

        self._armed = False

        msg = self._ad2._handle_message('[0010000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)   # Not set first time we hit it.

        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)

        msg = self._ad2._handle_message('[0010000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, True)

    def test_battery_low_event(self):
        msg = self._ad2._handle_message('[0000000000010000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._battery[0], True)

        # force the timeout to expire.
        with patch.object(time, 'time', return_value=self._battery[1] + 35):
            msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
            self.assertEquals(self._battery[0], False)

    def test_fire_alarm_event(self):
        msg = self._ad2._handle_message('[0000000000000100----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._fire[0], True)

        # force the timeout to expire.
        with patch.object(time, 'time', return_value=self._fire[1] + 35):
            msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
            self.assertEquals(self._fire[0], False)

    def test_hit_for_faults(self):
        self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"Hit * for faults                "')

        self._ad2._device.write.assert_called_with('*')

    def test_zonetracker_update(self):
        msg = self._ad2._handle_message('[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self._ad2._zonetracker.update.assert_called_with(msg)
