from scripts.kubernetes import coredns

COREFILE1 = """\
.:53 {
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
}
"""


COREFILE2 = """\
.:53 {
    health {
       lameduck 5s
    }
    hosts {
       127.0.0.1 svc.localtest.me
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
}
"""


def test_create_hosts():
    hosts = [
        coredns.Host(ip='127.0.0.1', name='svc1.localtest.me'),
        coredns.Host(ip='127.0.0.2', name='svc2.localtest.me'),
    ]
    lines = coredns.create_hosts(hosts)
    assert lines == [
        '       127.0.0.1 svc1.localtest.me',
        '       127.0.0.2 svc2.localtest.me',
    ]


def test_update_corefile_no_hosts():
    hosts = [
        coredns.Host(ip='127.0.0.1', name='svc1.localtest.me'),
        coredns.Host(ip='127.0.0.2', name='svc2.localtest.me'),
    ]
    content = coredns.update_corefile(COREFILE1, hosts)
    assert content == """\
.:53 {
    health {
       lameduck 5s
    }
    hosts {
       127.0.0.1 svc1.localtest.me
       127.0.0.2 svc2.localtest.me
       fallthrough
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
}"""


def test_update_corefile_with_hosts():
    hosts = [
        coredns.Host(ip='127.0.0.1', name='svc1.localtest.me'),
        coredns.Host(ip='127.0.0.2', name='svc2.localtest.me'),
    ]
    content = coredns.update_corefile(COREFILE2, hosts)
    assert content == """\
.:53 {
    health {
       lameduck 5s
    }
    hosts {
       127.0.0.1 svc1.localtest.me
       127.0.0.2 svc2.localtest.me
       fallthrough
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
}"""
