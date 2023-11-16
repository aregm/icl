import os
from unittest import mock

from infractl import identity


def test_sanitize():
    assert identity.sanitize('paul') == 'paul'
    assert identity.sanitize('first.last1-last2@domain.com') == 'first-last1-last2-domain-com'
    assert identity.sanitize('lee.foo-bar@domain.com') == 'lee-foo-bar-domain-com'
    assert identity.sanitize('.lee..foo--bar@domain.com.') == 'lee-foo-bar-domain-com'


@mock.patch.dict(os.environ, {"USER": "user@domain.com"}, clear=True)
def test_generate():
    assert identity.generate() == 'user-domain-com'
    assert identity.generate(prefix='foo') == 'foo-user-domain-com'
    assert identity.generate(suffix='bar') == 'user-domain-com-bar'
    assert identity.generate(prefix='foo', suffix='bar') == 'foo-user-domain-com-bar'
