from setuptools import setup


def make_readme():
    with open('README') as f:
        return f.read()


setup(
    name='roro_ioc',
    packages=['roro_ioc'],
    version='0.1.12',
    description='IOC Injection for python',
    long_description=make_readme(),
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
