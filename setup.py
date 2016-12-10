from setuptools import setup

setup(
    name='pyltc',
    author='Yassen Damyanov',
    author_email='yd@itlabs.bg',
    version='0.1.4',
    url='http://github.com/yassen-itlabs/py-linux-traffic-control',
    packages=['pyltc'],
    description="A simple tool for configuring Linux traffic control"
                " via command line clauses or programmatically.",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
