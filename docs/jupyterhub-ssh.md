# Enable SSH access to JupyterHub session

Follow the following instructions to enable SSH access to your JupyterHub session.
You can use this SSH access, for example, to connect your VSCode application that is running locally to your JupyterHub session that is running in X1 cluster.

Note that you will need to re-enable SSH each time after your JupyterHub session is restarted.
Also you may need to remove old records from `~/.ssh/known_host`, since every time SSH will use a newly generated host key. 

## SSH with a password

In your JupyterHub session, set a password for user jovyan:

```shell
sudo passwd jovyan
````

Then execute the following command:

```shell
x1 ssh enable
```

Note that you can always add your public key later with `ssh-copy-id` or with `x1 ssh enable --key ...` described below.

## SSH with a public key

In your JupyterHub session, execute:

```shell
x1 ssh enable --key "your_public_ssh_key"
```

Where "your_public_ssh_key" is a content of your `~/.ssh/id_rsa.pub` (or `~/.ssh/id_ed25519.pub` or other key).

