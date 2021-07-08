import csv
import io


def read_parameter_csv(slack_client, csv_link):
    f = io.StringIO(slack_client.download_file(csv_link).decode('utf-8'))
    return list(csv.DictReader(f))

def get_parameters(code):

    def parse_parameters(cls):
        # this function is special:
        # it will be evaluated against the user's flowspec in a
        # separate Python session. It must not have global dependencies
        # (don't rely on top-level imports) and it must work both with
        # Py2 and Py3.
        from metaflow import Parameter
        params = []
        for var in dir(cls):
            if var[0] == '_':
                continue
            param = getattr(cls, var)
            if isinstance(param, Parameter):
                params.append({'name': param.name,
                               'help': param.kwargs.get('help', ''),
                               'default': param.kwargs.get('default'),
                               'required': param.kwargs.get('required', False),
                               'external_artifact': param.external_artifact})
        return params

    return code.flowspec_apply(parse_parameters)
