from setuptools import find_packages, setup
setup(
name="lings",
    version="0.1",
    description="",
    author="Galen Curwen-McAdams",
    author_email='',
    platforms=["any"],
    license="Mozilla Public License 2.0 (MPL 2.0)",
    include_package_data=True,
    data_files = [("", ["LICENSE.txt"])],
    url="",
    packages=find_packages(),
    install_requires=['redis','logzero','lxml','paho-mqtt','attrs','python-consul', 'roman', 'textx', 'zerorpc'],
    entry_points = {'console_scripts': ['lings-pipe-add = lings.pipes_add:main',
                                        'lings-pipe-remove = lings.pipes_remove:main',
                                        'lings-pipe-get = lings.pipes_get:main',
                                        'lings-pipe-run = lings.pipes_run:main',
                                        'lings-pipe-xml = lings.pipes_xml:main',
                                        'lings-pipe-modify = lings.pipes_modify:main',
                                        'lings-route-add = lings.routes_add:main',
                                        'lings-route-remove = lings.routes_remove:main',
                                        'lings-route-get = lings.routes_get:main',
                                        'lings-route-gather = lings.routes_gather:main',
                                        'lings-route-run = lings.routes_run:main',
                                        'lings-route-xml = lings.routes_xml:main',
                                        'lings-rule-add = lings.rules_add:main',
                                        'lings-rule-remove = lings.rules_remove:main',
                                        'lings-rule-get = lings.rules_get:main',
                                        'lings-rule-run = lings.rules_run:main',
                                        'lings-rule-xml = lings.rules_xml:main',
                                        'lings-rule-modify = lings.rules_modify:main',
                                        'lings-state-xml = lings.states_xml:main',
                                        ],
                            },
)
