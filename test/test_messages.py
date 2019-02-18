from unittest import TestCase

from alarmdecoder.messages import Message, ExpanderMessage, RFMessage, LRRMessage
from alarmdecoder.messages.lrr import LRR_EVENT_TYPE, LRR_CID_EVENT, LRR_EVENT_STATUS
from alarmdecoder.util import InvalidMessageError
from alarmdecoder.panels import ADEMCO


class TestMessages(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    ### Tests
    def test_message_parse(self):
        msg = Message('[00000000000000000A--],001,[f707000600e5800c0c020000],"FAULT 1                         "')

        self.assertFalse(msg.ready)
        self.assertFalse(msg.armed_away)
        self.assertFalse(msg.armed_home)
        self.assertFalse(msg.backlight_on)
        self.assertFalse(msg.programming_mode)
        self.assertEqual(msg.beeps, 0)
        self.assertFalse(msg.zone_bypassed)
        self.assertFalse(msg.ac_power)
        self.assertFalse(msg.chime_on)
        self.assertFalse(msg.alarm_event_occurred)
        self.assertFalse(msg.alarm_sounding)
        self.assertFalse(msg.battery_low)
        self.assertFalse(msg.entry_delay_off)
        self.assertFalse(msg.fire_alarm)
        self.assertFalse(msg.check_zone)
        self.assertFalse(msg.perimeter_only)
        self.assertEqual(msg.system_fault, 0)
        self.assertFalse(msg.panel_type, ADEMCO)
        self.assertEqual(msg.numeric_code, '001')
        self.assertEqual(msg.mask, int('07000600', 16))
        self.assertEqual(msg.cursor_location, -1)
        self.assertEqual(msg.text, 'FAULT 1                         ')

    def test_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = Message('')

    def test_expander_message_parse(self):
        msg = ExpanderMessage('!EXP:07,01,01')

        self.assertEqual(msg.address, 7)
        self.assertEqual(msg.channel, 1)
        self.assertEqual(msg.value, 1)

    def test_expander_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = ExpanderMessage('')

    def test_rf_message_parse(self):
        msg = RFMessage('!RFX:0180036,80')

        self.assertEqual(msg.serial_number, '0180036')
        self.assertEqual(msg.value, int('80', 16))

    def test_rf_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = RFMessage('')

    def test_lrr_message_parse_v1(self):
        msg = LRRMessage('!LRR:012,1,ARM_STAY')

        self.assertEqual(msg.event_data, '012')
        self.assertEqual(msg.partition, '1')
        self.assertEqual(msg.event_type, 'ARM_STAY')

    def test_lrr_message_parse_v2(self):
        msg = LRRMessage('!LRR:001,1,CID_3401,ff')
        self.assertIsInstance(msg, LRRMessage)
        self.assertEquals(msg.event_data, '001')
        self.assertEquals(msg.partition, '1')
        self.assertEquals(msg.event_prefix, 'CID')
        self.assertEquals(msg.event_source, LRR_EVENT_TYPE.CID)
        self.assertEquals(msg.event_status, LRR_EVENT_STATUS.RESTORE)
        self.assertEquals(msg.event_code, LRR_CID_EVENT.OPENCLOSE_BY_USER)
        self.assertEquals(msg.report_code, 'ff')

    def test_lrr_event_code_override(self):
        msg = LRRMessage('!LRR:001,1,CID_3400,01')
        self.assertEquals(msg.event_code, LRR_CID_EVENT.OPENCLOSE_BY_USER)  # 400 -> 401

    def test_lrr_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = LRRMessage('')
