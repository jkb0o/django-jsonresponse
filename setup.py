from setuptools import setup, find_packages
from subprocess import check_call

try:
    check_call(['pandoc', '--to=rst', '-o', 'README.txt', 'README.md'])
    LONG_DESCRIPTION = open('README.txt').read()
except:
    LONG_DESCRIPTION = None

DESCRIPTION = 'Simple wrap django views to render json '

setup(
    name='django-jsonresponse',
    version='0.8.2',
    packages=find_packages(),
    author='Yasha Borevich',
    author_email='j.borevich@gmail.com',
    url='http://github.com/jjay/django-jsonresponse',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms='any',
    test_suite='tests',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
)

