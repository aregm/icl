import os
import sys

print('import')


def foo(arg1=None):
    print('foo')
    print('arg1:', arg1)


def check_dependency():
    """Check if dependency is installed."""
    # pylint: disable=import-outside-toplevel
    import toml


def check_environment():
    """Checks if environment variable is set."""
    if not os.getenv('PROGRAM1_ENV_VAR'):
        raise AssertionError('Environment variable PROGRAM1_ENV_VAR not set')


def all_checks():
    """Runs all tests."""
    check_dependency()
    check_environment()


if __name__ == '__main__':
    print('__main__')
    print('args:', sys.argv)
