from setuptools import setup, find_packages
from uiinspector import VERSION

setup(
    name='uiinspector',
    version=VERSION,
    description='GUI tool for capturing windows ui element',
    packages=find_packages(
        include=['uiinspector*']
    ),
    entry_points={
        'console_scripts': [
            'ui-inspector = uiinspector.uiinspector:run'
        ]
    },
    install_requires=['PySide6==6.3.0', 'uiautomation>=2.0.16', 'pyjab>=1.1.5', 'mouse', 'keyboard', 'yapf'],
    include_package_data=True
)

