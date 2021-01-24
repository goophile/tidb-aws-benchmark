"""
Linux SSH.
"""
from typing import Tuple
import socket
import os
import time
import logging
import paramiko

logger = logging.getLogger(__name__)


class CMDError(Exception):
    pass


class SSH:
    def __init__(self, host: str, port: int = 22, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = None

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass

    def login(self, username: str, keyfile: str):
        logger.info(f"ssh {self.host} -p {self.port} -l {username} -i {keyfile}")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = paramiko.RSAKey.from_private_key_file(keyfile)
        self.client.connect(self.host, self.port, username, pkey=key)

    def _validate_sudo_privilege(self, cmd: str):
        if 'sudo' not in cmd:
            return
        _stdin, stdout, _stderr = self.client.exec_command('sudo -n true', get_pty=True)
        rc_nr = stdout.channel.recv_exit_status()
        if int(rc_nr) != 0:
            raise CMDError(f'no sudo privilege or requires sudo password: `{cmd}`')

    def _cmd(self, cmd: str) -> Tuple[int, str]:
        cmd = f"bash -l -i -c '{cmd}'" # make bash load .bashrc

        # When get_pty=True, stderr is always empty.
        _stdin, stdout, _stderr = self.client.exec_command(cmd, timeout=self.timeout, get_pty=True)
        stdout.channel.settimeout(self.timeout)

        return_stdout = ''
        print()
        for _ in range(10240):
            time.sleep(0.1)
            try:
                data = stdout.channel.recv(102400)
            except socket.timeout:
                logger.error(f'ssh timeout, got return string: ({return_stdout})')
                raise CMDError(f'socket.timeout, ssh cmd failed: `{cmd}`')

            output = data.decode('utf-8', 'backslashreplace')
            if not output:
                break

            print(output, end='')
            return_stdout += output

        else:
            raise CMDError(f'Too large output or waiting too long for command: `{cmd}`')

        if return_stdout:
            print()

        rc_nr = stdout.channel.recv_exit_status()
        return int(rc_nr), return_stdout

    def exec_cmd(self, cmd: str, strict: bool = True) -> Tuple[int, str]:
        """
        Execute a shell command. Multiple calls are NOT in the same shell context.
        """
        self._validate_sudo_privilege(cmd)

        logger.info(f'Execute command `{cmd}` ...')
        rc_nr, output = self._cmd(cmd)

        if strict and rc_nr != 0:
            logger.error(output)
            raise CMDError(f'The command `{cmd}` exited with none-zero code: {rc_nr}')

        return rc_nr, output


class SFTP:
    def __init__(self, host: str, port: int, username: str, keyfile: str, timeout: int = 30):
        self.host = host
        self.port = port
        self.username = username
        self.keyfile = keyfile
        self.timeout = timeout
        self.client = None
        self.sftp_client = None

    def __del__(self):
        try:
            self.sftp_client.close()
            self.client.close()
        except Exception:
            pass

    def _connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = paramiko.RSAKey.from_private_key_file(self.keyfile)
        self.client.connect(self.host, self.port, self.username, pkey=key, timeout=self.timeout)

        self.sftp_client = self.client.open_sftp()  # Returns a new SFTPClient object
        self.sftp_client.get_channel().settimeout(self.timeout)

    def put(self, localpath: str, remotepath: str):
        """
        Scp local file or directory to remote.
        """
        self._connect()
        self._put_recursive(localpath, remotepath)
        logger.info(f'Put file from {localpath} to {self.host}:{self.port}:{remotepath}')

    def _put_recursive(self, localpath: str, remotepath: str):
        if os.path.islink(localpath):
            logger.warning(f"'{localpath}' is a link, skip")
            return

        if os.path.isfile(localpath):
            self._mkdir(f'{remotepath}')
            self.sftp_client.put(localpath, remotepath)

        elif os.path.isdir(localpath):
            self._mkdir(f'{remotepath}/')
            for item in os.listdir(localpath):
                self._put_recursive(os.path.join(localpath, item), f'{remotepath}/{item}')

    def _mkdir(self, remotepath: str):
        dirs_ = []
        dir_, _basename = os.path.split(remotepath)
        while len(dir_) > 1:
            dirs_.append(dir_)
            dir_, _ = os.path.split(dir_)

        if len(dir_) == 1 and not dir_.startswith("/"):
            dirs_.append(dir_)  # For a remote path like y/x.txt

        while dirs_:
            dir_ = dirs_.pop()
            try:
                self.sftp_client.stat(dir_)
            except FileNotFoundError:
                logger.debug(f"Making dir: {dir_}")
                self.sftp_client.mkdir(dir_)

    def get(self, remotepath: str, localpath: str):
        """
        Scp remote file to local. Not support directory yet.
        """
        self._connect()
        self.sftp_client.get(remotepath, localpath)
        logger.info(f'Got file from {self.host}:{self.port}:{remotepath} to {localpath}')
