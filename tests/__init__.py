import doctest
import os
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", __name__)
SECRET_KEY = 'alloha'

suite = doctest.DocTestSuite('jsonresponse')
runner = unittest.TextTestRunner()
runner.run(suite)
