import json
import functools
import logging
from collections import Iterable

from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger('django.request')

DEFAULT_DEBUG = getattr(settings, 'JSONRESPONSE_DEFAULT_DEBUG', False)
CALLBACK_NAME = getattr(settings, 'JSONRESPONSE_CALLBACK_NAME', 'callback')

class to_json(object):
    """
    Wrap view functions to render python native and custom 
    objects to json

    >>> from django.test.client import RequestFactory
    >>> requests = RequestFactory()

    Simple wrap returning data into json

    >>> @to_json('plain')
    ... def hello(request):
    ...    return dict(hello='world')

    >>> resp = hello(requests.get('/hello/'))
    >>> print resp.status_code
    200
    >>> print resp.content
    {"hello": "world"}
    
    Result can be wraped in some api manier

    >>> @to_json('api')
    ... def goodbye(request):
    ...    return dict(good='bye')
    >>> resp = goodbye(requests.get('/goodbye', {'debug': 1}))
    >>> print resp.status_code
    200
    >>> print resp.content
    {
        "data": {
            "good": "bye"
        }, 
        "err": 0
    }

    Automaticaly error handling

    >>> @to_json('api')
    ... def error(request):
    ...    raise Exception('Wooot!??')

    >>> resp = error(requests.get('/error', {'debug': 1}))
    >>> print resp.status_code
    500
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {            
        "err_class": "Exception",
        "err_desc": "Wooot!??",
        "data": null,
        "err": 1
    }

    >>> from django.core.exceptions import ObjectDoesNotExist
    >>> @to_json('api')
    ... def error_404(request):
    ...     raise ObjectDoesNotExist('Not found')

    >>> resp = error_404(requests.get('/error', {'debug': 1}))
    >>> print resp.status_code
    404
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {
        "err_class": "django.core.exceptions.ObjectDoesNotExist",
        "err_desc": "Not found",
        "data": null,
        "err": 1
    }


    You can serialize not only pure python data types.
    Implement `serialize` method on toplevel object or 
    each element of toplevel array.

    >>> class User(object):
    ...     def __init__(self, name, age):
    ...         self.name = name
    ...         self.age = age
    ... 
    ...     def serialize(self, request):
    ...         if request.GET.get('with_age', False):
    ...             return dict(name=self.name, age=self.age)
    ...         else:
    ...             return dict(name=self.name)
    
    >>> @to_json('objects')
    ... def users(request):
    ...    return [User('Bob', 10), User('Anna', 12)]

    >>> resp = users(requests.get('users', { 'debug': 1 }))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {
        "data": [
            {
                "name": "Bob"
            }, 
            {
                "name": "Anna"
            }
        ], 
        "err": 0
    }

    You can pass extra args for serialization:

    >>> resp = users(requests.get('users', 
    ...     { 'debug':1, 'with_age':1 }))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {
        "data": [
            {
                "age": 10, 
                "name": "Bob"
            }, 
            {
                "age": 12, 
                "name": "Anna"
            }
        ], 
        "err": 0
    }

    It is easy to use jsonp, just pass format=jsonp

    >>> resp = users(requests.get('users',
    ...     { 'debug':1, 'format': 'jsonp' }))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    callback({
        "data": [
            {   
                "name": "Bob"
            },
            {   
                "name": "Anna"
            }
        ],
        "err": 0
    });

    You can override the name of callback method using 
    JSONRESPONSE_CALLBACK_NAME option or query arg callback=another_callback
    
    >>> resp = users(requests.get('users',
    ...     { 'debug':1, 'format': 'jsonp', 'callback': 'my_callback' }))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    my_callback({
        "data": [
            {   
                "name": "Bob"
            },
            {   
                "name": "Anna"
            }
        ],
        "err": 0
    });

    You can pass raise=1 to raise exceptions in debug purposes 
    instead of passing info to json response

    >>> @to_json('api')
    ... def error(request):
    ...    raise Exception('Wooot!??')

    >>> resp = error(requests.get('/error',
    ...     {'debug': 1, 'raise': 1}))
    Traceback (most recent call last):
    Exception: Wooot!??

    You can wraps both methods and functions

    >>> class View(object):
    ...     @to_json('plain')
    ...     def render(self, request):
    ...         return dict(data='ok')
    ...     @to_json('api')
    ...     def render_api(self, request):
    ...         return dict(data='ok')
    

    >>> view = View()
    >>> resp = view.render(requests.get('/render'))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {"data": "ok"}
    
    Try it one more
    
    >>> resp = view.render(requests.get('/render'))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {"data": "ok"}
    
    Try it one more with api
    
    >>> resp = view.render_api(requests.get('/render'))
    >>> print resp.status_code
    200
    >>> print resp.content # doctest: +NORMALIZE_WHITESPACE
    {"data": {"data": "ok"}, "err": 0}


    You can pass custom kwargs to json.dumps,
    just give them to constructor

    >>> @to_json('plain', separators=(',  ', ':  '))
    ... def custom_kwargs(request):
    ...    return ['a', { 'b': 1 }]
    >>> resp = custom_kwargs(requests.get('/render'))
    >>> print resp.status_code
    200
    >>> print resp.content
    ["a",  {"b":  1}]
    """
    def __init__(self, serializer_type, error_code=500, **kwargs):
        """
        serializer_types:
            * api - serialize buildin objects (dict, list, etc) in strict api
            * objects - serialize list of region in strict api
            * plain - just serialize result of function, do not wrap response and do not handle exceptions
        """
        self.serializer_type = serializer_type
        self.method = None
        self.error_code=error_code
        self.kwargs = kwargs

    def __call__(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if self.method:
                return self.method(f, *args, **kwargs)

            if not args:
                if self.serializer_type == 'plain':
                    self.method = self.plain_func
                else:
                    self.method = self.api_func

            if getattr(getattr(args[0], f.__name__, None), "im_self", False):
                if self.serializer_type == 'plain':
                    self.method = self.plain_method
                else:
                    self.method = self.api_method
            else:
                if self.serializer_type == 'plain':
                    self.method = self.plain_func
                else:
                    self.method = self.api_func

            return self.method(f, *args, **kwargs)

        return wrapper
    
    def obj_to_response(self, req, obj):
        if self.serializer_type == 'objects':
            if isinstance(obj, Iterable):
                obj = [o.serialize(req) if obj else None for o in obj]
            elif obj:
                obj = obj.serialize(req)
            else:
                obj = None
        
        return { "err": 0, "data": obj }

    def err_to_response(self, err):
        if hasattr(err, "__module__"):
            err_module = err.__module__ + "."
        else:
            err_module = ""

        if hasattr(err, "owner"):
            err_module += err.owner.__name__ + "."

        err_class = err_module + err.__class__.__name__

        err_desc = str(err)
        
        return {
            "err": 1,
            "err_class": err_class,
            "err_desc": err_desc,
            "data": None
        }

    def render_data(self, req, data, status=200):
        debug = DEFAULT_DEBUG
        debug = debug or req.GET.get('debug', 'false').lower() in ('true', 't', '1', 'on')
        debug = debug or req.GET.get('decode', '0').lower() in ('true', 't', '1', 'on')
        format = req.GET.get('format', 'json')
        jsonp_cb = req.GET.get('callback', CALLBACK_NAME)
        content_type = "application/json"
        
        kwargs = dict(self.kwargs)
        if debug:
            kwargs["indent"] = 4
            kwargs["ensure_ascii"] = False
            kwargs["encoding"] = "utf8"

        plain = json.dumps(data, **kwargs)
        if format == 'jsonp':
            plain = "%s(%s);" % (jsonp_cb, plain)
            content_type = "application/javascript"
        
        return HttpResponse(plain, content_type="%s; charset=UTF-8" % content_type, status=status)
        

    def api_func(self, f, *args, **kwargs):
        return self.api(f, args[0], *args, **kwargs)

    def api_method(self, f, *args, **kwargs):
        return self.api(f, args[1], *args, **kwargs)

    def api(self, f, req, *args, **kwargs):
        try:
            resp = f(*args, **kwargs)
            if isinstance(resp, HttpResponse):
                return resp

            data = self.obj_to_response(req, resp)
            status = 200
        except Exception as e:
            logger.exception("Error occurrid while processing reuest [{0}] {1}".format(
                req.method, req.path))

            if int(req.GET.get('raise', 0)):
                raise

            data = self.err_to_response(e)
            status = 404 if isinstance(e, ObjectDoesNotExist) else self.error_code

        return self.render_data(req, data, status)

    def plain_method(self, f, *args, **kwargs):
        data = f(*args, **kwargs)
        if isinstance(data, HttpResponse):
            return data

        return self.render_data(args[1], data)

    def plain_func(self, f, *args, **kwargs):
        data = f(*args, **kwargs)
        if isinstance(data, HttpResponse):
            return data

        return self.render_data(args[0], data)

if __name__ == '__main__':
    import doctest
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", __name__)
    doctest.testmod()
