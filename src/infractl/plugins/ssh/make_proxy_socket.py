"""Socks proxy utilities."""

import json
import os
import socket
import time
from urllib.parse import urlsplit

import pypac
import socks

from infractl.logging import get_logger

SOCKS_PROXY = 'socks-proxy.txt'
logger = get_logger()

PROXY_CACHE_REFRESH = 60 * 60  # force refresh if cache is older than 1 hour

DEFAULT_SCHEME_PORTS = {
    'http': 80,
    'https': 443,
}


def split_address(addr, default_port=None):
    if '//' not in addr:
        addr = '//' + addr
    splitted = urlsplit(addr)

    try:
        socket.gethostbyname(splitted.hostname)
    except socket.error as exc:
        raise ValueError(f'Invalid address: hostname "{splitted.hostname}" does not exist') from exc

    port = splitted.port or default_port or DEFAULT_SCHEME_PORTS.get(splitted.scheme, 80)

    return splitted.hostname, int(port)


PROXY_PROTOS = ('http', 'https')


def _detect_proxies_by_pac(target_host):
    result = {}
    logger.info('Detecting proxy via PAC')
    pac = pypac.get_pac()
    if pac:
        for proto in PROXY_PROTOS:
            proxy = pypac.parser.proxy_url(
                pac.find_proxy_for_url(f'{proto}://{target_host}', target_host)
            )
            if proxy:
                logger.info('Found "%s" proxy for "%s" proto', proxy, proto)
                result[proto] = proxy
    else:
        logger.info('No proxy found')
    return result


def _apply_proxies_to_env(proxies):
    for proto in PROXY_PROTOS:
        os.environ[f'{proto}_proxy'] = proxies.get(proto, '')


def detect_proxies_and_update_env(target_host, proxy_cache=None, force_update=False):
    proxies, cache_data, force_cache_store = None, {}, False
    if proxy_cache and not force_update:
        try:
            with open(proxy_cache, encoding='utf-8') as cache:
                cache_data = json.loads(cache.read())
        except (ValueError, IOError):
            logger.info('Cache file "%s" is invalid', proxy_cache)
        else:
            if cache_data.get('timestamp', 0) + PROXY_CACHE_REFRESH >= time.time():
                proxies = cache_data.get(f'{target_host}-proxies', None)
                if proxies is not None:
                    logger.info('Read proxies from cache successfully')
                    for proxy in proxies.values():
                        try:
                            split_address(proxy)
                        except ValueError:
                            logger.info('Proxy "%s" does not exist, refreshing', proxy)
                            proxies = None
                            break
            else:
                logger.info("Refreshing proxy cache file as it's too old")
                force_cache_store = True

    cached_proxies = {} if proxies is None else dict(proxies)
    if proxies is None:
        proxies = _detect_proxies_by_pac(target_host)
        logger.info('Checking that proxy hosts exist')
        for proto, proxy in list(proxies.items()):
            try:
                split_address(proxy)
            except ValueError:
                logger.info('Proxy host "%s" found but does not exist', proxy)
                del proxies[proto]

    if proxy_cache and (cached_proxies != proxies or force_cache_store):
        cache_data['timestamp'] = time.time()
        cache_data[f'{target_host}-proxies'] = proxies
        try:
            with open(proxy_cache, 'w', encoding='utf-8') as cache:
                cache.write(json.dumps(cache_data))
        except IOError as err:
            logger.info('Cannot update "%s" proxy cache: %s', proxy_cache, err)

    _apply_proxies_to_env(proxies)
    return proxies


def read_socks_proxy():
    try:
        with open(os.path.join(os.path.dirname(__file__), SOCKS_PROXY), encoding='utf-8') as cfg:
            hostname = cfg.readline().strip()
    except IOError:
        return None, None
    if not hostname:
        # empty socks-proxy.txt
        return None, None
    # check if socks proxy host exists
    try:
        return split_address(hostname, 1080)
    except ValueError:
        return None, None


def proxy_socket():
    socks_proxy, socks_port = read_socks_proxy()
    if not socks_proxy:
        # not behind a proxy, use direct connection
        return None

    sock = socks.socksocket()
    sock.set_proxy(socks.SOCKS5, socks_proxy, socks_port)
    return sock


if __name__ == '__main__':
    print(read_socks_proxy())
