"""Utils for SSH infra."""

import errno
import os
import subprocess
import sys
import time

import paramiko
import socks

from infractl.logging import get_logger
from infractl.plugins.ssh import make_proxy_socket

logger = get_logger()


class ZymeClient:
    """Paramiko wrapper, inspired by enzyme."""

    def __init__(self, hostname, username, password, use_proxy=False, add2known_hosts=True):
        """
        Create SSH client.

        Parameters
        ----------
        hostname: str
        username: str
            using for authentication
        pkey_file: str
            private key in OpenSSH format
        use_proxy: bool, default True
            creates socksocket with SOCKS5 protocol to use by paramiko connect
        add2known_hosts: bool, default True
            automatically adding the hostname and new host key to the local
            known_hosts file

        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.use_proxy = use_proxy
        self.add2known_hosts = add2known_hosts
        self.connected = False

    def __enter__(self):
        """
        Connect to host.

        Returns
        -------
        client: ZymeClient

        """
        logger.info('Connecting to: %s', self.hostname)

        if self.use_proxy:
            self.sock = make_proxy_socket.proxy_socket()

            try:
                self.sock.connect((self.hostname.encode('utf-8'), 22))
            except socks.SOCKS5Error as err:
                raise ConnectionError(f'{err}; check hostname') from err

        else:
            self.sock = None

        self.client = paramiko.SSHClient()
        if self.add2known_hosts:
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                port=22,
                sock=self.sock,
            )
        except IOError as exc:
            raise ConnectionError(exc) from exc
        except paramiko.ssh_exception.SSHException as exc:
            raise ConnectionError(
                'server refused key; check credentials '
                + f'(username, private key) - ({self.username}, {self.password})'
            ) from exc

        self.connected = True
        logger.info('Connected')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if self.use_proxy:
            self.sock.close()

        self.connected = False

    def verify_connected(self):
        if not self.connected:
            raise ValueError('ZymeClient is not connected')

    @property
    def home(self) -> str:
        self.verify_connected()

        _, stdout, _ = self.client.exec_command('echo $HOME')
        return stdout.read().rstrip(b'\n').decode('utf-8')

    def exec_command(
        self,
        command,
        get_output=True,
        stdout_log_file='stdout_log.txt',
        stderr_log_file='stderr_log.txt',
        chunksize=1024,
    ):
        """
        Execute the command on remote host by using connected SSH client.

        Parameters
        ----------
        command:          str
        get_output:       bool, default True
            display information from stdout and stderr streams on remote host
            localy
        stdout_log_file:  str, default 'stdout_log.txt'
        stderr_log_file:  str, default 'stderr_log.txt'
        chunksize:        int, default 1024

        Returns
        -------
        retcode: int
            result of the executed command

        """
        self.verify_connected()
        _, stdout, stderr = self.client.exec_command(command, bufsize=1)

        stdout.channel.setblocking(0)
        stderr.channel.setblocking(0)

        while True:

            while stdout.channel.recv_ready():
                outdata = stdout.channel.recv(chunksize)
                if get_output:
                    sys.stdout.write(outdata)
                if stdout_log_file:
                    with open(stdout_log_file, 'a', encoding='utf-8') as out:
                        out.write(outdata)

            while stderr.channel.recv_stderr_ready():
                errdata = stderr.channel.recv_stderr(chunksize)
                if get_output:
                    sys.stderr.write(errdata)
                if stderr_log_file:
                    with open(stderr_log_file, 'a', encoding='utf-8') as out:
                        out.write(errdata)

            if (
                stdout.channel.exit_status_ready() and stderr.channel.exit_status_ready()
            ):  # If completed
                break
            time.sleep(0.5)

        return stdout.channel.recv_exit_status()

    def _get_sftp_client(self):
        self.verify_connected()
        transport = self.client.get_transport()
        sftp_client = paramiko.SFTPClient.from_transport(transport)
        return sftp_client

    def _make_dir(self, remotepath):
        self.verify_connected()
        dir_path, _ = os.path.split(remotepath)
        _, stdout, stderr = self.client.exec_command(f'mkdir -p "{dir_path}"')
        res = stdout.read().rstrip('\n') + stderr.read().rstrip('\n')

        if res:
            raise OSError(
                -1,
                f"Can't create file on remote host ({remotepath}); result - {res}",
                remotepath,
            )

    def put_file(self, localpath, remotepath, overwrite=False, chunksize=1024**2):
        """
        Copy a local file (localpath) to the SFTP server as remotepath by using
        connected SSH client.

        Parameters
        ----------
        local_path: str
        remotepath: str
        chunksize: int, default 1024

        Returns
        -------
        file_attr: paramiko.sftp_attr.SFTPAttributes

        """

        def file_content_generator():
            with open(localpath, mode='rb') as f:
                while True:
                    data = f.read(chunksize)
                    if not data:
                        break
                    yield data

        return self._put_string(file_content_generator, remotepath, overwrite, 'w')

    def put_string(self, file_content, remotepath, overwrite=False, mode='w'):
        """
        Copy a file_content string to the SFTP server as remotepath by using
        connected SSH client.

        Parameters
        ----------
        file_content: str
        remotepath: str
        mode: str, default 'w'
            mode for open function

        Returns
        -------
        file_attr: paramiko.sftp_attr.SFTPAttributes

        """

        def string_generator():
            yield file_content

        return self._put_string(string_generator, remotepath, overwrite, mode)

    def _put_string(self, data_generator, remotepath, overwrite, mode):
        with self._get_sftp_client() as sftp_client:
            exist_remotepath = True
            try:
                sftp_client.stat(remotepath)
            except IOError:
                # remotepath not exist
                exist_remotepath = False

            if not exist_remotepath or overwrite:
                try:
                    with sftp_client.file(remotepath, mode=mode) as f:
                        for data in data_generator():
                            f.write(data)
                except IOError:
                    self._make_dir(remotepath)
                    self._put_string(data_generator, remotepath, overwrite, mode)
            else:
                raise OSError(errno.EEXIST, f'{remotepath} already exists', remotepath)

            return sftp_client.stat(remotepath)

    def expand_home_path(self, remotepath):
        if remotepath.startswith('~'):
            remotepath = remotepath.replace('~', self.home)
        return remotepath

    def ensure_remotepath(self, remotepath):
        if remotepath is None:
            remotepath = '~/run_script.sh'

        return self.expand_home_path(remotepath)


def check_script(file_path):
    """
    File having string shebang is treated as a script, otherwise
    it is treated as binary.

    Parameters
    ----------
    file_path: str

    Returns
    -------
    : bool
        True if script

    """
    with open(file_path, encoding='utf-8') as f:
        return f.readline().startswith('#!')


def convert_newline_symbol(local_file):
    """
    Converts DOS/Windows newline (CRLF) to UNIX newline (LF)
    in local_file content.

    Parameters
    ----------
    local_file: str

    Returns
    -------
    unix_like_string: str

    """
    with open(local_file, 'rU', encoding='utf-8') as f:
        return f.read()


def identify_script_position(args):
    skip_next_arg = False
    mpi_script_pos = -1

    for idx, arg in enumerate(args):
        if not skip_next_arg:
            if arg.startswith('-') or arg.startswith('+'):
                skip_next_arg = True
                continue
            mpi_script_pos = idx
            break
        skip_next_arg = False

    if mpi_script_pos == -1:
        raise ValueError("script not found in run command's arguments")

    return mpi_script_pos


def prepare_run_args(run_args: list, remotepath):
    run_args = list(run_args)
    script_pos = identify_script_position(run_args)
    script = run_args[script_pos]
    run_args[script_pos] = remotepath

    return (script, subprocess.list2cmdline(run_args))


def zyme_run_command(
    run_args,
    zyme_client,
    remotepath=None,
    newline_conversion=True,
    overwrite=False,
    no_remove=False,
):
    """
    Run script on remote host.

    Parameters
    ----------
    script_args: list
        first element of list is script path;
        other - args that will be passed into script
    zyme_client: ZymeClient
    remotepath: str, default None
        the place to which the file will be copied
    newline_conversion: bool, default True
        convert DOS/Windows newline (CRLF) to UNIX newline (LF) in script
    overwrite: bool, default False
    no_remove: bool, default False

    Returns
    -------
    retcode: int

    """
    try:
        with zyme_client as connected_client:
            if newline_conversion:
                unix_string = convert_newline_symbol(run_args[1])
                connected_client.put_string(unix_string, remotepath, overwrite=overwrite)
            else:
                connected_client.put_file(run_args[1], remotepath, overwrite=overwrite)

            # TODO: either the conda must be available through PATH env var
            # or the option must be available through settings
            conda_path = os.environ['ICL_REMOTE_CONDA_PATH']
            command = f'{conda_path} run -n base python {remotepath}'
            _, stdout, stderr = connected_client.client.exec_command(command)
            logger.info('output from command: "%s":\n%s', command, stdout.read().decode('utf-8'))
            # pylint: disable=pointless-string-statement
            '''
            remotepath = connected_client.ensure_remotepath(remotepath)

            script_path, script_args_str = prepare_run_args(
                run_args, remotepath)

            try:
                if newline_conversion and check_script(script_path):
                    unix_string = convert_newline_symbol(script_path)
                    connected_client.put_string(unix_string,
                                                remotepath, overwrite)
                else:
                    connected_client.put_file(script_path,
                                              remotepath, overwrite)
            except Exception as err:
                print('Error: %s' % err)
                # return bad_retcode
                return 1

            connected_client.exec_command('chmod +x "%s"' % (remotepath))
            print('Command execution "%s":\n' % script_args_str)
            retcode = connected_client.exec_command(script_args_str)
            print('\nExecution complete')
            '''

            if not no_remove:
                connected_client.exec_command(f'rm -f "{remotepath}"')

        return len(stderr.read())

    except ConnectionError as err:
        logger.info('Error: %s', err)
        return -1
