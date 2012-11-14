import doctest
import os
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", __name__)

suite = doctest.DocTestSuite('jsonresponse')
runner = unittest.TextTestRunner()
runner.run(suite)
