"""
Copyright 2018 Brandon Black

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
import pytest
from nso_template import ( MonkeyTemplate,
                           MonkeyResult,
                           dict_to_ncs_vars,
                           apply_nso_template,
                        )
import ncs


ncs.template.Template = MonkeyTemplate # Monkey patch
#These tests are setup for a specifc local enviroment
#This is leveraging a specific template as well
def test_make_ncs_list():
    monkey_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "netsim")
    assert monkey_template._make_ncs_list(service_variables) == "variable { name lab_gateway value netsim } "

def test_ncs_cli():
    monkey_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "netsim")
    assert monkey_template._make_ncs_cli("ipv6-acl", service_variables) == "ipv6-acl variable { name lab_gateway value netsim } "
    assert monkey_template._open_ncs_cli("ipv6-acl variable { name lab_gateway value netsim } ")
    cli_result = monkey_template._get_results()
    assert cli_result[0] == "Error: Python cb_action error. Unknown error (66): A variable value has not been assigned to: building_id, lab_id, lab_v6_p2p, lab_v6_prefix\n"

def test_proper_cli():
    monkey_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "netsim")
    service_variables.add('lab_id', "12342")
    service_variables.add('building_id', "test1")
    service_variables.add('lab_v6_p2p', "2001::2")
    service_variables.add('lab_v6_prefix', "2001::2/64")
    expected_cli = """
             ipv6 access-list ipv6-test1labID12342in
              permit ipv6 2001::2/64 any
              permit ipv6 2001::2 any
              deny ipv6 any any
             !
             ipv6 access-list ipv6-test1labID12342out
              deny ipv6 2001::2/64 any
              deny ipv6 2001::2 any
             !"""
    assert expected_cli in monkey_template.apply("ipv6-acl", service_variables)["native"]['devices'][0]["data"]

def test_dict_to_ncs_vars():
    # NSO Generic Template applicator helper tests
    variables ={'lab_id': "12342",
                'lab_gateway': "netsim",
                'building_id': "test1",
                'lab_v6_p2p': "2001::2",
                'lab_v6_prefix': "2001::2/64",
                }
    assert type(dict_to_ncs_vars(variables)) == ncs.template.Variables

def test_apply_nso_template():
    variables ={'lab_id': "12342",
                'lab_gateway': "netsim",
                'building_id': "test1",
                'lab_v6_p2p': "2001::2",
                'lab_v6_prefix': "2001::2/64",
                }
    expected_cli = """
             ipv6 access-list ipv6-test1labID12342in
              permit ipv6 2001::2/64 any
              permit ipv6 2001::2 any
              deny ipv6 any any
             !
             ipv6 access-list ipv6-test1labID12342out
              deny ipv6 2001::2/64 any
              deny ipv6 2001::2 any
             !"""
    assert expected_cli in apply_nso_template("service", "ipv6-acl", variables)["native"]['devices'][0]["data"]


def test_dict_to_ncs_vars_invalid():
    with pytest.raises(TypeError):
        bad_vars = {"Tuples": ("Are"), "Not": {"Cool": "Neither"},"Are": ["Lists"]}
        dict_to_ncs_vars(bad_vars)

## TEST MonkResult

def test_MonkeyResult():
    """Test that the parser for result parsing generates the expected struture.

    """
    result = """\
native {
        device {
            name dummy
            data cli commands a b c
            commands e f g
        }
    }"""
    mock_template =  MonkeyResult(result)

    parsed = mock_template.result
    #Validate data strucure
    assert type(parsed) == dict
    assert "native" in parsed
    assert "devices" in parsed["native"]
    assert list == type(parsed["native"]['devices'])
    assert "name" in parsed["native"]['devices'][0]
    assert "data" in parsed["native"]['devices'][0]

    # Validate data
    devices = []
    for device in parsed["native"]['devices']:
        devices.append(device['name'])
    assert "dummy" in devices
    assert parsed["native"]['devices'][0]["data"] == "cli commands a b c\n            commands e f g"

    result_cli = """\
native {
        device {
            name dummy
            data ipv6 access-list ipv6-test1labID12342in
                  permit ipv6 2001::2/64 any
                  permit ipv6 2001::2 any
                  deny ipv6 any any
                 !
                 ipv6 access-list ipv6-test1labID12342out
                  deny ipv6 2001::2/64 any
                  deny ipv6 2001::2 any
         }
     }"""

    expected_cli = """ipv6 access-list ipv6-test1labID12342in
                  permit ipv6 2001::2/64 any
                  permit ipv6 2001::2 any
                  deny ipv6 any any
                 !
                 ipv6 access-list ipv6-test1labID12342out
                  deny ipv6 2001::2/64 any
                  deny ipv6 2001::2 any"""
    parsed = MonkeyResult(result_cli).result
    print parsed["native"]['devices'][0]["data"]
    assert expected_cli == parsed["native"]['devices'][0]["data"]


def test_multiple_MonkeyResult_parse_result():
    """Test that the parser for result parsing generates the expected struture.

    With multiple devices insdie the output.
    """
    result = """\
native {
        device {
            name dummy
            data cli commands a b c
            commands e f g
        }
        device {
            name dummy2
            data cli commands h i j
            commands k l m
        }
    }"""
    mock_template =  MonkeyResult(result)
    parsed = mock_template._parse_result(result)
    devices = []
    for device in parsed["native"]['devices']:
        devices.append(device['name'])
    assert "dummy2" in devices
    assert parsed["native"]['devices'][0]["data"] == "cli commands a b c\n            commands e f g"
    assert parsed["native"]['devices'][1]["data"] == "cli commands h i j\n            commands k l m"
