from unittest import TestCase

from alarmdecoder.messages import Message, ExpanderMessage, RFMessage, LRRMessage
from alarmdecoder.util import InvalidMessageError


class TestMessages(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_message_parse(self):
        msg = Message('[0000000000000000----],001,[f707000600e5800c0c020000],"FAULT 1                         "')

        self.assertEquals(msg.numeric_code, '001')

    def test_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = Message('')

    def test_expander_message_parse(self):
        msg = ExpanderMessage('!EXP:07,01,01')

        self.assertEquals(msg.address, 7)

    def test_expander_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = ExpanderMessage('')

    def test_rf_message_parse(self):
        msg = RFMessage('!RFX:0180036,80')

        self.assertEquals(msg.serial_number, '0180036')

    def test_rf_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = RFMessage('')

    def test_lrr_message_parse(self):
        msg = LRRMessage('!LRR:012,1,ARM_STAY')

        self.assertEquals(msg.event_type, 'ARM_STAY')

    def test_lrr_message_parse_fail(self):
        with self.assertRaises(InvalidMessageError):
            msg = LRRMessage('')
