import os
import yaml
from typing import Dict

from OCR.utilities.dir_helper import is_file_or_dir_exist

def convert_dict_to_config_yaml(kv_dict: str, out_file: str) -> Dict:
    """
    Convert Python dictionary to the yaml configuration file.
    """
    def tuple_representer(dumper, data):
        return dumper.represent_sequence('!!python/tuple', data)

    yaml.add_representer(tuple, tuple_representer)

    # convert python dict to yaml file
    with open(out_file, 'w') as file:
        yaml.dump(kv_dict, file, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    # CAUTION: Update out_file before running
    out_file = "../config/config.yaml"

    kv_dict = {
    "a": {
        "TYPE_OF_REPORT": (2, 37, 522, 61),
    },
    "b": {
        "OFS_COMPANY_ID": (2, 70, 140, 92),
        "EMPLOYER NAME": (140, 70, 522, 92),
        "ADDRESS": (4, 93, 257, 117),
        "CITY_TOWN": (257, 93, 409, 117),
        "STATE": (409, 93, 448, 117),
        "ZIPCODE": (448, 93, 522, 117),
    },
    "d": {
        "EIN": (2, 173, 522, 193),
    },
    "ef": {
        "SECTION_E_AND_F": (2, 192, 502, 280),
    },
    # "f": {
    #     "DESIGNATION": (2, 215, 522, 280),
    # },
    "g": {
        "NAICS": (2, 280, 522, 297),
    },
    "h": {
        "TABLE": (154, 430, 522, 548),
    },
    "i": {
        "PERIOD": (2, 548, 522, 556),
    },
    "j": {
        "COMMENT": (2, 566, 522, 679),
    },
    "k": {
        "OFS_COMPANY_ID": (8, 61, 153, 83),
        "EMPLOYER NAME": (134, 62, 516, 83),
        "ADDRESS": (8, 83, 248, 117),
        "CITY_TOWN": (248, 83, 398, 118),
        "STATE": (397, 84, 437, 118),
        "ZIPCODE": (436, 84, 515, 118),
        "COMMENTS": (8, 128, 514, 452),
        "DATE_OF_CERTIFICATION": (8, 494, 514, 521),
        "NAME_OF_OFFICAL": (8, 532, 262, 565),
        "TITLE_OF_OFFICAL": (262, 532, 515, 565),
        "EMAIL_OF_OFFICAL": (8, 565, 262, 600),
        "TELEPHONE_OF_OFFICAL": (262, 566, 515, 600),
        "NAME_OF_POC": (8, 610, 262, 643),
        "TITLE_AND_EMPLOYER_OF_POC": (263, 610, 501, 642),
        "EMAIL_OF_POC": (8, 610, 262, 642),
        "TELEPHONE_OF_POC": (262, 644, 501, 669),
    },
}

    
    convert_dict_to_config_yaml(kv_dict, out_file)
    