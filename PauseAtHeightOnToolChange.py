# Based on https://github.com/Ultimaker/Cura/blob/master/plugins/PostProcessingPlugin/scripts/PauseAtHeight.py

from ..Script import Script

from UM.Application import Application
from UM.Logger import Logger

from typing import List, Tuple
import re

class PauseAtHeightOnToolChange(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self) -> str:
        return """{
            "name": "Pause At Height On Tool Change",
            "key": "PauseAtHeightOnToolChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_method":
                {
                    "label": "Method",
                    "description": "The method or gcode command to use for pausing.",
                    "type": "enum",
                    "options": {"marlin": "Marlin (M0)", "griffin": "Griffin (M0, firmware retract)", "bq": "BQ (M25)", "reprap": "RepRap (M226)", "repetier": "Repetier (@pause)"},
                    "default_value": "marlin",
                    "value": "\\\"griffin\\\" if machine_gcode_flavor==\\\"Griffin\\\" else \\\"reprap\\\" if machine_gcode_flavor==\\\"RepRap (RepRap)\\\" else \\\"repetier\\\" if machine_gcode_flavor==\\\"Repetier\\\" else \\\"bq\\\" if \\\"BQ\\\" in machine_name or \\\"Flying Bear Ghost 4S\\\" in machine_name  else \\\"marlin\\\""
                },                    
                "disarm_timeout":
                {
                    "label": "Disarm timeout",
                    "description": "After this time steppers are going to disarm (meaning that they can easily lose their positions). Set this to 0 if you don't want to set any duration.",
                    "type": "int",
                    "value": "0",
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "1800",
                    "unit": "s"
                },
                "head_park_x":
                {
                    "label": "Park Print Head X",
                    "description": "What X location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "head_park_y":
                {
                    "label": "Park Print Head Y",
                    "description": "What Y location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "head_move_z":
                {
                    "label": "Head move Z",
                    "description": "The Height of Z-axis retraction before parking.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 15.0,
                    "enabled": "pause_method == \\\"repetier\\\""
                },
                "retraction_amount":
                {
                    "label": "Initial Retraction",
                    "description": "How much filament must be retracted at pause.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "unload_amount":
                {
                    "label": "Unload Amount",
                    "description": "Once paused, amount of filament to be retracted (e.g. length of Bowden tube).",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 300,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "load_amount":
                {
                    "label": "Load Amount",
                    "description": "Once filament has been loaded, amount of filament to be extruded (e.g. length of Bowden tube). Will pause before continuing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 300,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "retraction_speed":
                {
                    "label": "Retraction Speed",
                    "description": "How fast to retract the filament.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 25,
                    "enabled": "pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "extrude_amount":
                {
                    "label": "Extrude Amount",
                    "description": "How much filament should be extruded after pause. This is needed when doing a material change on Ultimaker2's to compensate for the retraction after the change. In that case 128+ is recommended.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "extrude_speed":
                {
                    "label": "Extrude Speed",
                    "description": "How fast to extrude the material after pause.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 3.3333,
                    "enabled": "pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "standby_temperature":
                {
                    "label": "Standby Temperature",
                    "description": "Change the temperature during the pause.",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 0,
                    "enabled": "pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "display_text":
                {
                    "label": "Display Text",
                    "description": "Text that should appear on the display while paused. If left empty, there will not be any message.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "pause_method != \\\"repetier\\\""
                },
                "machine_name":
                {
                    "label": "Machine Type",
                    "description": "The name of your 3D printer model. This setting is controlled by the script and will not be visible.",
                    "default_value": "Unknown",
                    "type": "str",
                    "enabled": false
                },
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": false
                },
                "custom_gcode_before_pause":
                {
                    "label": "G-code Before Pause",
                    "description": "Any custom g-code to run before the pause, for example, M300 S440 P200 to beep.",
                    "type": "str",
                    "default_value": ""
                },
                "custom_gcode_after_pause":
                {
                    "label": "G-code After Pause",
                    "description": "Any custom g-code to run after the pause, for example, M300 S440 P200 to beep.",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""

    ##  Copy machine name and gcode flavor from global stack so we can use their value in the script stack
    def initialize(self) -> None:
        super().initialize()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None or self._instance is None:
            return

        for key in ["machine_name", "machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", global_container_stack.getProperty(key, "value"))

    ##  Get the X and Y values after the pause.
    def getNextXY(self, layer: str) -> Tuple[float, float]:
        """Get the X and Y values for a layer (will be used to get X and Y of the position after the pause)."""
        lines = layer.split("\n")
        for line in lines:
            if line.startswith(("G0", "G1", "G2", "G3")):
                if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                    x = self.getValue(line, "X")
                    y = self.getValue(line, "Y")
                    return x, y
        return 0, 0

    def execute(self, data: List[str]) -> List[str]:
        """Inserts the pause commands."""
        disarm_timeout = self.getSettingValueByKey("disarm_timeout")
        retraction_amount = self.getSettingValueByKey("retraction_amount")
        unload_amount = self.getSettingValueByKey("unload_amount")
        load_amount = self.getSettingValueByKey("load_amount")
        retraction_speed = self.getSettingValueByKey("retraction_speed")
        extrude_amount = self.getSettingValueByKey("extrude_amount")
        extrude_speed = self.getSettingValueByKey("extrude_speed")
        park_x = self.getSettingValueByKey("head_park_x")
        park_y = self.getSettingValueByKey("head_park_y")
        move_z = self.getSettingValueByKey("head_move_z")
        layers_started = False
        standby_temperature = self.getSettingValueByKey("standby_temperature")
        firmware_retract = Application.getInstance().getGlobalContainerStack().getProperty("machine_firmware_retract", "value")
        control_temperatures = Application.getInstance().getGlobalContainerStack().getProperty("machine_nozzle_temp_enabled", "value")
        initial_layer_height = Application.getInstance().getGlobalContainerStack().getProperty("layer_height_0", "value")
        display_text = self.getSettingValueByKey("display_text")
        gcode_before = self.getSettingValueByKey("custom_gcode_before_pause")
        gcode_after = self.getSettingValueByKey("custom_gcode_after_pause")
        is_first_tool_change = True     # ignore the first tool change; replace all that follow

        pause_method = self.getSettingValueByKey("pause_method")
        pause_command = {
            "marlin": self.putValue(M = 0),
            "griffin": self.putValue(M = 0),
            "bq": self.putValue(M = 25),
            "reprap": self.putValue(M = 226),
            "repetier": self.putValue("@pause now change filament and press continue printing")
        }[pause_method]

        current_z = 0

        for index, layer in enumerate(data):
            lines = layer.split("\n")
            layer_data = ""

            # Scroll each line of instruction for each layer in the G-code
            for line in lines:
                # If a Z instruction is in the line, read the current Z
                if self.getValue(line, "Z") is not None:
                    current_z = self.getValue(line, "Z")

                if line.startswith("T"):
                    if not is_first_tool_change:                        
                        halt_gcode = ";TYPE:CUSTOM\n"
                        halt_gcode += ";added code by post processing\n"
                        halt_gcode += ";script: PauseAtHeightOnToolChange.py\n"
   
                        if pause_method == "repetier":
                            #Retraction
                            halt_gcode += self.putValue(M = 83) + " ; switch to relative E values for any needed retraction\n"
                            if retraction_amount != 0:
                                halt_gcode += self.putValue(G = 1, E = retraction_amount, F = 6000) + "\n"

                            #Move the head away
                            halt_gcode += self.putValue(G = 1, Z = current_z + 1, F = 300) + " ; move up a millimeter to get out of the way\n"
                            halt_gcode += self.putValue(G = 1, X = park_x, Y = park_y, F = 9000) + "\n"
                            if current_z < move_z:
                                halt_gcode += self.putValue(G = 1, Z = current_z + move_z, F = 300) + "\n"

                            #Disable the E steppers
                            halt_gcode += self.putValue(M = 84, E = 0) + "\n"

                        elif pause_method != "griffin":
                            # Retraction
                            halt_gcode += self.putValue(M = 83) + " ; switch to relative E values for any needed retraction\n"
                            if retraction_amount != 0:
                                if firmware_retract: #Can't set the distance directly to what the user wants. We have to choose ourselves.
                                    retraction_count = 1 if control_temperatures else 3 #Retract more if we don't control the temperature.
                                    for i in range(retraction_count):
                                        halt_gcode += self.putValue(G = 10) + "\n"
                                else:
                                    halt_gcode += self.putValue(G = 1, E = -retraction_amount, F = retraction_speed * 60) + "\n"

                            # Move the head away
                            halt_gcode += self.putValue(G = 1, Z = current_z + 1, F = 300) + " ; move up a millimeter to get out of the way\n"

                            # This line should be ok
                            halt_gcode += self.putValue(G = 1, X = park_x, Y = park_y, F = 9000) + "\n"

                            if current_z < 15:
                                halt_gcode += self.putValue(G = 1, Z = 15, F = 9000) + " ; too close to bed--move to at least 15mm\n"

                            if control_temperatures:
                                # Set extruder standby temperature
                                halt_gcode += self.putValue(M = 104, S = standby_temperature) + " ; standby temperature\n"

                        if display_text:
                            halt_gcode += "M117 " + display_text + "\n"

                        # Set the disarm timeout
                        if disarm_timeout > 0:
                            halt_gcode += self.putValue(M = 18, S = disarm_timeout) + " ; Set the disarm timeout\n"

                        # Set a custom GCODE section before pause
                        if gcode_before:
                            halt_gcode += gcode_before + "\n"

                        tmp_unload_amount = unload_amount
                        if tmp_unload_amount is not None:
                            while tmp_unload_amount > 0:
                                if tmp_unload_amount - 200 <= 0:
                                    halt_gcode += self.putValue(G = 1, E = -tmp_unload_amount, F = retraction_speed * 60) + "\n"
                                else:
                                    halt_gcode += self.putValue(G = 1, E = -200, F = retraction_speed * 60) + "\n"
                                tmp_unload_amount -= 200

                        # Wait till the user continues printing
                        halt_gcode += pause_command + " ; Do the actual pause\n"

                        tmp_load_amount = load_amount
                        if tmp_load_amount is not None:
                            while tmp_load_amount > 0:
                                if tmp_load_amount - 100 <= 0:
                                    halt_gcode += self.putValue(G = 1, E = tmp_load_amount, F = retraction_speed * 60) + "\n"
                                else:
                                    halt_gcode += self.putValue(G = 1, E = 100, F = retraction_speed * 60) + "\n"
                                tmp_load_amount -= 100

                        # Wait till the user continues printing
                        halt_gcode += pause_command + " ; Do the another pause\n"

                        # Set a custom GCODE section after pause
                        if gcode_after:
                            halt_gcode += gcode_after + "\n"

                        halt_gcode += self.putValue(M = 82) + "\n"    
                        layer_data += halt_gcode
                    else:
                        is_first_tool_change = False
                        layer_data += line + "\n"
                else:
                    layer_data += line + "\n"
            data[index] = layer_data
        return data
