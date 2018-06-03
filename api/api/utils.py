def jsonify(value):
    if type(value) == dict:
        return json_dict(value)
    elif type(value) == list:
        return json_list(value)
    elif type(value) == object:
        return json_object(value)
    else:
        raise TypeError("jsonify only accepts list or dict arguments")


def json_dict(target: dict) -> dict:
    output = {}
    for k, v in target.items():
        if isinstance(v, list):
            output[k] = json_list(v)
        elif isinstance(v, dict):
            output[k] = json_dict(v)
        elif isinstance(v, object):
            output[k] = json_object(v)
        else:
            output[k] = str(v)
    return output


def json_list(target: list) -> list:
    output = []
    for i in target:
        if isinstance(i, list):
            output.append(json_list(i))
        elif isinstance(i, dict):
            output.append(json_dict(i))
        elif isinstance(i, object):
            output.append(json_object(i))
        else:
            output.append(str(i))
    return output


def json_object(target: object):
    if hasattr(target, '__dict__'):
        return json_dict(target.__dict__)
    else:
        return str(target)
