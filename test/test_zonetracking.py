from unittest import TestCase
from mock import Mock, MagicMock

from alarmdecoder import AlarmDecoder
from alarmdecoder.panels import ADEMCO
from alarmdecoder.messages import Message, ExpanderMessage
from alarmdecoder.zonetracking import Zonetracker, Zone


class TestZonetracking(TestCase):
    def setUp(self):
        self._alarmdecoder = Mock(spec=AlarmDecoder)

        self._alarmdecoder.mode = ADEMCO
        self._zonetracker = Zonetracker(self._alarmdecoder)

        self._zonetracker.on_fault += self.fault_event
        self._zonetracker.on_restore += self.restore_event

        self._faulted = False
        self._restored = False

    def tearDown(self):
        pass

    ### Library events
    def fault_event(self, sender, *args, **kwargs):
        self._faulted = True

    def restore_event(self, sender, *args, **kwargs):
        self._restored = True

    ### Util
    def _build_expander_message(self, msg):
        msg = ExpanderMessage(msg)
        zone = self._zonetracker.expander_to_zone(msg.address, msg.channel)

        return zone, msg

    ### Tests
    def test_zone_fault(self):
        zone, msg = self._build_expander_message('!EXP:07,01,01')
        self._zonetracker.update(msg)

        self.assertEqual(self._zonetracker._zones[zone].status, Zone.FAULT)
        self.assertTrue(self._faulted)

    def test_zone_restore(self):
        zone, msg = self._build_expander_message('!EXP:07,01,01')
        self._zonetracker.update(msg)

        zone, msg = self._build_expander_message('!EXP:07,01,00')
        self._zonetracker.update(msg)

        self.assertEqual(self._zonetracker._zones[zone].status, Zone.CLEAR)
        self.assertTrue(self._restored)

    def test_message_ready(self):
        msg = Message('[00000000000000100A--],001,[f707000600e5800c0c020000],"                                "')
        self._zonetracker.update(msg)

        self.assertEqual(len(self._zonetracker._zones_faulted), 1)

        msg = Message('[10000000000000000A--],000,[f707000600e5800c0c020000],"                                "')
        self._zonetracker.update(msg)

        self.assertEqual(len(self._zonetracker._zones_faulted), 0)

    def test_message_fault_text(self):
        msg = Message('[00000000000000000A--],001,[f707000600e5800c0c020000],"FAULT 1                         "')
        self._zonetracker.update(msg)

        self.assertEqual(len(self._zonetracker._zones_faulted), 1)

    def test_ECP_failure(self):
        msg = Message('[00000000000000100A--],0bf,[f707000600e5800c0c020000],"CHECK 1                         "')
        self._zonetracker.update(msg)

        self.assertEqual(self._zonetracker._zones['1'].status, Zone.CHECK)

    def test_zone_restore_skip(self):
        panel_messages = [
            '[00000000000000000A--],001,[f707000600e5800c0c020000],"FAULT 1                         "',
            '[00000000000000000A--],002,[f707000600e5800c0c020000],"FAULT 2                         "',
            '[00000000000000000A--],001,[f707000600e5800c0c020000],"FAULT 1                         "',
            '[00000000000000000A--],001,[f707000600e5800c0c020000],"FAULT 1                         "'
        ]

        for m in panel_messages:
            msg = Message(m)

            self._zonetracker.update(msg)

        self.assertIn(1, self._zonetracker._zones_faulted)
        self.assertNotIn(2, self._zonetracker._zones_faulted)

    def test_zone_out_of_order_fault(self):
        panel_messages = [
            '[00000000000000100A--],001,[f707000600e5800c0c020000],"FAULT 1                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
            '[00000000000000100A--],003,[f707000600e5800c0c020000],"FAULT 3                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
        ]

        for m in panel_messages:
            msg = Message(m)

            self._zonetracker.update(msg)

        self.assertIn(1, self._zonetracker._zones_faulted)
        self.assertIn(3, self._zonetracker._zones_faulted)
        self.assertIn(4, self._zonetracker._zones_faulted)

    def test_zone_multi_zone_skip_restore(self):
        panel_messages = [
            '[00000000000000100A--],001,[f707000600e5800c0c020000],"FAULT 1                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
            '[00000000000000100A--],002,[f707000600e5800c0c020000],"FAULT 2                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
        ]

        for m in panel_messages:
            msg = Message(m)

            self._zonetracker.update(msg)

        self.assertNotIn(1, self._zonetracker._zones_faulted)
        self.assertNotIn(2, self._zonetracker._zones_faulted)
        self.assertIn(4, self._zonetracker._zones_faulted)

    def test_zone_timeout_restore(self):
        panel_messages = [
            '[00000000000000100A--],001,[f707000600e5800c0c020000],"FAULT 1                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
            '[00000000000000100A--],002,[f707000600e5800c0c020000],"FAULT 2                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
            '[00000000000000100A--],004,[f707000600e5800c0c020000],"FAULT 4                         "',
        ]

        for m in panel_messages:
            msg = Message(m)

            self._zonetracker.update(msg)

        self.assertIn(4, self._zonetracker._zones_faulted)
        self._zonetracker._zones[4].timestamp -= 35     # forcefully expire the zone

        # generic message to force an update.
        msg = Message('[00000000000000000A--],000,[f707000600e5800c0c020000],"                                "')
        self._zonetracker.update(msg)

        self.assertNotIn(4, self._zonetracker._zones_faulted)
