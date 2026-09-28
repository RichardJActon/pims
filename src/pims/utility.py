import typing
from typing import (
    Dict,
    Any,
)
from flask import (
    make_response,
    Response,
)

from werkzeug.datastructures import ImmutableMultiDict
from bson.json_util import dumps
from bson.raw_bson import RawBSONDocument

def jsonify(data: RawBSONDocument) -> Response:
    """
    This is a function which deals with the bson structures
    specifically ObjectID which can't auto convert to json 
    and will make a flask response object from it.
    
    :param data: a RawBSONDocument object, such as those returned by a mongodb query with pymongo
    :type data: RawBSONDocument
    :return: A flask response
    :rtype: Response
    """
    response: Response = make_response(dumps(data))
    response.content_type = 'application/json'
    return response

def args_to_dict(args: ImmutableMultiDict) -> Dict[str, Any]:
# def args_to_dict(args) -> Dict[str, Any]:
    """
    Converts Flask Request Arguments to a dictionary
    From the Flask Request Class:
    
    args
        The parsed URL parameters (the part in the URL after the question
        mark).

        By default an
        :class:`~werkzeug.datastructures.ImmutableMultiDict`
        is returned from this function.  This can be changed by setting
        :attr:`parameter_storage_class` to a different type.  This might
        be necessary if the order of the form data is important.

        .. versionchanged:: 2.3
            Invalid bytes remain percent encoded.
            
    :param args:
    :type args: ImmutableMultiDict
    :return:
    :rtype: dict

    :Example:
        >>> from werkzeug.datastructures import MultiDict, ImmutableMultiDict
        >>> x = ImmutableMultiDict(MultiDict([('a', 'b'), ('a', 'c')]))
        >>> args_to_dict(x)
        {'a': 'b'}
    """
    form = {}

    for key in args.keys():
        if key.endswith("[]"):
            form[key[:-2]] = args.getlist(key)
        else:
            form[key] = args.get(key)

    return form

