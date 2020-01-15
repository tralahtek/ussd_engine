from setuptools import setup, find_packages
import os
from ussd_version.version import VERSION
from os import path


def _strip_comments(l):
    return l.split('#', 1)[0].strip()


def _pip_requirement(req):
    if req.startswith('-r '):
        _, path = req.split()
        return reqs(*path.split('/'))
    return [req]


def _reqs(*f):
    return [
        _pip_requirement(r) for r in (
            _strip_comments(l) for l in open(
                os.path.join(os.getcwd(), *f)).readlines()
        ) if r]


def reqs(*f):
    """Parse requirement file.
    Example:
        reqs('default.txt')          # requirements/default.txt
        reqs('extras', 'redis.txt')  # requirements/extras/redis.txt
    Returns:
        List[str]: list of requirements specified in the file.
    """
    return [req for subreq in _reqs(*f) for req in subreq]


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ussd_airflow_engine',
    version=VERSION,
    packages=find_packages(exclude=('ussd_airflow',)),
    url='https://github.com/ussd-airflow/ussd_engine',
    install_requires=reqs('default.txt'),
    include_package_data=True,
    license='MIT',
    author='Mwas',
    maintainer="mwas",
    author_email='mwasgize@gmail.com',
    description='Ussd Airflow Library',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
