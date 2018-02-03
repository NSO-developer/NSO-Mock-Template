import subprocess
import os
import re
import ncs

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
        """Generates ncs_cli string for given strings and variables.

        """
        return (template + " " + self._make_ncs_list(variables))

    def _open_ncs_cli(self, ncs_cli):
        """Call bash script to execute commands in ncs_cli.

        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        subprocess.call('sh %s/shell/ncs_cli_dry_run.sh "%s"' % (dir_path, ncs_cli), shell=True)
        return True

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

    def apply(self, template, variables):
        """Mock method for the ncs.application.Template.apply() method.

        This method enables us to replace the apply() method to call our
        template module via ncs_cli dryrun rather than the service itself.

         """
        cli_string = self._make_ncs_cli(template, variables)
        self._open_ncs_cli(cli_string)
        result = self._collate_results(self._get_results())
        return result

########## End of Monkey Template ############

class MonkeyResult(object):
    def __init__(self, result):
        self.result = self._parse_result(result)

    def _parse_result(self, result):
        """Parse the result string into dict.

        This function seeks to mimic ncs.maagic expected API for future dry-run.

        Input:
            result (str): ncs_cli commit dry-run string output

        Returns:
            dict: { "native": { "devices":[{'name':device, 'data': native}] } }

        """
        structure = { "native": { "devices":[] } }
        devices = structure["native"]["devices"]
        pairs = re.findall(r"device {(.*?)}", result, re.DOTALL)
        for device in pairs:
            lines =  device.split('\n')
            name = lines[1].split('name ')[1]
            data = lines[2:][0].split('data ')[1]
            for line in lines[2:][1:-1]:
                data += ('\n' + line)
            devices.append({"name":name, "data":data})
        return structure


def apply_nso_template(service, template, variables):
    """Function to simplify the application of NSO Templates.

    Inputs:
        service: ncs service object or dummy placeholder
        template (str): name of the template to apply
        variables (ncs.template.Variables): Variable Key-Value Pairs to apply

    Returns:
        Output from template.apply()

        When running the MonkeyTEmplate this will be the ncs_cli output.
    """
    template_obj = ncs.template.Template(service)
    template_vars = dict_to_ncs_vars(variables)
    return template_obj.apply(template, template_vars)

def dict_to_ncs_vars(dictionary):
    """Function that translates a dictionary into ncs Variables object.

    Inputs:
        dictionary (dict): Flat dictionary of template variable Key-Value pairs

    Returns:
        ncs.template.Variables
    """
    service_variables = ncs.template.Variables()
    for key, value in dictionary.iteritems():
        if type(value) is not str and type(value) is not int:
            raise TypeError(value)
        service_variables.add(key, value)
    return service_variables
