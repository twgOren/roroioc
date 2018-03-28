from setuptools import setup


def readfile(filename):
    with open(filename) as f:
        return f.read()


readme = readfile('README.md')
license = readfile('LICENSE')

setup(
    name='roro_ioc',
    packages=['roro_ioc'],
    version='0.1.4',
    description='IOC Injection for python',
    long_description='{}\n\n{}'.format(readme, license),
    author='Twiggle',
    author_email='oren@twiggle.com',
    url='https://github.com/twgOren/roroioc',
    keywords=['ioc'],
    classifiers=[],
    install_requires=[
        'attrs',
        'typing',
        'cached_property',
        'werkzeug',
    ]
)
