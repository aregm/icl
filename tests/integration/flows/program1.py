import sys

print('import')


def foo(arg1=None):
    print('foo')
    print('arg1:', arg1)


if __name__ == '__main__':
    print('__main__')
    print('args:', sys.argv)
