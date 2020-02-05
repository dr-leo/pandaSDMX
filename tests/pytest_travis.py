'''
Wrapper script for pytest. Runs pytest with given command line args.
``--remote-data` is removed from the args list, unless the script is invoked
within a cron job on on travis-ci. As a result, builds triggered by
commits will not cause the test suite to request 
remote data from data sources. In particular, test runs triggered by commits to master are robust against
server outages at the sources.
'''


import pytest
import os
import sys


args = sys.argv[1:]
if '--remote-data' in args and os.getenv('TRAVIS_EVENT_TYPE') != 'cron':
    args.remove('--remote-data')
pytest.main(args)
