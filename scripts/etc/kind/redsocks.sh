#!/usr/bin/env bash

# This script is executed in the kind container.

set -e

http_proxy_host="$1"
http_proxy_port="$2"

if [[ $http_proxy_host && $http_proxy_port ]]; then
  echo "Enabling proxy"
else
  echo "Disabling proxy"
  if dpkg -s redsocks &> /dev/null; then
    systemctl stop redsocks --no-block
  fi
  exit 0
fi

if ! dpkg -s redsocks &> /dev/null; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends redsocks
fi

mkdir -p /etc/systemd/system/redsocks.service.d

echo "\
[Unit]
After=containerd.service
StartLimitIntervalSec=0
StartLimitBurst=infinity
" > /etc/systemd/system/redsocks.service.d/order.conf

echo "\
[Service]
Restart=on-failure
RestartSec=5s

ExecStartPre=/usr/sbin/iptables -w 60 -t nat -N REDSOCKS
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 0.0.0.0/8 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 10.0.0.0/8 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 100.64.0.0/10 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 127.0.0.0/8 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 169.254.0.0/16 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 172.16.0.0/12 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 192.168.0.0/16 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 198.18.0.0/15 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 224.0.0.0/4 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -d 240.0.0.0/4 -j RETURN
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -p tcp --dport 80 -j REDIRECT --to-ports 12345
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -p tcp --dport 443 -j REDIRECT --to-ports 12346
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A REDSOCKS -p tcp --dport 11371 -j REDIRECT --to-ports 12345
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A PREROUTING -p tcp --dport 80 -j REDSOCKS
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A PREROUTING -p tcp --dport 443 -j REDSOCKS
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A PREROUTING -p tcp --dport 11371 -j REDSOCKS
ExecStartPre=/usr/sbin/iptables -w 60 -t nat -A OUTPUT -p tcp -j REDSOCKS
ExecStartPre=/usr/sbin/iptables -w 60 -P FORWARD ACCEPT

ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D OUTPUT -p tcp -j REDSOCKS
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D PREROUTING -p tcp --dport 80 -j REDSOCKS
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D PREROUTING -p tcp --dport 443 -j REDSOCKS
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D PREROUTING -p tcp --dport 11371 -j REDSOCKS
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -p tcp --dport 80 -j REDIRECT --to-ports 12345
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -p tcp --dport 443 -j REDIRECT --to-ports 12345
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -p tcp --dport 443 -j REDIRECT --to-ports 12346
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -p tcp --dport 11371 -j REDIRECT --to-ports 12345
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 0.0.0.0/8 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 10.0.0.0/8 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 100.64.0.0/10 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 127.0.0.0/8 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 169.254.0.0/16 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 172.16.0.0/12 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 192.168.0.0/16 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 198.18.0.0/15 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 224.0.0.0/4 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -D REDSOCKS -d 240.0.0.0/4 -j RETURN
ExecStopPost=-/usr/sbin/iptables -w 60 -t nat -X REDSOCKS
" > /etc/systemd/system/redsocks.service.d/iptables.conf

cat << EOF > /etc/redsocks.conf
base {
    log_debug = off;
    log_info = off;
    log = "file:/var/log/redsocks.log";
    daemon = on;
    redirector = iptables;
}
redsocks {
    local_ip = 0.0.0.0;
    local_port = 12345;
    ip = $http_proxy_host;
    port = $http_proxy_port;
    type = http-relay;
}
redsocks {
    local_ip = 0.0.0.0;
    local_port = 12346;
    ip = $http_proxy_host;
    port = $http_proxy_port;
    type = http-connect;
}
EOF

systemctl daemon-reload
systemctl restart redsocks --no-block
