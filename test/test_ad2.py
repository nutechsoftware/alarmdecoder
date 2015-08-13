import time

from builtins import bytes

from unittest import TestCase
from mock import Mock, MagicMock, patch

from alarmdecoder.decoder import AlarmDecoder
from alarmdecoder.devices import USBDevice
from alarmdecoder.messages import Message, RFMessage, LRRMessage, ExpanderMessage
from alarmdecoder.event.event import Event, EventHandler
from alarmdecoder.zonetracking import Zonetracker


class TestAlarmDecoder(TestCase):
    def setUp(self):
        self._panicked = False
        self._relay_changed = False
        self._power_changed = False
        self._alarmed = False
        self._bypassed = False
        self._battery = False
        self._fire = False
        self._armed = False
        self._got_config = False
        self._message_received = False
        self._rfx_message_received = False
        self._lrr_message_received = False
        self._expander_message_received = False
        self._sending_received_status = None
        self._alarm_restored = False
        self._on_boot_received = False
        self._zone_faulted = None
        self._zone_restored = None

        self._device = Mock(spec=USBDevice)
        self._device.on_open = EventHandler(Event(), self._device)
        self._device.on_close = EventHandler(Event(), self._device)
        self._device.on_read = EventHandler(Event(), self._device)
        self._device.on_write = EventHandler(Event(), self._device)

        self._decoder = AlarmDecoder(self._device)
        self._decoder.on_panic += self.on_panic
        self._decoder.on_relay_changed += self.on_relay_changed
        self._decoder.on_power_changed += self.on_power_changed
        self._decoder.on_alarm += self.on_alarm
        self._decoder.on_alarm_restored += self.on_alarm_restored
        self._decoder.on_bypass += self.on_bypass
        self._decoder.on_low_battery += self.on_battery
        self._decoder.on_fire += self.on_fire
        self._decoder.on_arm += self.on_arm
        self._decoder.on_disarm += self.on_disarm
        self._decoder.on_config_received += self.on_config
        self._decoder.on_message += self.on_message
        self._decoder.on_rfx_message += self.on_rfx_message
        self._decoder.on_lrr_message += self.on_lrr_message
        self._decoder.on_expander_message += self.on_expander_message
        self._decoder.on_sending_received += self.on_sending_received
        self._decoder.on_boot += self.on_boot
        self._decoder.on_zone_fault += self.on_zone_fault
        self._decoder.on_zone_restore += self.on_zone_restore

        self._decoder.address_mask = int('ffffffff', 16)
        self._decoder.open()

    def tearDown(self):
        pass

    def on_panic(self, sender, *args, **kwargs):
        self._panicked = kwargs['status']

    def on_relay_changed(self, sender, *args, **kwargs):
        self._relay_changed = True

    def on_power_changed(self, sender, *args, **kwargs):
        self._power_changed = kwargs['status']

    def on_alarm(self, sender, *args, **kwargs):
        self._alarmed = True

    def on_alarm_restored(self, sender, *args, **kwargs):
        self._alarm_restored = True

    def on_bypass(self, sender, *args, **kwargs):
        self._bypassed = kwargs['status']

    def on_battery(self, sender, *args, **kwargs):
        self._battery = kwargs['status']

    def on_fire(self, sender, *args, **kwargs):
        self._fire = kwargs['status']

    def on_arm(self, sender, *args, **kwargs):
        self._armed = True

    def on_disarm(self, sender, *args, **kwargs):
        self._armed = False

    def on_config(self, sender, *args, **kwargs):
        self._got_config = True

    def on_message(self, sender, *args, **kwargs):
        self._message_received = True

    def on_rfx_message(self, sender, *args, **kwargs):
        self._rfx_message_received = True

    def on_lrr_message(self, sender, *args, **kwargs):
        self._lrr_message_received = True

    def on_expander_message(self, sender, *args, **kwargs):
        self._expander_message_received = True

    def on_sending_received(self, sender, *args, **kwargs):
        self._sending_received_status = kwargs['status']

    def on_boot(self, sender, *args, **kwargs):
        self._on_boot_received = True

    def on_zone_fault(self, sender, *args, **kwargs):
        self._zone_faulted = kwargs['zone']

    def on_zone_restore(self, sender, *args, **kwargs):
        self._zone_restored = kwargs['zone']

    def test_open(self):
        self._decoder.open()
        self._device.open.assert_any_calls()

    def test_close(self):
        self._decoder.open()

        self._decoder.close()
        self._device.close.assert_any_calls()

    def test_send(self):
        self._decoder.send('test')
        self._device.write.assert_called_with(b'test')

    def test_get_config(self):
        self._decoder.get_config()
        self._device.write.assert_called_with(b"C\r")

    def test_save_config(self):
        self._decoder.save_config()
        self._device.write.assert_any_calls()

    def test_reboot(self):
        self._decoder.reboot()
        self._device.write.assert_called_with(b'=')

    def test_fault(self):
        self._decoder.fault_zone(1)
        self._device.write.assert_called_with(bytes("L{0:02}{1}\r".format(1, 1), 'utf-8'))

    def test_fault_wireproblem(self):
        self._decoder.fault_zone(1, simulate_wire_problem=True)
        self._device.write.assert_called_with(bytes("L{0:02}{1}\r".format(1, 2), 'utf-8'))

    def test_clear_zone(self):
        self._decoder.clear_zone(1)
        self._device.write.assert_called_with(bytes("L{0:02}0\r".format(1), 'utf-8'))

    def test_message(self):
        msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertIsInstance(msg, Message)

        self._decoder._on_read(self, data=b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertTrue(self._message_received)

    def test_message_kpm(self):
        msg = self._decoder._handle_message(b'!KPM:[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertIsInstance(msg, Message)

        self._decoder._on_read(self, data=b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertTrue(self._message_received)

    def test_expander_message(self):
        msg = self._decoder._handle_message(b'!EXP:07,01,01')
        self.assertIsInstance(msg, ExpanderMessage)

        self._decoder._on_read(self, data=b'!EXP:07,01,01')
        self.assertTrue(self._expander_message_received)

    def test_relay_message(self):
        self._decoder.open()
        msg = self._decoder._handle_message(b'!REL:12,01,01')
        self.assertIsInstance(msg, ExpanderMessage)
        self.assertEquals(self._relay_changed, True)

    def test_rfx_message(self):
        msg = self._decoder._handle_message(b'!RFX:0180036,80')
        self.assertIsInstance(msg, RFMessage)
        self.assertTrue(self._rfx_message_received)

    def test_panic(self):
        self._decoder.open()

        msg = self._decoder._handle_message(b'!LRR:012,1,ALARM_PANIC')
        self.assertEquals(self._panicked, True)

        msg = self._decoder._handle_message(b'!LRR:012,1,CANCEL')
        self.assertEquals(self._panicked, False)
        self.assertIsInstance(msg, LRRMessage)

    def test_config_message(self):
        self._decoder.open()

        msg = self._decoder._handle_message(b'!CONFIG>ADDRESS=18&CONFIGBITS=ff00&LRR=N&EXP=NNNNN&REL=NNNN&MASK=ffffffff&DEDUPLICATE=N')
        self.assertEquals(self._decoder.address, 18)
        self.assertEquals(self._decoder.configbits, int('ff00', 16))
        self.assertEquals(self._decoder.address_mask, int('ffffffff', 16))
        self.assertEquals(self._decoder.emulate_zone, [False for x in range(5)])
        self.assertEquals(self._decoder.emulate_relay, [False for x in range(4)])
        self.assertEquals(self._decoder.emulate_lrr, False)
        self.assertEquals(self._decoder.deduplicate, False)

        self.assertEquals(self._got_config, True)

    def test_power_changed_event(self):
        msg = self._decoder._handle_message(b'[0000000100000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._power_changed, False)   # Not set first time we hit it.

        msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._power_changed, False)

        msg = self._decoder._handle_message(b'[0000000100000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._power_changed, True)

    def test_alarm_event(self):
        msg = self._decoder._handle_message(b'[0000000000100000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._alarmed, False)   # Not set first time we hit it.

        msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._alarmed, False)
        self.assertEquals(self._alarm_restored, True)

        msg = self._decoder._handle_message(b'[0000000000100000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._alarmed, True)

    def test_zone_bypassed_event(self):
        msg = self._decoder._handle_message(b'[0000001000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._bypassed, False)   # Not set first time we hit it.

        msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._bypassed, False)

        msg = self._decoder._handle_message(b'[0000001000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._bypassed, True)

    def test_armed_away_event(self):
        msg = self._decoder._handle_message(b'[0100000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)   # Not set first time we hit it.

        msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)

        msg = self._decoder._handle_message(b'[0100000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, True)

        self._armed = False

        msg = self._decoder._handle_message(b'[0010000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)   # Not set first time we hit it.

        msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, False)

        msg = self._decoder._handle_message(b'[0010000000000000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._armed, True)

    def test_battery_low_event(self):
        msg = self._decoder._handle_message(b'[0000000000010000----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._battery, True)

        # force the timeout to expire.
        with patch.object(time, 'time', return_value=self._decoder._battery_status[1] + 35):
            msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
            self.assertEquals(self._battery, False)

    def test_fire_alarm_event(self):
        msg = self._decoder._handle_message(b'[0000000000000100----],000,[f707000600e5800c0c020000],"                                "')
        self.assertEquals(self._fire, True)

        # force the timeout to expire.
        with patch.object(time, 'time', return_value=self._decoder._battery_status[1] + 35):
            msg = self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"                                "')
            self.assertEquals(self._fire, False)

    def test_hit_for_faults(self):
        self._decoder._handle_message(b'[0000000000000000----],000,[f707000600e5800c0c020000],"Hit * for faults                "')

        self._decoder._device.write.assert_called_with(b'*')

    def test_sending_received(self):
        self._decoder._on_read(self, data=b'!Sending.done')
        self.assertTrue(self._sending_received_status)

        self._decoder._on_read(self, data=b'!Sending.....done')
        self.assertFalse(self._sending_received_status)

    def test_boot(self):
        self._decoder._on_read(self, data=b'!Ready')
        self.assertTrue(self._on_boot_received)

    def test_zone_fault_and_restore(self):
        self._decoder._on_read(self, data=b'[00010001000000000A--],003,[f70000051003000008020000000000],"FAULT 03                        "')
        self.assertEquals(self._zone_faulted, 3)

        self._decoder._on_read(self, data=b'[00010001000000000A--],004,[f70000051003000008020000000000],"FAULT 04                        "')
        self.assertEquals(self._zone_faulted, 4)

        self._decoder._on_read(self, data=b'[00010001000000000A--],005,[f70000051003000008020000000000],"FAULT 05                        "')
        self.assertEquals(self._zone_faulted, 5)

        self._decoder._on_read(self, data=b'[00010001000000000A--],004,[f70000051003000008020000000000],"FAULT 04                        "')
        self.assertEquals(self._zone_restored, 3)
