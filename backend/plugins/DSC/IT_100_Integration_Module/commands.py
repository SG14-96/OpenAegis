IT100_COMMANDS = {
    "command": {
        "Poll": {
            "code": "000",
            "description": "Verifies the communication channel is active"
        },
        "Status Request": {
            "code": "001",
            "description": "Requests full zone, partition, and trouble status update"
        },
        "Labels Request": {
            "code": "002",
            "description": "Requests all programmable labels"
        },
        "Set Time and Date": {
            "code": "010",
            "description": "Sets the alarm system's time and date (format: hhmmMMDDYY)"
        },
        "Command Output Control": {
            "code": "020",
            "description": "Activates a selected command output (1-4) on a selected partition (1-8)"
        },
        "Partition Arm Control - Away": {
            "code": "030",
            "description": "Arms selected partition in Away mode (no zones bypassed)"
        },
        "Partition Arm Control - Stay": {
            "code": "031",
            "description": "Arms selected partition in Stay mode"
        },
        "Partition Arm Control - No Entry Delay": {
            "code": "032",
            "description": "Arms selected partition with no entry delay"
        },
        "Partition Arm Control - With Code": {
            "code": "033",
            "description": "Arms selected partition using a provided user code"
        },
        "Partition Disarm Control - With Code": {
            "code": "040",
            "description": "Disarms selected partition and silences any active alarms"
        },
        "Time Stamp Control": {
            "code": "055",
            "description": "Enables/disables an 8-digit timestamp prefix on all IT-100 commands"
        },
        "Time/Date Broadcast Control": {
            "code": "056",
            "description": "Enables/disables time/date broadcasts every 4 minutes"
        },
        "Temperature Broadcast Control": {
            "code": "057",
            "description": "Enables/disables indoor/outdoor temperature broadcasts every minute"
        },
        "Virtual Keypad Control": {
            "code": "058",
            "description": "Enables/disables virtual keypad functionality"
        },
        "Trigger Panic Alarm": {
            "code": "060",
            "description": "Emulates Fire (F), Ambulance (A), or Panic (P) keypad keys to trigger an instant alarm"
        },
        "Key Pressed (Virtual)": {
            "code": "070",
            "description": "Simulates a keypress on the keypad (numeric, function, arrow, break keys)"
        },
        "Baud Rate Change": {
            "code": "080",
            "description": "Changes the serial baud rate (0=9600, 1=19200, 2=38400, 3=57600, 4=115200)"
        },
        "Get Temperature Set Point": {
            "code": "095",
            "description": "Requests current thermostat set points from a connected Escort module"
        },
        "Temperature Change": {
            "code": "096",
            "description": "Changes thermostat cool or heat set point (increment, decrement, or set absolute value)"
        },
        "Save Temperature Setting": {
            "code": "097",
            "description": "Saves the temperature set point to the Escort module"
        },
        "Code Send": {
            "code": "200",
            "description": "Sends a 6-digit access code in response to a Code Required (900) prompt"
        },
    },
    "messages": {
        "Command Acknowledge": {
            "code": "500",
            "category": "General",
            "description": "Confirms a command was successfully received"
        },
        "Command Error": {
            "code": "501",
            "category": "General",
            "description": "Indicates a command was received with a bad checksum"
        },
        "System Error": {
            "code": "502",
            "category": "General",
            "description": "Indicates a system-level error; includes an error code"
        },
        "Time/Date Broadcast": {
            "code": "550",
            "category": "Time/Broadcast",
            "description": "Sends current system time every 4 minutes when broadcast is enabled"
        },
        "Ring Detected": {
            "code": "560",
            "category": "Time/Broadcast",
            "description": "Indicates the panel detected a ring on the phone line (requires ESCORT 5580TC)"
        },
        "Indoor Temperature Broadcast": {
            "code": "561",
            "category": "Time/Broadcast",
            "description": "Sends interior temperature and thermostat number every minute"
        },
        "Outdoor Temperature Broadcast": {
            "code": "562",
            "category": "Time/Broadcast",
            "description": "Sends exterior temperature and thermostat number every minute"
        },
        "Thermostat Set Points": {
            "code": "563",
            "category": "Time/Broadcast",
            "description": "Sends current cool and heat set points for a thermostat; response to 095, 096, or 097"
        },
        "Broadcast Labels": {
            "code": "570",
            "category": "Time/Broadcast",
            "description": "Sends all programmable labels; response to Labels Request (002)"
        },
        "Baud Rate Set": {
            "code": "580",
            "category": "Time/Broadcast",
            "description": "Confirms the new baud rate after a Baud Rate Change (080) command"
        },
        "Zone Alarm": {
            "code": "601",
            "category": "Zone Events",
            "description": "A zone and its associated partition have gone into alarm"
        },
        "Zone Alarm Restore": {
            "code": "602",
            "category": "Zone Events",
            "description": "A zone alarm and its associated partition have been restored"
        },
        "Zone Tamper": {
            "code": "603",
            "category": "Zone Events",
            "description": "A zone and its associated partition have a tamper condition"
        },
        "Zone Tamper Restore": {
            "code": "604",
            "category": "Zone Events",
            "description": "A zone tamper condition has been restored"
        },
        "Zone Fault": {
            "code": "605",
            "category": "Zone Events",
            "description": "A zone has a fault condition"
        },
        "Zone Fault Restore": {
            "code": "606",
            "category": "Zone Events",
            "description": "A zone fault condition has been restored"
        },
        "Zone Open": {
            "code": "609",
            "category": "Zone Events",
            "description": "General status - a zone is currently open"
        },
        "Zone Restored": {
            "code": "610",
            "category": "Zone Events",
            "description": "General status - a zone has been restored/closed"
        },
        "Duress Alarm": {
            "code": "620",
            "category": "Alarm/Key Events",
            "description": "A duress code was entered on a system keypad"
        },
        "[F] Key Alarm": {
            "code": "621",
            "category": "Alarm/Key Events",
            "description": "Fire key alarm has been activated"
        },
        "[F] Key Restoral": {
            "code": "622",
            "category": "Alarm/Key Events",
            "description": "Fire key alarm has been restored (sent automatically after alarm)"
        },
        "[A] Key Alarm": {
            "code": "623",
            "category": "Alarm/Key Events",
            "description": "Auxiliary key alarm has been activated"
        },
        "[A] Key Restoral": {
            "code": "624",
            "category": "Alarm/Key Events",
            "description": "Auxiliary key alarm has been restored"
        },
        "[P] Key Alarm": {
            "code": "625",
            "category": "Alarm/Key Events",
            "description": "Panic key alarm has been activated"
        },
        "[P] Key Restoral": {
            "code": "626",
            "category": "Alarm/Key Events",
            "description": "Panic key alarm has been restored"
        },
        "Auxiliary Input Alarm": {
            "code": "631",
            "category": "Alarm/Key Events",
            "description": "An auxiliary input alarm has been activated"
        },
        "Auxiliary Input Alarm Restored": {
            "code": "632",
            "category": "Alarm/Key Events",
            "description": "An auxiliary input alarm has been restored"
        },
        "Partition Ready": {
            "code": "650",
            "category": "Partition Status",
            "description": "Partition can be armed (all zones restored, no troubles)"
        },
        "Partition Not Ready": {
            "code": "651",
            "category": "Partition Status",
            "description": "Partition cannot be armed (zones open or trouble present)"
        },
        "Partition Armed - Descriptive Mode": {
            "code": "652",
            "category": "Partition Status",
            "description": "Partition is armed; includes mode: Away, Stay, Away No Delay, Stay No Delay"
        },
        "Partition Ready to Force Arm": {
            "code": "653",
            "category": "Partition Status",
            "description": "Partition is in ready-to-force-arm state"
        },
        "Partition In Alarm": {
            "code": "654",
            "category": "Partition Status",
            "description": "Partition is currently in alarm"
        },
        "Partition Disarmed": {
            "code": "655",
            "category": "Partition Status",
            "description": "Partition has been disarmed"
        },
        "Exit Delay in Progress": {
            "code": "656",
            "category": "Partition Status",
            "description": "Partition is in exit delay"
        },
        "Entry Delay in Progress": {
            "code": "657",
            "category": "Partition Status",
            "description": "Partition is in entry delay"
        },
        "Keypad Lock-out": {
            "code": "658",
            "category": "Partition Status",
            "description": "Partition is locked out due to too many failed code attempts"
        },
        "Keypad Blanking": {
            "code": "659",
            "category": "Partition Status",
            "description": "Keypad blanking has occurred on a partition"
        },
        "Command Output In Progress": {
            "code": "660",
            "category": "Partition Status",
            "description": "Partition is in command output mode"
        },
        "Invalid Access Code": {
            "code": "670",
            "category": "Partition Status",
            "description": "An invalid access code was entered (only reported if response comes within 1 second)"
        },
        "Function Not Available": {
            "code": "671",
            "category": "Partition Status",
            "description": "The requested function is not available at this time (only reported if no response within 1 second)"
        },
        "Fail to Arm": {
            "code": "672",
            "category": "Partition Status",
            "description": "A partition failed to arm"
        },
        "Partition Busy": {
            "code": "673",
            "category": "Partition Status",
            "description": "Partition is busy and cannot process the request"
        },
        "User Closing": {
            "code": "700",
            "category": "Opening/Closing Events",
            "description": "Partition armed by a user; sent at end of exit delay; includes user code"
        },
        "Special Closing": {
            "code": "701",
            "category": "Opening/Closing Events",
            "description": "Partition armed via Quick Arm, Auto Arm, Keyswitch, DLS software, or Wireless Key"
        },
        "Partial Closing": {
            "code": "702",
            "category": "Opening/Closing Events",
            "description": "Partition armed with one or more zones bypassed"
        },
        "User Opening": {
            "code": "750",
            "category": "Opening/Closing Events",
            "description": "Partition disarmed by a user; includes user code"
        },
        "Special Opening": {
            "code": "751",
            "category": "Opening/Closing Events",
            "description": "Partition disarmed via Keyswitch, DLS software, or Wireless Key"
        },
        "Panel Battery Trouble": {
            "code": "800",
            "category": "Trouble/System Events",
            "description": "Panel has a low battery"
        },
        "Panel Battery Trouble Restore": {
            "code": "801",
            "category": "Trouble/System Events",
            "description": "Panel low battery condition has been restored"
        },
        "Panel AC Trouble": {
            "code": "802",
            "category": "Trouble/System Events",
            "description": "AC power to the panel has been removed"
        },
        "Panel AC Restore": {
            "code": "803",
            "category": "Trouble/System Events",
            "description": "AC power to the panel has been restored"
        },
        "System Bell Trouble": {
            "code": "806",
            "category": "Trouble/System Events",
            "description": "Open circuit detected across bell terminals"
        },
        "System Bell Trouble Restoral": {
            "code": "807",
            "category": "Trouble/System Events",
            "description": "Bell trouble has been restored"
        },
        "TLM Line 1 Trouble": {
            "code": "810",
            "category": "Trouble/System Events",
            "description": "Phone line 1 is open or shorted"
        },
        "TLM Line 1 Trouble Restored": {
            "code": "811",
            "category": "Trouble/System Events",
            "description": "Phone line 1 trouble has been restored"
        },
        "TLM Line 2 Trouble": {
            "code": "812",
            "category": "Trouble/System Events",
            "description": "Phone line 2 is open or shorted"
        },
        "TLM Line 2 Trouble Restored": {
            "code": "813",
            "category": "Trouble/System Events",
            "description": "Phone line 2 trouble has been restored"
        },
        "FTC Trouble": {
            "code": "814",
            "category": "Trouble/System Events",
            "description": "Panel failed to communicate with the monitoring station"
        },
        "Buffer Near Full": {
            "code": "816",
            "category": "Trouble/System Events",
            "description": "Panel event buffer is 75\\% full since last DLS upload"
        },
        "General Device Low Battery": {
            "code": "821",
            "category": "Trouble/System Events",
            "description": "A wireless zone has a low battery"
        },
        "General Device Low Battery Restore": {
            "code": "822",
            "category": "Trouble/System Events",
            "description": "Wireless zone low battery condition has been restored"
        },
        "Wireless Key Low Battery Trouble": {
            "code": "825",
            "category": "Trouble/System Events",
            "description": "A wireless key has a low battery condition"
        },
        "Wireless Key Low Battery Restore": {
            "code": "826",
            "category": "Trouble/System Events",
            "description": "Wireless key low battery condition has been restored"
        },
        "Handheld Keypad Low Battery Trouble": {
            "code": "827",
            "category": "Trouble/System Events",
            "description": "A handheld keypad has a low battery condition"
        },
        "Handheld Keypad Low Battery Restore": {
            "code": "828",
            "category": "Trouble/System Events",
            "description": "Handheld keypad low battery condition has been restored"
        },
        "General System Tamper": {
            "code": "829",
            "category": "Trouble/System Events",
            "description": "A tamper has occurred on an alarm system module"
        },
        "General System Tamper Restore": {
            "code": "830",
            "category": "Trouble/System Events",
            "description": "Module tamper condition has been restored"
        },
        "Home Automation Trouble": {
            "code": "831",
            "category": "Trouble/System Events",
            "description": "Escort 5580 module trouble detected"
        },
        "Home Automation Trouble Restore": {
            "code": "832",
            "category": "Trouble/System Events",
            "description": "Escort 5580 module trouble has been restored"
        },
        "Trouble Status - LED ON": {
            "code": "840",
            "category": "Trouble/System Events",
            "description": "General trouble is present (trouble LED is on) for the specified partition"
        },
        "Trouble Status - LED OFF": {
            "code": "841",
            "category": "Trouble/System Events",
            "description": "No troubles present (trouble LED is off) for the specified partition"
        },
        "Fire Trouble Alarm": {
            "code": "842",
            "category": "Trouble/System Events",
            "description": "A fire trouble condition has been detected"
        },
        "Fire Trouble Alarm Restored": {
            "code": "843",
            "category": "Trouble/System Events",
            "description": "Fire trouble condition has been restored"
        },
        "Code Required": {
            "code": "900",
            "category": "Virtual Keypad/UI",
            "description": "An access code must be entered; application must respond with Code Send (200)"
        },
        "LCD Update": {
            "code": "901",
            "category": "Virtual Keypad/UI",
            "description": "Sent whenever the IT-100 menu text changes; includes line, column, character count, and text"
        },
        "LCD Cursor": {
            "code": "902",
            "category": "Virtual Keypad/UI",
            "description": "Sent whenever the cursor position changes; includes type (off/underline/block), line, and column"
        },
        "LED Status": {
            "code": "903",
            "category": "Virtual Keypad/UI",
            "description": "Reports the on/off/flashing state of one of 9 keypad LEDs (Ready, Armed, Memory, Bypass, Trouble, Program, Fire, Backlight, AC)"
        },
        "Beep Status": {
            "code": "904",
            "category": "Virtual Keypad/UI",
            "description": "Reports beep duration (0-255 seconds)"
        },
        "Tone Status": {
            "code": "905",
            "category": "Virtual Keypad/UI",
            "description": "Reports constant tone control, number of beeps, and interval"
        },
        "Buzzer Status": {
            "code": "906",
            "category": "Virtual Keypad/UI",
            "description": "Reports buzzer duration (0-255 seconds)"
        },
        "Door Chime Status": {
            "code": "907",
            "category": "Virtual Keypad/UI",
            "description": "Sent when door chime is active on the current partition"
        },
        "Software Version": {
            "code": "908",
            "category": "Virtual Keypad/UI",
            "description": "Sent on power-up and in response to Status Request (001); includes version, sub-version"
        },
    },
    "error_codes": {
        "Keybus Busy - Installer Mode": {"code": "017"},
        "Requested Partition is Out of Range": {"code": "021"},
        "Partition is Not Armed": {"code": "023"},
        "Partition is Not Ready to Arm": {"code": "024"},
        "User Code Not Required": {"code": "026"},
        "Virtual Keypad is Disabled": {"code": "028"},
        "Not a Valid Parameter": {"code": "029"},
        "Keypad Does Not Come Out of Blank Mode": {"code": "030"},
        "IT-100 is Already in Thermostat Menu": {"code": "031"},
        "IT-100 is Not in Thermostat Menu": {"code": "032"},
        "No Response from Thermostat or Escort Module": {"code": "033"},
    }
}