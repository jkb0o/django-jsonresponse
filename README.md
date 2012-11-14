About
=====

Wrap view functions, allowng them render python native and custom 
objects to json

Usage
-----

Simple wrap returning data into json

```python
from jsonresponse import to_json

@to_json('plain')
def hello(request):
   return dict(hello='world')
```

    GET /hello/
    {"hello": "world"}
    
Result can be wraped in some api manier. 
Note, you can pass debug=1 to pretty print response. 
Use JSONRESPONCE_DEBUG_DEFAULT=True to enable by default. 

```python
@to_json('api')
def goodbye(request):
   return dict(good='bye')
```
    
    GET /goodbye/?debug=1
    {
        "data": {
            "good": "bye"
        }, 
        "err": 0
    }

Automaticaly error handling, note response code is 500 here

```python
@to_json('api')
def error(request):
   raise Exception('Wooot!??')
```
    
    GET /error/
    {            
        "err_class": "Exception",
        "err_desc": "Wooot!??",
        "data": null,
        "err": 1
    }

You can pass raise=1 to raise exceptions in debug purposes 
instead of passing info to json response

    GET /error/?raise=1
    Traceback (most recent call last):
    Exception: Wooot!??


You can serialize not only pure python data types.
Implement `serialize` method on toplevel object or 
each element of toplevel array. Note, that request 
object is passed to serialize method.

```python
class User(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def serialize(self, request):
        if request.GET.get('with_age', False):
            return dict(name=self.name, age=self.age)
        else:
            return dict(name=self.name)

@to_json('objects')
def users(request):
   return [User('Bob', 10), User('Anna', 12)]
```
    
    GET /users/?with_age=1
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
    
    GET /users/?format=jsonp
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
JSON_RESPONSE_CBNAME option or query arg callback=another_callback
    
    GET /users/?format=jsonp&callback=my_callback    
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

