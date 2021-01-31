# Based on https://github.com/Ultimaker/Cura/blob/master/plugins/PostProcessingPlugin/scripts/FilamentChange.py

from ..Script import Script
import re

class FilamentChangeOnToolChange(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Filament Change On Tool Change",
            "key": "FilamentChangeOnToolChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "initial_retract":
                {
                    "label": "Initial Retraction",
                    "description": "Initial filament retraction distance. The filament will be retracted with this amount before moving the nozzle away from the ongoing print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 30.0
                },
                "later_retract":
                {
                    "label": "Later Retraction Distance",
                    "description": "Later filament retraction distance for removal. The filament will be retracted all the way out of the printer so that you can change the filament.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 300.0
                },
                "x_position":
                {
                    "label": "X Position",
                    "description": "Extruder X position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                },
                "y_position":
                {
                    "label": "Y Position",
                    "description": "Extruder Y position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                }
            }
        }"""

    def execute(self, data):
        """
        Inserts the filament change g-code when a tool switch occurs.
        The tool switch command is removed since it is currently assumed
        that only one tool is available.
        """
        initial_retract = self.getSettingValueByKey("initial_retract")
        later_retract = self.getSettingValueByKey("later_retract")
        x_pos = self.getSettingValueByKey("x_position")
        y_pos = self.getSettingValueByKey("y_position")

        filament_change = "M600"

        if initial_retract is not None and initial_retract > 0.:
            filament_change = filament_change + (" E%.2f" % -initial_retract)

        if later_retract is not None and later_retract > 0.:
            filament_change = filament_change + (" L%.2f" % -later_retract)
            filament_change = filament_change + (" U%.2f" % -later_retract)

        if x_pos is not None:
            filament_change = filament_change + (" X%.2f" % x_pos)

        if y_pos is not None:
            filament_change = filament_change + (" Y%.2f" % y_pos)

        filament_change = filament_change + (" Z%.2f" % 10)    
        filament_change = filament_change + " ; Generated by FilamentChangeOnToolChange plugin\n"

        tool_change_regex = re.compile("T[0-9]+")

        is_first_tool_change = True     # ignore the first tool change; replace all that follow
        for layer_number, layer in enumerate(data):
            layer_data = ""
            for line in layer.split("\n"):
                if tool_change_regex.match(line):
                    if not is_first_tool_change:
                        layer_data += filament_change
                    else:
                        is_first_tool_change = False
                        layer_data += line + "\n"
                else:
                    layer_data += line + "\n"
            data[layer_number] = layer_data

        return data
