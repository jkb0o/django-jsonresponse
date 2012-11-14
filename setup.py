from setuptools import setup, find_packages

DESCRIPTION = 'Simple wrap django views to render json '
try:
    LONG_DESCRIPTION = open('README.md').read()
except:
    LONG_DESCRIPTION = None

setup(
    name='django-jsonresponse',
    version='0.1',
    packages=find_packages(),
    author='Yasha Borevich',
    author_email='j.borevich@gmail.com',
    url='http://github.com/jjay/django-staticfinders',
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

