##############################################################################
#
# Copyright (c) 2008-2013 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# Copyright (c) 2015 MTSolutions S.A.
# All Rights Reserved.

# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
import sys

py_version = sys.version_info[:2]

if py_version < (2, 6):
    raise RuntimeError('On Python 2, superslacker requires Python 2.6 or later')
elif (3, 0) < py_version < (3, 2):
    raise RuntimeError('On Python 3, superslacker requires Python 3.2 or later')

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.txt')).read()
except (IOError, OSError):
    README = ''
try:
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except (IOError, OSError):
    CHANGES = ''

setup(name='superslacker',
      version='0.2',
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      description='superslacker plugin for supervisord',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Development Status :: 3 - Alpha",
          'Environment :: No Input/Output (Daemon)',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: System :: Boot',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Systems Administration',
      ],
      author='Sebastian Lara Menares',
      author_email='slaramen@gmail.com',
      url="https://github.com/MTSolutions/superslacker",
      maintainer="Sebastian Lara Menares",
      maintainer_email="slaramen@gmail.com",
      keywords='supervisor slack monitoring',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'superlance',
          'supervisor',
          'slacker'
      ],
      tests_require=[
          'supervisor',
          'superlance',
          'slacker',
          'mock'
      ],
      test_suite='superslacker.tests',
      entry_points="""\
      [console_scripts]
      fatalslack = superslacker.superslacker:fatalslack
      superslacker = superslacker.superslacker:main
      """
      )
