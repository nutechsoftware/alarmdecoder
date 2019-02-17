"""
Constants and utility functions used for LRR event handling.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

def get_event_description(event_type, event_code):
    """
    Retrieves the human-readable description of an LRR event.

    :param event_type: Base LRR event type.  Use LRR_EVENT_TYPE.*
    :type event_type: int
    :param event_code: LRR event code
    :type event_code: int

    :returns: string
    """
    description = 'Unknown'
    lookup_map = LRR_TYPE_MAP.get(event_type, None)

    if lookup_map is not None:
        description = lookup_map.get(event_code, description)
        # Extract the real message if it's a dictionary
        if isinstance(description, dict):
            description = description.get('message', description)
    return description

def get_event_data_type(event_type, event_code):
    """
    Retrieves the human-readable data type for the LRR event.

    :param event_type: Base LRR event type.  Use LRR_EVENT_TYPE.*
    :type event_type: int
    :param event_code: LRR event code
    :type event_code: int

    :returns: string
    """
    dtype = ''
    lookup_map = LRR_TYPE_MAP.get(event_type, None)

    if lookup_map is not None:
        dtype = lookup_map.get(event_code, dtype)
        # Extract the event data type if it's a dictionary
        if isinstance(dtype, dict):
            dtype = dtype.get('dtype', dtype)
    return dtype

def get_event_source(prefix):
    """
    Retrieves the LRR_EVENT_TYPE corresponding to the prefix provided.abs

    :param prefix: Prefix to convert to event type
    :type prefix: string

    :returns: int
    """
    source = LRR_EVENT_TYPE.UNKNOWN

    if prefix == 'CID':
        source = LRR_EVENT_TYPE.CID
    elif prefix == 'DSC':
        source = LRR_EVENT_TYPE.DSC
    elif prefix == 'AD2':
        source = LRR_EVENT_TYPE.ALARMDECODER
    elif prefix == 'ADEMCO':
        source = LRR_EVENT_TYPE.ADEMCO

    return source


class LRR_EVENT_TYPE:
    """
    Base LRR event types
    """
    CID = 1
    DSC = 2
    ADEMCO = 3
    ALARMDECODER = 4
    UNKNOWN = 5


class LRR_EVENT_STATUS:
    """
    LRR event status codes
    """
    TRIGGER = 1
    RESTORE = 3

class LRR_DATA_TYPE:
    """
    LRR Data type for the event
    """
    ZONE = 'Z'
    USER = 'U'

class LRR_CID_EVENT:
    """
    ContactID event codes
    """
    MEDICAL = 0x100
    MEDICAL_PENDANT = 0x101
    MEDICAL_FAIL_TO_REPORT = 0x102
    # 103-108: ?
    TAMPER_ZONE = 0x109     # NOTE: Where did we find this?
    FIRE = 0x110
    FIRE_SMOKE = 0x111
    FIRE_COMBUSTION = 0x112
    FIRE_WATER_FLOW = 0x113
    FIRE_HEAT = 0x114
    FIRE_PULL_STATION = 0x115
    FIRE_DUCT = 0x116
    FIRE_FLAME = 0x117
    FIRE_NEAR_ALARM = 0x118
    PANIC = 0x120
    PANIC_DURESS = 0x121
    PANIC_SILENT = 0x122
    PANIC_AUDIBLE = 0x123
    PANIC_DURESS_ACCESS_GRANTED = 0x124
    PANIC_DURESS_EGRESS_GRANTED = 0x125
    PANIC_HOLDUP_SUSPICION = 0x126
    # 127-128: ?
    PANIC_HOLDUP_VERIFIER = 0x129
    BURGLARY = 0x130
    BURGLARY_PERIMETER = 0x131
    BURGLARY_INTERIOR = 0x132
    BURGLARY_AUX = 0x133
    BURGLARY_ENTRYEXIT = 0x134
    BURGLARY_DAYNIGHT = 0x135
    BURGLARY_OUTDOOR = 0x136
    BURGLARY_TAMPER = 0x137
    BURGLARY_NEAR_ALARM = 0x138
    BURGLARY_INTRUSION_VERIFIER = 0x139
    ALARM_GENERAL = 0x140
    ALARM_POLLING_LOOP_OPEN = 0x141
    ALARM_POLLING_LOOP_SHORT = 0x142
    ALARM_EXPANSION_MOD_FAILURE = 0x143
    ALARM_SENSOR_TAMPER = 0x144
    ALARM_EXPANSION_MOD_TAMPER = 0x145
    BURGLARY_SILENT = 0x146
    TROUBLE_SENSOR_SUPERVISION = 0x147
    # 148-149: ?
    ALARM_AUX = 0x150
    ALARM_GAS_DETECTED = 0x151
    ALARM_REFRIDGERATION = 0x152
    ALARM_LOSS_OF_HEAT = 0x153
    ALARM_WATER_LEAKAGE = 0x154
    TROUBLE_FOIL_BREAK = 0x155
    TROUBLE_DAY_TROUBLE = 0x156
    ALARM_LOW_BOTTLED_GAS_LEVEL = 0x157
    ALARM_HIGH_TEMP = 0x158
    ALARM_LOW_TEMP = 0x159
    # 160: ?
    ALARM_LOSS_OF_AIR_FLOW = 0x161
    ALARM_CARBON_MONOXIDE = 0x162
    TROUBLE_TANK_LEVEL = 0x163
    # 164-167: ?
    TROUBLE_HIGH_HUMIDITY = 0x168
    TROUBLE_LOW_HUMIDITY = 0x169
    # 170-199: ?
    SUPERVISORY_FIRE = 0x200
    SUPERVISORY_LOW_PRESSURE = 0x201
    SUPERVISORY_LOW_CO2 = 0x202
    SUPERVISORY_GATE_VALVE_SENSOR = 0x203
    SUPERVISORY_LOW_WATER_LEVEL = 0x204
    SUPERVISORY_PUMP_ACTIVATED = 0x205
    SUPERVISORY_PUMP_FAILURE = 0x206
    # 207-299: ?
    TROUBLE_SYSTEM_TROUBLE = 0x300
    TROUBLE_AC_LOSS = 0x301
    TROUBLE_LOW_BATTERY = 0x302
    TROUBLE_RAM_CHECKSUM_BAD = 0x303
    TROUBLE_ROM_CHECKSUM_BAD = 0x304
    TROUBLE_RESET = 0x305
    TROUBLE_PANEL_PROGRAMMING_CHANGED = 0x306
    TROUBLE_SELF_TEST_FAILURE = 0x307
    TROUBLE_SHUTDOWN = 0x308
    TROUBLE_BATTERY_TEST_FAIL = 0x309
    TROUBLE_GROUND_FAULT = 0x310
    TROUBLE_BATTERY_MISSING = 0x311
    TROUBLE_POWER_SUPPLY_OVERCURRENT = 0x312
    STATUS_ENGINEER_RESET = 0x313
    TROUBLE_PRIMARY_POWER_SUPPLY_FAILURE = 0x314
    # 315: ?
    TROUBLE_TAMPER = 0x316
    # 317-319: ?
    TROUBLE_SOUNDER = 0x320
    TROUBLE_BELL_1 = 0x321
    TROUBLE_BELL_2 = 0x322
    TROUBLE_ALARM_RELAY = 0x323
    TROUBLE_TROUBLE_RELAY = 0x324
    TROUBLE_REVERSING_RELAY = 0x325
    TROUBLE_NOTIFICATION_APPLIANCE_CIRCUIT_3 = 0x326
    TROUBLE_NOTIFICATION_APPLIANCE_CIRCUIT_4 = 0x327
    # 328-329: ?
    TROUBLE_SYSTEM_PERIPHERAL = 0x330
    TROUBLE_POLLING_LOOP_OPEN = 0x331
    TROUBLE_POLLING_LOOP_SHORT = 0x332
    TROUBLE_EXPANSION_MODULE_FAILURE = 0x333
    TROUBLE_REPEATER_FAILURE = 0x334
    TROUBLE_LOCAL_PRINTER_PAPER_OUT = 0x335
    TROUBLE_LOCAL_PRINTER_FAILURE = 0x336
    TROUBLE_EXPANDER_MODULE_DC_LOSS = 0x337
    TROUBLE_EXPANDER_MODULE_LOW_BATTERY = 0x338
    TROUBLE_EXPANDER_MODULE_RESET = 0x339
    # 340: ?
    TROUBLE_EXPANDER_MODULE_TAMPER = 0x341
    TROUBLE_EXPANDER_MODULE_AC_LOSS = 0x342
    TROUBLE_EXPANDER_MODULE_SELF_TEST_FAIL = 0x343
    TROUBLE_RF_RECEIVER_JAM_DETECTED = 0x344
    TROUBLE_AES_ENCRYPTION = 0x345
    # 346-349: ?
    TROUBLE_COMMUNICATION = 0x350
    TROUBLE_TELCO_1_FAULT = 0x351
    TROUBLE_TELCO_2_FAULT = 0x352
    TROUBLE_LRR_TRANSMITTER_FAULT = 0x353
    TROUBLE_FAILURE_TO_COMMUNICATE = 0x354
    TROUBLE_LOSS_OF_RADIO_SUPERVISION = 0x355
    TROUBLE_LOSS_OF_CENTRAL_POLLING = 0x356
    TROUBLE_LRR_TRANSMITTER_VSWR = 0x357
    TROUBLE_PERIODIC_COMM_TEST = 0x358
    # 359-369: ?
    TROUBLE_PROTECTION_LOOP = 0x370
    TROUBLE_PROTECTION_LOOP_OPEN = 0x371
    TROUBLE_PROTECTION_LOOP_SHORT = 0x372
    TROUBLE_FIRE = 0x373
    TROUBLE_EXIT_ERROR = 0x374
    TROUBLE_PANIC_ZONE_TROUBLE = 0x375
    TROUBLE_HOLDUP_ZONE_TROUBLE = 0x376
    TROUBLE_SWINGER_TROUBLE = 0x377
    TROUBLE_CROSS_ZONE_TROUBLE = 0x378
    # 379: ?
    TROUBLE_SENSOR_TROUBLE = 0x380
    TROUBLE_RF_LOSS_OF_SUPERVISION = 0x381
    TROUBLE_RPM_LOSS_OF_SUPERVISION = 0x382
    TROUBLE_SENSOR_TAMPER = 0x383
    TROUBLE_RF_LOW_BATTERY = 0x384
    TROUBLE_SMOKE_HI_SENS = 0x385
    TROUBLE_SMOKE_LO_SENS = 0x386
    TROUBLE_INTRUSION_HI_SENS = 0x387
    TROUBLE_INTRUSION_LO_SENS = 0x388
    TROUBLE_SELF_TEST_FAIL = 0x389
    # 390: ?
    TROUBLE_SENSOR_WATCH_FAIL = 0x391
    TROUBLE_DRIFT_COMP_ERROR = 0x392
    TROUBLE_MAINTENANCE_ALERT = 0x393
    # 394-399: ?
    OPENCLOSE = 0x400
    OPENCLOSE_BY_USER = 0x401
    OPENCLOSE_GROUP = 0x402
    OPENCLOSE_AUTOMATIC = 0x403
    OPENCLOSE_LATE = 0x404
    OPENCLOSE_DEFERRED = 0x405
    OPENCLOSE_CANCEL_BY_USER = 0x406
    OPENCLOSE_REMOTE_ARMDISARM = 0x407
    OPENCLOSE_QUICK_ARM = 0x408
    OPENCLOSE_KEYSWITCH = 0x409
    # 410: ?
    REMOTE_CALLBACK_REQUESTED = 0x411
    REMOTE_SUCCESS = 0x412
    REMOTE_UNSUCCESSFUL = 0x413
    REMOTE_SYSTEM_SHUTDOWN = 0x414
    REMOTE_DIALER_SHUTDOWN = 0x415
    REMOTE_SUCCESSFUL_UPLOAD = 0x416
    # 417-420: ?
    ACCESS_DENIED = 0x421
    ACCESS_REPORT_BY_USER = 0x422
    ACCESS_FORCED_ACCESS = 0x423
    ACCESS_EGRESS_DENIED = 0x424
    ACCESS_EGRESS_GRANTED = 0x425
    ACCESS_DOOR_PROPPED_OPEN = 0x426
    ACCESS_POINT_DSM_TROUBLE = 0x427
    ACCESS_POINT_RTE_TROUBLE = 0x428
    ACCESS_PROGRAM_MODE_ENTRY = 0x429
    ACCESS_PROGRAM_MODE_EXIT = 0x430
    ACCESS_THREAT_LEVEL_CHANGE = 0x431
    ACCESS_RELAY_FAIL = 0x432
    ACCESS_RTE_SHUNT = 0x433
    ACCESS_DSM_SHUNT = 0x434
    ACCESS_SECOND_PERSON = 0x435
    ACCESS_IRREGULAR_ACCESS = 0x436
    # 437-440: ?
    OPENCLOSE_ARMED_STAY = 0x441
    OPENCLOSE_KEYSWITCH_ARMED_STAY = 0x442
    # 443-449: ?
    OPENCLOSE_EXCEPTION = 0x450
    OPENCLOSE_EARLY = 0x451
    OPENCLOSE_LATE = 0x452
    TROUBLE_FAILED_TO_OPEN = 0x453
    TROUBLE_FAILED_TO_CLOSE = 0x454
    TROUBLE_AUTO_ARM_FAILED = 0x455
    OPENCLOSE_PARTIAL_ARM = 0x456
    OPENCLOSE_EXIT_ERROR = 0x457
    OPENCLOSE_USER_ON_PREMISES = 0x458
    TROUBLE_RECENT_CLOSE = 0x459
    # 460: ?
    ACCESS_WRONG_CODE_ENTRY = 0x461
    ACCESS_LEGAL_CODE_ENTRY = 0x462
    STATUS_REARM_AFTER_ALARM = 0x463
    STATUS_AUTO_ARM_TIME_EXTENDED = 0x464
    STATUS_PANIC_ALARM_RESET = 0x465
    ACCESS_SERVICE_ONOFF_PREMISES = 0x466
    # 467-469: ?
    OPENCLOSE_PARTIAL_CLOSING = 0x470   # HACK: This is from our DSC firmware implementation, 
                                        #       and is named far too closely to 0x480.
    # 471-479: ?
    OPENCLOSE_PARTIAL_CLOSE = 0x480
    # 481-500: ?
    DISABLE_ACCESS_READER = 0x501
    # 502-519: ?
    DISABLE_SOUNDER = 0x520
    DISABLE_BELL_1 = 0x521
    DISABLE_BELL_2 = 0x522
    DISABLE_ALARM_RELAY = 0x523
    DISABLE_TROUBLE_RELAY = 0x524
    DISABLE_REVERSING_RELAY = 0x525
    DISABLE_NOTIFICATION_APPLIANCE_CIRCUIT_3 = 0x526
    DISABLE_NOTIFICATION_APPLIANCE_CIRCUIT_4 = 0x527
    # 528-530: ?
    SUPERVISORY_MODULE_ADDED = 0x531
    SUPERVISORY_MODULE_REMOVED = 0x532
    # 533-550: ?
    DISABLE_DIALER = 0x551
    DISABLE_RADIO_TRANSMITTER = 0x552
    DISABLE_REMOTE_UPLOADDOWNLOAD = 0x553
    # 554-569: ?
    BYPASS_ZONE = 0x570
    BYPASS_FIRE = 0x571
    BYPASS_24HOUR_ZONE = 0x572
    BYPASS_BURGLARY = 0x573
    BYPASS_GROUP = 0x574
    BYPASS_SWINGER = 0x575
    BYPASS_ACCESS_ZONE_SHUNT = 0x576
    BYPASS_ACCESS_POINT_BYPASS = 0x577
    BYPASS_ZONE_VAULT = 0x578
    BYPASS_ZONE_VENT = 0x579
    # 580-600: ?
    TEST_MANUAL = 0x601
    TEST_PERIODIC = 0x602
    TEST_PERIODIC_RF_TRANSMISSION = 0x603
    TEST_FIRE = 0x604
    TEST_FIRE_STATUS = 0x605
    TEST_LISTENIN_TO_FOLLOW = 0x606
    TEST_WALK = 0x607
    TEST_SYSTEM_TROUBLE_PRESENT = 0x608
    TEST_VIDEO_TRANSMITTER_ACTIVE = 0x609
    # 610: ?
    TEST_POINT_TESTED_OK = 0x611
    TEST_POINT_NOT_TESTED = 0x612
    TEST_INTRUSION_ZONE_WALK_TESTED = 0x613
    TEST_FIRE_ZONE_WALK_TESTED = 0x614
    TEST_PANIC_ZONE_WALK_TESTED = 0x615
    TROUBLE_SERVICE_REQUEST = 0x616
    # 617-620: ?
    TROUBLE_EVENT_LOG_RESET = 0x621
    TROUBLE_EVENT_LOG_50PERCENT_FULL = 0x622
    TROUBLE_EVENT_LOG_90PERCENT_FULL = 0x623
    TROUBLE_EVENT_LOG_OVERFLOW = 0x624
    TROUBLE_TIMEDATE_RESET = 0x625
    TROUBLE_TIMEDATE_INACCURATE = 0x626
    TROUBLE_PROGRAM_MODE_ENTRY = 0x627
    TROUBLE_PROGRAM_MODE_EXIT = 0x628
    TROUBLE_32HOUR_EVENT_LOG_MARKER = 0x629
    SCHEDULE_CHANGE = 0x630
    SCHEDULE_EXCEPTION_SCHEDULE_CHANGE = 0x631
    SCHEDULE_ACCESS_SCHEDULE_CHANGE = 0x632
    # 633-640: ?
    TROUBLE_SENIOR_WATCH_TROUBLE = 0x641
    STATUS_LATCHKEY_SUPERVISION = 0x642
    # 643-650: ?
    SPECIAL_ADT_AUTHORIZATION = 0x651
    RESERVED_652 = 0x652
    RESERVED_653 = 0x653
    TROUBLE_SYSTEM_INACTIVITY = 0x654
    # 750-789: User Assigned
    # 790-795: ?
    TROUBLE_UNABLE_TO_OUTPUT_SIGNAL = 0x796
    # 797: ?
    TROUBLE_STU_CONTROLLER_DOWN = 0x798
    # 799-899: ?
    REMOTE_DOWNLOAD_ABORT = 0x900
    REMOTE_DOWNLOAD_STARTEND = 0x901
    REMOTE_DOWNLOAD_INTERRUPTED = 0x902
    REMOTE_CODE_DOWNLOAD_STARTEND = 0x903
    REMOTE_CODE_DOWNLOAD_FAILED = 0x904
    # 905-909: ?
    OPENCLOSE_AUTOCLOSE_WITH_BYPASS = 0x910
    OPENCLOSE_BYPASS_CLOSING = 0x911
    EVENT_FIRE_ALARM_SILENCED = 0x912
    EVENT_SUPERVISOR_POINT_STARTEND = 0x913
    EVENT_HOLDUP_TEST_STARTEND = 0x914
    EVENT_BURGLARY_TEST_PRINT_STARTEND = 0x915
    EVENT_SUPERVISORY_TEST_PRINT_STARTEND = 0x916
    EVENT_BURGLARY_DIAGNOSTICS_STARTEND = 0x917
    EVENT_FIRE_DIAGNOSTICS_STARTEND = 0x918
    EVENT_UNTYPED_DIAGNOSTICS = 0x919
    EVENT_TROUBLE_CLOSING = 0x920
    EVENT_ACCESS_DENIED_CODE_UNKNOWN = 0x921
    ALARM_SUPERVISORY_POINT = 0x922
    EVENT_SUPERVISORY_POINT_BYPASS = 0x923
    TROUBLE_SUPERVISORY_POINT = 0x924
    EVENT_HOLDUP_POINT_BYPASS = 0x925
    EVENT_AC_FAILURE_FOR_4HOURS = 0x926
    TROUBLE_OUTPUT = 0x927
    EVENT_USER_CODE_FOR_EVENT = 0x928
    EVENT_LOG_OFF = 0x929
    # 930-953: ?
    EVENT_CS_CONNECTION_FAILURE = 0x954
    # 955-960: ?
    EVENT_RECEIVER_DATABASE_CONNECTION = 0x961
    EVENT_LICENSE_EXPIRATION = 0x962
    # 963-998: ?
    OTHER_NO_READ_LOG = 0x999


class LRR_DSC_EVENT:
    """
    DSC event codes
    """
    ZONE_EXPANDER_SUPERVISORY_ALARM = 0x04c
    ZONE_EXPANDER_SUPERVISORY_RESTORE = 0x04d
    AUX_INPUT_ALARM = 0x051
    SPECIAL_CLOSING = 0x0bf
    CROSS_ZONE_POLICE_CODE_ALARM = 0x103
    AUTOMATIC_CLOSING = 0x12b
    ZONE_BYPASS = 0x570
    REPORT_DSC_USER_LOG_EVENT = 0x800


class LRR_ADEMCO_EVENT:
    """
    ADEMCO event codes
    """
    pass


class LRR_ALARMDECODER_EVENT:
    """
    AlarmDecoder event codes
    """
    CUSTOM_PROG_MSG = 0x0
    CUSTOM_PROG_KEY = 0x1


class LRR_UNKNOWN_EVENT:
    """
    Unknown event codes.  Realistically there shouldn't ever be anything here.
    """
    pass


# Map of ContactID event codes to human-readable text.
LRR_CID_MAP = {
    LRR_CID_EVENT.MEDICAL: {'message': 'Medical Emergency: Non-specific', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.MEDICAL_PENDANT: {'message': 'Emergency Assistance Request', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.MEDICAL_FAIL_TO_REPORT: {'message': 'Medical: Failed to activate monitoring device', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TAMPER_ZONE: {'message': 'Zone Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE: {'message': 'Fire: Non-specific', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_SMOKE: {'message': 'Fire: Smoke Alarm', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_COMBUSTION: {'message': 'Fire: Combustion', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_WATER_FLOW: {'message': 'Fire: Water Flow', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_HEAT: {'message': 'Fire: Heat', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_PULL_STATION: {'message': 'Fire: Pull Station', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_DUCT: {'message': 'Fire: Duct', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_FLAME: {'message': 'Fire: Flame', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.FIRE_NEAR_ALARM: {'message': 'Fire: Near Alarm', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC: {'message': 'Panic', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC_DURESS: {'message': 'Panic: Duress', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC_SILENT: {'message': 'Panic: Silent', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC_AUDIBLE: {'message': 'Panic: Audible', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC_DURESS_ACCESS_GRANTED: {'message': 'Fire: Duress', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC_DURESS_EGRESS_GRANTED: {'message': 'Fire: Egress', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.PANIC_HOLDUP_SUSPICION: {'message': 'Panic: Hold-up, Suspicious Condition', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.PANIC_HOLDUP_VERIFIER: {'message': 'Panic: Hold-up Verified', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY: {'message': 'Burglary', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_PERIMETER: {'message': 'Burglary: Perimeter', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_INTERIOR: {'message': 'Burglary: Interior', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_AUX: {'message': 'Burglary: 24 Hour', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_ENTRYEXIT: {'message': 'Burglary: Entry/Exit', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_DAYNIGHT: {'message': 'Burglary: Day/Night', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_OUTDOOR: {'message': 'Burglary: Outdoor', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_TAMPER: {'message': 'Burglary: Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_NEAR_ALARM: {'message': 'Burglary: Near Alarm', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_INTRUSION_VERIFIER: {'message': 'Burglary: Intrusion Verifier', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_GENERAL: {'message': 'Alarm: General', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_POLLING_LOOP_OPEN: {'message': 'Alarm: Polling Loop Open', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_POLLING_LOOP_SHORT: {'message': 'Alarm: Polling Loop Closed', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_EXPANSION_MOD_FAILURE: {'message': 'Alarm: Expansion Module Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_SENSOR_TAMPER: {'message': 'Alarm: Sensor Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_EXPANSION_MOD_TAMPER: {'message': 'Alarm: Expansion Module Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BURGLARY_SILENT: {'message': 'Burglary: Silent', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SENSOR_SUPERVISION: {'message': 'Trouble: Sensor Supervision Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_AUX: {'message': 'Alarm: 24 Hour Non-Burglary', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_GAS_DETECTED: {'message': 'Alarm: Gas Detected', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_REFRIDGERATION: {'message': 'Alarm: Refridgeration', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_LOSS_OF_HEAT: {'message': 'Alarm: Loss of Heat', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_WATER_LEAKAGE: {'message': 'Alarm: Water Leakage', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_FOIL_BREAK: {'message': 'Trouble: Foil Break', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_DAY_TROUBLE: {'message': 'Trouble: Day Trouble', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_LOW_BOTTLED_GAS_LEVEL: {'message': 'Alarm: Low Bottled Gas Level', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_HIGH_TEMP: {'message': 'Alarm: High Temperature', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_LOW_TEMP: {'message': 'Alarm: Low Temperature', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_LOSS_OF_AIR_FLOW: {'message': 'Alarm: Loss of Air Flow', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ALARM_CARBON_MONOXIDE: {'message': 'Alarm: Carbon Monoxide', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_TANK_LEVEL: {'message': 'Trouble: Tank Level', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_HIGH_HUMIDITY: {'message': 'Trouble: High Humidity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LOW_HUMIDITY: {'message': 'Trouble: Low Humidity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_FIRE: {'message': 'Supervisory: Fire', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_LOW_PRESSURE: {'message': 'Supervisory: Low Water Pressure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_LOW_CO2: {'message': 'Supervisory: Low CO2', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_GATE_VALVE_SENSOR: {'message': 'Supervisory: Gate Valve Sensor', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_LOW_WATER_LEVEL: {'message': 'Supervisory: Low Water Level', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_PUMP_ACTIVATED: {'message': 'Supervisory: Pump Activated', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_PUMP_FAILURE: {'message': 'Supervisory: Pump Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SYSTEM_TROUBLE: {'message': 'Trouble: System Trouble', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_AC_LOSS: {'message': 'Trouble: AC Loss', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LOW_BATTERY: {'message': 'Trouble: Low Battery', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_RAM_CHECKSUM_BAD: {'message': 'Trouble: RAM Checksum Bad', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_ROM_CHECKSUM_BAD: {'message': 'Trouble: ROM Checksum Bad', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_RESET: {'message': 'Trouble: System Reset', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PANEL_PROGRAMMING_CHANGED: {'message': 'Trouble: Panel Programming Changed', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SELF_TEST_FAILURE: {'message': 'Trouble: Self-Test Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SHUTDOWN: {'message': 'Trouble: System Shutdown', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_BATTERY_TEST_FAIL: {'message': 'Trouble: Battery Test Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_GROUND_FAULT: {'message': 'Trouble: Ground Fault', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_BATTERY_MISSING: {'message': 'Trouble: Battery Missing', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_POWER_SUPPLY_OVERCURRENT: {'message': 'Trouble: Power Supply Overcurrent', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.STATUS_ENGINEER_RESET: {'message': 'Status: Engineer Reset', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_PRIMARY_POWER_SUPPLY_FAILURE: {'message': 'Trouble: Primary Power Supply Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_TAMPER: {'message': 'Trouble: System Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SOUNDER: {'message': 'Trouble: Sounder', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_BELL_1: {'message': 'Trouble: Bell 1', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_BELL_2: {'message': 'Trouble: Bell 2', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_ALARM_RELAY: {'message': 'Trouble: Alarm Relay', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_TROUBLE_RELAY: {'message': 'Trouble: Trouble Relay', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_REVERSING_RELAY: {'message': 'Trouble: Reversing Relay', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_NOTIFICATION_APPLIANCE_CIRCUIT_3: {'message': 'Trouble: Notification Appliance Circuit #3', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_NOTIFICATION_APPLIANCE_CIRCUIT_4: {'message': 'Trouble: Notification Appliance Circuit #3', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SYSTEM_PERIPHERAL: {'message': 'Trouble: System Peripheral', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_POLLING_LOOP_OPEN: {'message': 'Trouble: Pooling Loop Open', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_POLLING_LOOP_SHORT: {'message': 'Trouble: Polling Loop Short', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANSION_MODULE_FAILURE: {'message': 'Trouble: Expansion Module Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_REPEATER_FAILURE: {'message': 'Trouble: Repeater Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LOCAL_PRINTER_PAPER_OUT: {'message': 'Trouble: Local Printer Out Of Paper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LOCAL_PRINTER_FAILURE: {'message': 'Trouble: Local Printer Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANDER_MODULE_DC_LOSS: {'message': 'Trouble: Expander Module, DC Power Loss', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANDER_MODULE_LOW_BATTERY: {'message': 'Trouble: Expander Module, Low Battery', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANDER_MODULE_RESET: {'message': 'Trouble: Expander Module, Reset', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANDER_MODULE_TAMPER: {'message': 'Trouble: Expander Module, Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANDER_MODULE_AC_LOSS: {'message': 'Trouble: Expander Module, AC Power Loss', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXPANDER_MODULE_SELF_TEST_FAIL: {'message': 'Trouble: Expander Module, Self-test Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_RF_RECEIVER_JAM_DETECTED: {'message': 'Trouble: RF Receiver Jam Detected', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_AES_ENCRYPTION: {'message': 'Trouble: AES Encryption', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_COMMUNICATION: {'message': 'Trouble: Communication', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_TELCO_1_FAULT: {'message': 'Trouble: Telco 1', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_TELCO_2_FAULT: {'message': 'Trouble: Telco 2', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LRR_TRANSMITTER_FAULT: {'message': 'Trouble: Long Range Radio Transmitter Fault', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_FAILURE_TO_COMMUNICATE: {'message': 'Trouble: Failure To Communicate', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LOSS_OF_RADIO_SUPERVISION: {'message': 'Trouble: Loss of Radio Supervision', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LOSS_OF_CENTRAL_POLLING: {'message': 'Trouble: Loss of Central Polling', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_LRR_TRANSMITTER_VSWR: {'message': 'Trouble: Long Range Radio Transmitter/Antenna', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PERIODIC_COMM_TEST: {'message': 'Trouble: Periodic Communication Test', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PROTECTION_LOOP: {'message': 'Trouble: Protection Loop', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PROTECTION_LOOP_OPEN: {'message': 'Trouble: Protection Loop Open', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PROTECTION_LOOP_SHORT: {'message': 'Trouble: Protection Loop Short', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_FIRE: {'message': 'Trouble: Fire', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EXIT_ERROR: {'message': 'Trouble: Exit Error', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PANIC_ZONE_TROUBLE: {'message': 'Trouble: Panic', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_HOLDUP_ZONE_TROUBLE: {'message': 'Trouble: Hold-up', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SWINGER_TROUBLE: {'message': 'Trouble: Swinger', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_CROSS_ZONE_TROUBLE: {'message': 'Trouble: Cross-zone', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SENSOR_TROUBLE: {'message': 'Trouble: Sensor', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_RF_LOSS_OF_SUPERVISION: {'message': 'Trouble: RF Loss of Supervision', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_RPM_LOSS_OF_SUPERVISION: {'message': 'Trouble: RPM Loss of Supervision', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SENSOR_TAMPER: {'message': 'Trouble: Sensor Tamper', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_RF_LOW_BATTERY: {'message': 'Trouble: RF Low Battery', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SMOKE_HI_SENS: {'message': 'Trouble: Smoke Detector, High Sensitivity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SMOKE_LO_SENS: {'message': 'Trouble: Smoke Detector, Low Sensitivity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_INTRUSION_HI_SENS: {'message': 'Trouble: Intrusion Detector, High Sensitivity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_INTRUSION_LO_SENS: {'message': 'Trouble: Intrusion Detector, Low Sensitivity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SELF_TEST_FAIL: {'message': 'Trouble: Self-test Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SENSOR_WATCH_FAIL: {'message': 'Trouble: Sensor Watch', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_DRIFT_COMP_ERROR: {'message': 'Trouble: Drift Compensation Error', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_MAINTENANCE_ALERT: {'message': 'Trouble: Maintenance Alert', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.OPENCLOSE: {'message': 'Open/Close', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_BY_USER: {'message': 'Open/Close: By User', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_GROUP: {'message': 'Open/Close: Group', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_AUTOMATIC: {'message': 'Open/Close: Automatic', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_LATE: {'message': 'Open/Close: Late', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_DEFERRED: {'message': 'Open/Close: Deferred', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER: {'message': 'Open/Close: Cancel', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_REMOTE_ARMDISARM: {'message': 'Open/Close: Remote', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_QUICK_ARM: {'message': 'Open/Close: Quick Arm', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_KEYSWITCH: {'message': 'Open/Close: Keyswitch', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_CALLBACK_REQUESTED: {'message': 'Remote: Callback Requested', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_SUCCESS: {'message': 'Remote: Successful Access', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_UNSUCCESSFUL: {'message': 'Remote: Unsuccessful Access', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_SYSTEM_SHUTDOWN: {'message': 'Remote: System Shutdown', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_DIALER_SHUTDOWN: {'message': 'Remote: Dialer Shutdown', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_SUCCESSFUL_UPLOAD: {'message': 'Remote: Successful Upload', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_DENIED: {'message': 'Access: Denied', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_REPORT_BY_USER: {'message': 'Access: Report By User', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_FORCED_ACCESS: {'message': 'Access: Forced Access', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_EGRESS_DENIED: {'message': 'Access: Egress Denied', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_EGRESS_GRANTED: {'message': 'Access: Egress Granted', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_DOOR_PROPPED_OPEN: {'message': 'Access: Door Propped Open', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_POINT_DSM_TROUBLE: {'message': 'Access: Door Status Monitor Trouble', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_POINT_RTE_TROUBLE: {'message': 'Access: Request To Exit Trouble', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_PROGRAM_MODE_ENTRY: {'message': 'Access: Program Mode Entry', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_PROGRAM_MODE_EXIT: {'message': 'Access: Program Mode Exit', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_THREAT_LEVEL_CHANGE: {'message': 'Access: Threat Level Change', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_RELAY_FAIL: {'message': 'Access: Relay Fail', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_RTE_SHUNT: {'message': 'Access: Request to Exit Shunt', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_DSM_SHUNT: {'message': 'Access: Door Status Monitor Shunt', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_SECOND_PERSON: {'message': 'Access: Second Person Access', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_IRREGULAR_ACCESS: {'message': 'Access: Irregular Access', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_ARMED_STAY: {'message': 'Open/Close: Armed Stay', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_KEYSWITCH_ARMED_STAY: {'message': 'Open/Close: Keyswitch, Armed Stay', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_EXCEPTION: {'message': 'Open/Close: Armed with Trouble Override', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_EARLY: {'message': 'Open/Close: Early', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_LATE: {'message': 'Open/Close: Late', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_FAILED_TO_OPEN: {'message': 'Trouble: Failed To Open', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_FAILED_TO_CLOSE: {'message': 'Trouble: Failed To Close', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_AUTO_ARM_FAILED: {'message': 'Trouble: Auto Arm Failed', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_PARTIAL_ARM: {'message': 'Open/Close: Partial Arm', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_EXIT_ERROR: {'message': 'Open/Close: Exit Error', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_USER_ON_PREMISES: {'message': 'Open/Close: User On Premises', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_RECENT_CLOSE: {'message': 'Trouble: Recent Close', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ACCESS_WRONG_CODE_ENTRY: {'message': 'Access: Wrong Code', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_LEGAL_CODE_ENTRY: {'message': 'Access: Legal Code', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.STATUS_REARM_AFTER_ALARM: {'message': 'Status: Re-arm After Alarm', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.STATUS_AUTO_ARM_TIME_EXTENDED: {'message': 'Status: Auto-arm Time Extended', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.STATUS_PANIC_ALARM_RESET: {'message': 'Status: Panic Alarm Reset', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.ACCESS_SERVICE_ONOFF_PREMISES: {'message': 'Status: Service On/Off Premises', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_PARTIAL_CLOSING: {'message': 'Open/Close: Partial Closing', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.OPENCLOSE_PARTIAL_CLOSE: {'message': 'Open/Close: Partial Close', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.DISABLE_ACCESS_READER: {'message': 'Disable: Access Reader', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_SOUNDER: {'message': 'Disable: Sounder', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_BELL_1: {'message': 'Disable: Bell 1', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_BELL_2: {'message': 'Disable: Bell 2', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_ALARM_RELAY: {'message': 'Disable: Alarm Relay', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_TROUBLE_RELAY: {'message': 'Disable: Trouble Relay', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_REVERSING_RELAY: {'message': 'Disable: Reversing Relay', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_NOTIFICATION_APPLIANCE_CIRCUIT_3: {'message': 'Disable: Notification Appliance Circuit #3', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_NOTIFICATION_APPLIANCE_CIRCUIT_4: {'message': 'Disable: Notification Appliance Circuit #4', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_MODULE_ADDED: {'message': 'Supervisory: Module Added', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SUPERVISORY_MODULE_REMOVED: {'message': 'Supervisory: Module Removed', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_DIALER: {'message': 'Disable: Dialer', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_RADIO_TRANSMITTER: {'message': 'Disable: Radio Transmitter', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.DISABLE_REMOTE_UPLOADDOWNLOAD: {'message': 'Disable: Remote Upload/Download', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_ZONE: {'message': 'Bypass: Zone', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_FIRE: {'message': 'Bypass: Fire', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_24HOUR_ZONE: {'message': 'Bypass: 24 Hour Zone', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_BURGLARY: {'message': 'Bypass: Burglary', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_GROUP: {'message': 'Bypass: Group', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.BYPASS_SWINGER: {'message': 'Bypass: Swinger', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_ACCESS_ZONE_SHUNT: {'message': 'Bypass: Access Zone Shunt', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_ACCESS_POINT_BYPASS: {'message': 'Bypass: Access Point', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_ZONE_VAULT: {'message': 'Bypass: Vault', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.BYPASS_ZONE_VENT: {'message': 'Bypass: Vent', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_MANUAL: {'message': 'Test: Manual Trigger', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_PERIODIC: {'message': 'Test: Periodic', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_PERIODIC_RF_TRANSMISSION: {'message': 'Test: Periodic RF Transmission', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_FIRE: {'message': 'Test: Fire', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TEST_FIRE_STATUS: {'message': 'Test: Fire, Status Report To Follow', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_LISTENIN_TO_FOLLOW: {'message': 'Test: Listen-in To Follow', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_WALK: {'message': 'Test: Walk', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TEST_SYSTEM_TROUBLE_PRESENT: {'message': 'Test: Periodic Test, System Trouble Present', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_VIDEO_TRANSMITTER_ACTIVE: {'message': 'Test: Video Transmitter Active', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_POINT_TESTED_OK: {'message': 'Test: Point Tested OK', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_POINT_NOT_TESTED: {'message': 'Test: Point Not Tested', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_INTRUSION_ZONE_WALK_TESTED: {'message': 'Test: Intrusion Zone Walk Tested', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_FIRE_ZONE_WALK_TESTED: {'message': 'Test: Fire Zone Walk Tested', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TEST_PANIC_ZONE_WALK_TESTED: {'message': 'Test: Panic Zone Walk Tested', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SERVICE_REQUEST: {'message': 'Trouble: Service Request', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EVENT_LOG_RESET: {'message': 'Trouble: Event Log Reset', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EVENT_LOG_50PERCENT_FULL: {'message': 'Trouble: Event Log 50% Full', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EVENT_LOG_90PERCENT_FULL: {'message': 'Trouble: Event Log 90% Full', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_EVENT_LOG_OVERFLOW: {'message': 'Trouble: Event Log Overflow', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_TIMEDATE_RESET: {'message': 'Trouble: Time/Date Reset', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_TIMEDATE_INACCURATE: {'message': 'Trouble: Time/Date Inaccurate', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PROGRAM_MODE_ENTRY: {'message': 'Trouble: Program Mode Entry', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_PROGRAM_MODE_EXIT: {'message': 'Trouble: Program Mode Exit', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_32HOUR_EVENT_LOG_MARKER: {'message': 'Trouble: 32 Hour Event Log Marker', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SCHEDULE_CHANGE: {'message': 'Schedule: Change', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SCHEDULE_EXCEPTION_SCHEDULE_CHANGE: {'message': 'Schedule: Exception Schedule Change', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.SCHEDULE_ACCESS_SCHEDULE_CHANGE: {'message': 'Schedule: Access Schedule Change', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_SENIOR_WATCH_TROUBLE: {'message': 'Schedule: Senior Watch Trouble', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.STATUS_LATCHKEY_SUPERVISION: {'message': 'Status: Latch-key Supervision', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.SPECIAL_ADT_AUTHORIZATION: {'message': 'Special: ADT Authorization', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.RESERVED_652: {'message': 'Reserved: For Ademco Use', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.RESERVED_653: {'message': 'Reserved: For Ademco Use', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_SYSTEM_INACTIVITY: {'message': 'Trouble: System Inactivity', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_UNABLE_TO_OUTPUT_SIGNAL: {'message': 'Trouble: Unable To Output Signal (Derived Channel)', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_STU_CONTROLLER_DOWN: {'message': 'Trouble: STU Controller Down (Derived Channel)', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.REMOTE_DOWNLOAD_ABORT: {'message': 'Remote: Download Aborted', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_DOWNLOAD_STARTEND: {'message': 'Remote: Download Start/End', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_DOWNLOAD_INTERRUPTED: {'message': 'Remote: Download Interrupted', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.REMOTE_CODE_DOWNLOAD_STARTEND: {'message': 'Remote: Device Flash Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.REMOTE_CODE_DOWNLOAD_FAILED: {'message': 'Remote: Device Flash Failed', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.OPENCLOSE_AUTOCLOSE_WITH_BYPASS: {'message': 'Open/Close: Auto-Close With Bypass', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.OPENCLOSE_BYPASS_CLOSING: {'message': 'Open/Close: Bypass Closing', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_FIRE_ALARM_SILENCED: {'message': 'Event: Fire Alarm Silenced', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_SUPERVISOR_POINT_STARTEND: {'message': 'Event: Supervisory Point Test Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_HOLDUP_TEST_STARTEND: {'message': 'Event: Hold-up Test Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_BURGLARY_TEST_PRINT_STARTEND: {'message': 'Event: Burglary Test Print Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_SUPERVISORY_TEST_PRINT_STARTEND: {'message': 'Event: Supervisory Test Print Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_BURGLARY_DIAGNOSTICS_STARTEND: {'message': 'Event: Burglary Diagnostics Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_FIRE_DIAGNOSTICS_STARTEND: {'message': 'Event: Fire Diagnostics Start/End', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_UNTYPED_DIAGNOSTICS: {'message': 'Event: Untyped Diagnostics', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_TROUBLE_CLOSING: {'message': 'Event: Trouble Closing', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.EVENT_ACCESS_DENIED_CODE_UNKNOWN: {'message': 'Event: Access Denied, Code Unknown', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.ALARM_SUPERVISORY_POINT: {'message': 'Alarm: Supervisory Point', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_SUPERVISORY_POINT_BYPASS: {'message': 'Event: Supervisory Point Bypass', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.TROUBLE_SUPERVISORY_POINT: {'message': 'Trouble: Supervisory Point', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_HOLDUP_POINT_BYPASS: {'message': 'Event: Hold-up Point Bypass', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_AC_FAILURE_FOR_4HOURS: {'message': 'Event: AC Failure For 4 Hours', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.TROUBLE_OUTPUT: {'message': 'Trouble: Output Trouble', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_USER_CODE_FOR_EVENT: {'message': 'Event: User Code For Event', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.EVENT_LOG_OFF: {'message': 'Event: Log-off', 'dtype': LRR_DATA_TYPE.USER},
    LRR_CID_EVENT.EVENT_CS_CONNECTION_FAILURE: {'message': 'Event: Central Station Connection Failure', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_RECEIVER_DATABASE_CONNECTION: {'message': 'Event: Receiver Database Connection', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.EVENT_LICENSE_EXPIRATION: {'message': 'Event: License Expiration', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_CID_EVENT.OTHER_NO_READ_LOG: {'message': 'Other: No Read Log', 'dtype': LRR_DATA_TYPE.ZONE},
}

# Map of DSC event codes to human-readable text.
LRR_DSC_MAP = {
    LRR_DSC_EVENT.ZONE_EXPANDER_SUPERVISORY_ALARM: {'message': 'Zone Expander Supervisory Alarm', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.ZONE_EXPANDER_SUPERVISORY_RESTORE: {'message': 'Zone Expander Supervisory Restore', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.AUX_INPUT_ALARM: {'message': 'Auxillary Input Alarm', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.SPECIAL_CLOSING: {'message': 'Special Closing', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.CROSS_ZONE_POLICE_CODE_ALARM: {'message': 'Cross-zone Police Code Alarm', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.AUTOMATIC_CLOSING: {'message': 'Automatic Closing', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.ZONE_BYPASS: {'message': 'Zone Bypass', 'dtype': LRR_DATA_TYPE.ZONE},
    LRR_DSC_EVENT.REPORT_DSC_USER_LOG_EVENT: {'message': 'Report DSC User Log Event', 'dtype': LRR_DATA_TYPE.ZONE},
}

# Map of ADEMCO event codes to human-readable text.
LRR_ADEMCO_MAP = {

}

LRR_ALARMDECODER_MAP = {
    LRR_ALARMDECODER_EVENT.CUSTOM_PROG_MSG: 'Custom Programming Message',
    LRR_ALARMDECODER_EVENT.CUSTOM_PROG_KEY: 'Custom Programming Key'
}

# Map of UNKNOWN event codes to human-readable text.
LRR_UNKNOWN_MAP = {

}

# Map of event type codes to text maps.
LRR_TYPE_MAP = {
    LRR_EVENT_TYPE.CID: LRR_CID_MAP,
    LRR_EVENT_TYPE.DSC: LRR_DSC_MAP,
    LRR_EVENT_TYPE.ADEMCO: LRR_ADEMCO_MAP,
    LRR_EVENT_TYPE.ALARMDECODER: LRR_ALARMDECODER_MAP,
    LRR_EVENT_TYPE.UNKNOWN: LRR_UNKNOWN_MAP,
}

# LRR events that should be considered Fire events.
LRR_FIRE_EVENTS = [
    LRR_CID_EVENT.FIRE,
    LRR_CID_EVENT.FIRE_SMOKE,
    LRR_CID_EVENT.FIRE_COMBUSTION,
    LRR_CID_EVENT.FIRE_WATER_FLOW,
    LRR_CID_EVENT.FIRE_HEAT,
    LRR_CID_EVENT.FIRE_PULL_STATION,
    LRR_CID_EVENT.FIRE_DUCT,
    LRR_CID_EVENT.FIRE_FLAME,
    LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER              # HACK: Don't really like having this here
]

# LRR events that should be considered Alarm events.
LRR_ALARM_EVENTS = [
    LRR_CID_EVENT.BURGLARY,
    LRR_CID_EVENT.BURGLARY_PERIMETER,
    LRR_CID_EVENT.BURGLARY_INTERIOR,
    LRR_CID_EVENT.BURGLARY_AUX,
    LRR_CID_EVENT.BURGLARY_ENTRYEXIT,
    LRR_CID_EVENT.BURGLARY_DAYNIGHT,
    LRR_CID_EVENT.BURGLARY_OUTDOOR,
    LRR_CID_EVENT.ALARM_GENERAL,
    LRR_CID_EVENT.BURGLARY_SILENT,
    LRR_CID_EVENT.ALARM_AUX,
    LRR_CID_EVENT.ALARM_GAS_DETECTED,
    LRR_CID_EVENT.ALARM_REFRIDGERATION,
    LRR_CID_EVENT.ALARM_LOSS_OF_HEAT,
    LRR_CID_EVENT.ALARM_WATER_LEAKAGE,
    LRR_CID_EVENT.ALARM_LOW_BOTTLED_GAS_LEVEL,
    LRR_CID_EVENT.ALARM_HIGH_TEMP,
    LRR_CID_EVENT.ALARM_LOW_TEMP,
    LRR_CID_EVENT.ALARM_LOSS_OF_AIR_FLOW,
    LRR_CID_EVENT.ALARM_CARBON_MONOXIDE,
    LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER              # HACK: Don't really like having this here
]

# LRR events that should be considered Power events.
LRR_POWER_EVENTS = [
    LRR_CID_EVENT.TROUBLE_AC_LOSS
]

# LRR events that should be considered Bypass events.
LRR_BYPASS_EVENTS = [
    LRR_CID_EVENT.BYPASS_ZONE,
    LRR_CID_EVENT.BYPASS_24HOUR_ZONE,
    LRR_CID_EVENT.BYPASS_BURGLARY
]

# LRR events that should be considered Battery events.
LRR_BATTERY_EVENTS = [
    LRR_CID_EVENT.TROUBLE_LOW_BATTERY
]

# LRR events that should be considered Panic events.
LRR_PANIC_EVENTS = [
    LRR_CID_EVENT.MEDICAL,
    LRR_CID_EVENT.MEDICAL_PENDANT,
    LRR_CID_EVENT.MEDICAL_FAIL_TO_REPORT,
    LRR_CID_EVENT.PANIC,
    LRR_CID_EVENT.PANIC_DURESS,
    LRR_CID_EVENT.PANIC_SILENT,
    LRR_CID_EVENT.PANIC_AUDIBLE,
    LRR_CID_EVENT.PANIC_DURESS_ACCESS_GRANTED,
    LRR_CID_EVENT.PANIC_DURESS_EGRESS_GRANTED,
    LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER              # HACK: Don't really like having this here
]

# LRR events that should be considered Arm events.
LRR_ARM_EVENTS = [
    LRR_CID_EVENT.OPENCLOSE,
    LRR_CID_EVENT.OPENCLOSE_BY_USER,
    LRR_CID_EVENT.OPENCLOSE_GROUP,
    LRR_CID_EVENT.OPENCLOSE_AUTOMATIC,
    LRR_CID_EVENT.OPENCLOSE_REMOTE_ARMDISARM,
    LRR_CID_EVENT.OPENCLOSE_QUICK_ARM,
    LRR_CID_EVENT.OPENCLOSE_KEYSWITCH,
    LRR_CID_EVENT.OPENCLOSE_ARMED_STAY,                 # HACK: Not sure if I like having these in here.
    LRR_CID_EVENT.OPENCLOSE_KEYSWITCH_ARMED_STAY
]

# LRR events that should be considered Arm Stay events.
LRR_STAY_EVENTS = [
    LRR_CID_EVENT.OPENCLOSE_ARMED_STAY,
    LRR_CID_EVENT.OPENCLOSE_KEYSWITCH_ARMED_STAY
]
