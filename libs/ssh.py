"""
Linux SSH.
"""
from typing import Tuple
import socket
import logging
import paramiko

logger = logging.getLogger(__name__)


class CMDError(Exception):
    pass


class SSH(object):
    def __init__(self, host: str, port: int = 22, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = None

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
        # When get_pty=True, stderr is always empty.
        _stdin, stdout, _stderr = self.client.exec_command(cmd, timeout=self.timeout, get_pty=True)
        stdout.channel.settimeout(self.timeout)

        return_stdout = ''
        print()
        for _ in range(1024):
            try:
                data = stdout.channel.recv(4096)
            except socket.timeout:
                logger.error(f'ssh timeout, got return string: ({return_stdout})')
                raise CMDError(f'socket.timeout, ssh cmd failed: `{cmd}`')

            output = data.decode('utf-8', 'backslashreplace')
            if not output:
                break

            print(output, end='')
            return_stdout += output

        else:
            raise CMDError(f'Too large output for command: `{cmd}`')

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
