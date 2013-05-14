from setuptools import find_packages, setup

setup_args = dict(
    name='appstats-logger',
    version='0.1',
    license='Apache',
    description='AppStats Logger is a simple middleware used to log App '
                'Engine RPC profiling data, based on App Stats, so that it '
                'can be later processed for log data.',
    author='Robert Kluin',
    author_email='robert.kluin@ezoxsystems.com',
    url='http://github.com/robertkluin/appstats-logger',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 2 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: Apache',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)

if __name__ == '__main__':
    setup(**setup_args)

