import sys
import subprocess
import os

class MonkeyTemplate(object):
    """Mock ncs.template.Template object to run a dry-run.

    This object replaces the ncs template object with a monkey patch.

    This new object replaces the apply() function to not aply via maapi.
    Instead the apply function subprocess the variables and templates,
    to the template apply action module via ncs_cli and runs a dry-run.
    This dry-run is saves to /tmp/template_data.txt,
    Then read by python, removed, and parsed into native CLI.
    """
    def __init__(self, trans):
        pass

    def _make_ncs_list(self, variables):
        """Convert inputed ncs.template.Variables object to a ncs_cli string.

        """
        cli_string = ""
        for key, value in variables:
            cli_string += "variable { name %s value %s } " % (key, value[1:-1])
        return cli_string

    def _make_ncs_cli(self, template, variables):
        return (template + " " + self._make_ncs_list(variables) )

    def _open_ncs_cli(self, ncs_cli):
        """Call bash script to execute commands in ncs_cli.

        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        subprocess.call('sh %s/shell/ncs_cli_dry_run.sh "%s"' % (dir_path ,ncs_cli), shell=True)
        return True

    def apply(self, template, variables):
        """Mock method for the ncs.application.Template.apply() method.

        This method enables us to replace the apply() method to call our
        template module via ncs_cli dryrun rather than the service itself.

         """
        cli_string = self._make_ncs_cli(template, variables)
        self._open_ncs_cli(cli_string)
        result = self._collate_results(self._get_results())
        return result

    def _get_results(self):
        """Gets the CLI output in /tmp/ncs_template.txt then removes it.

        """
        with open('/tmp/template_data.txt', 'r') as infile:
            os.remove('/tmp/template_data.txt' )
            return infile.readlines()

    def _collate_results(self, output):
        """Collate the output list into a single string.

        """
        result = ""
        for line in output:
            result += line
        return result


if __name__ == "__main__":
    import ncs

    #These tests are setup for a specifc local enviroment
    #This is leveraging a specific template as well
    #TODO Develop generic test scripts for clean NSO Enviroment
    assert MonkeyTemplate("service")
    mock_template = MonkeyTemplate("service")
    service_variables = ncs.template.Variables()
    service_variables.add('lab_gateway', "lab-gw0")
    assert mock_template._make_ncs_list(service_variables) == "variable { name lab_gateway value lab-gw0 } "
    assert mock_template._make_ncs_cli("ipv6-acl", service_variables) == "ipv6-acl variable { name lab_gateway value lab-gw0 } "
    assert mock_template._open_ncs_cli("ipv6-acl variable { name lab_gateway value lab-gw0 } ") == True
    cli_result = mock_template._get_results()
    assert cli_result[0] == "Error: Python cb_action error. Unknown error (66): A variable value has not been assigned to: building_id, lab_id, lab_v6_p2p, lab_v6_prefix\n"
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
    assert expected_cli in mock_template.apply("ipv6-acl", service_variables)
