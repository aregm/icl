# Functions used by other scripts

: ${CONTROL_NODE_IMAGE:=pbchekin/icl-ccn-kubespray:0.0.3}
: ${COREDNS_IMAGE:=registry.k8s.io/coredns/coredns:v1.8.6}
: ${NGINX_IMAGE:=nginx:stable}
: ${ARTIFACTS_DIR:=$HOME/generated}
: ${ICL_INGRESS_DOMAIN:=localtest.me}
: ${INGRESS_IP:=127.0.0.1}

# Load .x1/environment file in the current directory, if exists. This file contains custom settings
# for this environment, such as ingress domain and ingress IP address.
if [[ -f .x1/environment ]]; then
  source .x1/environment
fi

export KUBECONFIG=~/.kube/config
export KUBE_CONFIG_PATH=$KUBECONFIG

function coredns_ip() {
  # returns empty string if the container is not runnning
  docker container inspect coredns 2>/dev/null | jq -r '.[].NetworkSettings.IPAddress'
}

# Starts the control code in a ephemeral container.
function control_node() {
  local docker_cmd=(
    --rm
    --network host
    --volume $HOME/x1:/work/x1
    --volume $ARTIFACTS_DIR:/work/generated
    --volume $HOME/.ssh:/work/.ssh
    --volume $HOME/.kube:/work/.kube
    --volume $HOME/.x1:/work/x1/.x1
    --volume $ARTIFACTS_DIR/passwd:/etc/passwd
    --workdir /work/x1
    --user "$(id -u):$(id -g)"
    --env USER
  )

  if [[ -v http_proxy ]]; then
    docker_cmd+=( --env http_proxy )
  fi

  if [[ -v https_proxy ]]; then
    docker_cmd+=( --env https_proxy )
  fi

  if [[ -v no_proxy ]]; then
    docker_cmd+=( --env no_proxy )
  fi

  if [[ -t 0 ]]; then
    docker_cmd+=( --interactive )
  fi

  if [[ -t 1 ]]; then
    docker_cmd+=( --tty )
  fi

  NAMESERVER_IP="$(coredns_ip)"
  if [[ $NAMESERVER_IP ]]; then
    docker_cmd+=( --dns $NAMESERVER_IP )
  fi

  docker_cmd+=( $CONTROL_NODE_IMAGE )

  if (( $# != 0 )); then
    docker_cmd+=( -c "$*" )
  fi

  # Workaround for cases when mounted directories do not exists
  mkdir -p ~/.kube $ARTIFACTS_DIR ~/.x1

  # Create minimal /etc/passwd for the current user and mount it to the container, so tools like
  # whoami and ssh will be able to detect current user and its home directory.
  echo "${USER}:x:$(id -u):$(id -g)::/work:/bin/bash" > $ARTIFACTS_DIR/passwd

  docker run "${docker_cmd[@]}"
}

function render_corefile() {
  mkdir -p $ARTIFACTS_DIR/coredns
  cat <<EOF >$ARTIFACTS_DIR/coredns/Corefile
. {
    errors
    hosts {
        ${INGRESS_IP} ${ICL_INGRESS_DOMAIN}
        ${INGRESS_IP} hub.${ICL_INGRESS_DOMAIN}
        ${INGRESS_IP} jupyter.${ICL_INGRESS_DOMAIN}
        ${INGRESS_IP} prefect.${ICL_INGRESS_DOMAIN}
        ${INGRESS_IP} ray.${ICL_INGRESS_DOMAIN}
        ${INGRESS_IP} registry.${ICL_INGRESS_DOMAIN}
        ${INGRESS_IP} s3.${ICL_INGRESS_DOMAIN}
        fallthrough
    }
    forward . /etc/resolv.conf
    reload
}
EOF
}

function coredns_start() {
  coredns_stop
  render_corefile
  local docker_cmd=(
      --volume $ARTIFACTS_DIR/coredns:/etc/coredns
      --detach
      --name coredns
      $COREDNS_IMAGE
      -conf /etc/coredns/Corefile
  )
  docker run "${docker_cmd[@]}"
}

function coredns_stop() {
  docker rm --force coredns >/dev/null 2>&1 || true
}

function nginx_start() {
  nginx_stop
  local docker_cmd=(
      --volume $ARTIFACTS_DIR/nginx/sites-available:/etc/nginx/conf.d
      --network host
      --detach
      --name nginx
      $NGINX_IMAGE
  )
  docker run "${docker_cmd[@]}"
}

function nginx_stop() {
  docker rm --force nginx >/dev/null 2>&1 || true
}
