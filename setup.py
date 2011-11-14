from distutils.core import setup

setup(name='ardrone',
    version='0.0.1',
    description='Python interface to the Parrot A.R. Drone',
    author='Rich Wareham',
    author_email='rjw57@cantab.net',
    url='http://example.com/',

    packages=[
      'ardrone', 'ardrone.core', 'ardrone.util', 'ardrone.platform', 'ardrone.qtgui',
      'controllers', 'controllers.keyboard'
    ],

    package_data = {
      'ardrone.qtgui': ['res/*.ui'],
    },

    scripts = ['qtdronegui.py', 'keybdcontrol.py'],
)
