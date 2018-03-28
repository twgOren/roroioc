from setuptools import setup

setup(
    name='roro_ioc',
    packages=['roro_ioc'],
    version='0.1.2',
    description='IOC Injection for python',
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
