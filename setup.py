from setuptools import find_packages, setup
setup(
name="lings",
    version="0.1",
    description="",
    author="Galen Curwen-McAdams",
    author_email='',
    platforms=["any"],
    license="Mozilla Public License 2.0 (MPL 2.0)",
    data_files = [("", ["LICENSE.txt"])],
    url="",
    packages=find_packages(),
    install_requires=['redis','logzero','paho-mqtt','attrs','python-consul','textx'],

    entry_points = {'console_scripts': ['lings-pipe-add = lings.pipes_add:main',
                                        'lings-pipe-remove = lings.pipes_remove:main',
                                        'lings-route-add = lings.routes_add:main',
                                        'lings-route-remove = lings.routes_remove:main',
                                        'lings-rule-add = lings.rules_add:main',
                                        'lings-rule-remove = lings.rules_remove:main',
                                        ],
                            },
)
