import pytest
from nso_template import MonkeyTemplate, dict_to_ncs_vars, apply_nso_template
import ncs
ncs.template.Template = MonkeyTemplate # Monkey patch

#These tests are setup for a specifc local enviroment
#This is leveraging a specific template as well
def test_make_ncs_list():
    monkey_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "lab-gw0")
    assert monkey_template._make_ncs_list(service_variables) == "variable { name lab_gateway value lab-gw0 } "

def test_ncs_cli():
    monkey_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "lab-gw0")
    assert monkey_template._make_ncs_cli("ipv6-acl", service_variables) == "ipv6-acl variable { name lab_gateway value lab-gw0 } "
    assert monkey_template._open_ncs_cli("ipv6-acl variable { name lab_gateway value lab-gw0 } ")
    cli_result = monkey_template._get_results()
    assert cli_result[0] == "Error: Python cb_action error. Unknown error (66): A variable value has not been assigned to: building_id, lab_id, lab_v6_p2p, lab_v6_prefix\n"

def test_proper_cli():
    monkey_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "lab-gw0")
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
    assert expected_cli in monkey_template.apply("ipv6-acl", service_variables)

def test_dict_to_ncs_vars():
    # NSO Generic Template applicator helper tests
    variables ={'lab_id':"12342",
                'lab_gateway': "lab-gw0",
                'building_id': "test1",
                'lab_v6_p2p': "2001::2",
                'lab_v6_prefix': "2001::2/64",
                }
    assert type(dict_to_ncs_vars(variables)) == ncs.template.Variables

def test_apply_nso_template():
    variables ={'lab_id':"12342",
                'lab_gateway': "lab-gw0",
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
    assert expected_cli in apply_nso_template("service", "ipv6-acl", variables)

def test_test_dict_to_ncs_vars_invalid():
    with pytest.raises(TypeError):
        bad_vars = {"Tuples": ("Are"), "Not":{"Cool":"Neither"},"Are":["Lists"]}
        dict_to_ncs_vars(bad_vars)
