"""
Install and benchmark TiDB via the ControlServer.
"""
import logging
from .ssh import SSH, SFTP

logger = logging.getLogger(__name__)


def _log_step(msg: str):
    logger.info('=' * 50)
    logger.info(msg)
    logger.info('=' * 50)


class ControlServer:
    """
    The ControlServer in the Cloudformation template.
    """
    def __init__(self, host: str, username: str, keyfile: str):
        self.host = host
        self.username = username
        self.keyfile = keyfile

        self.ssh = SSH(host)
        self.ssh.login(username, keyfile)
        self.tidb_host = '10.0.1.11'  # keep the same as tidb-topology.yaml

    def _put_ssh_key(self):
        logger.info('SCP SSH private key to ControlServer')
        # All EC2 instances share the same key, so copy the private key to ControlServer
        rsa_path = f'/home/{self.username}/.ssh/id_rsa'
        SFTP(self.host, 22, self.username, self.keyfile).put(self.keyfile, rsa_path)
        self.ssh.exec_cmd(f'chmod 600 {rsa_path}')

    def install_tiup(self):
        """
        Add SSH key, install sshpass and TiUP.
        """
        _log_step('Add SSH key, install sshpass and TiUP')

        self._put_ssh_key()

        cmds = [
            'sudo apt update',
            'sudo apt install -y sshpass',
            "curl --proto '=https' --tlsv1.2 -sSf https://tiup-mirrors.pingcap.com/install.sh | sh",
        ]

        for cmd in cmds:
            self.ssh.exec_cmd(cmd)

    def install_tidb(self, template_path: str, version: str):
        """
        Install TiDB with TiUP, and start TiDB cluster.
        """
        _log_step('Install TiDB with TiUP, and start TiDB cluster')

        yaml = f'/home/{self.username}/tidb-template.yaml'
        SFTP(self.host, 22, self.username, self.keyfile).put(template_path, yaml)

        cmd = f"yes | tiup cluster deploy tidb-test {version} {yaml} --user {self.username}"
        self.ssh.exec_cmd(cmd)

        self.ssh.exec_cmd('tiup cluster start tidb-test')
        self.ssh.exec_cmd('tiup cluster display tidb-test')

    def install_go_tpc(self, version: str = '1.0.4'):
        """
        Download go-tpc from Github.
        """
        _log_step('Download go-tpc from Github onto ControlServer')

        url = ('https://github.com/pingcap/go-tpc/releases/download/'
               f'v{version}/go-tpc_{version}_linux_amd64.tar.gz')
        self.ssh.exec_cmd(f'wget "{url}"')
        self.ssh.exec_cmd('tar xzf go-tpc_1.0.4_linux_amd64.tar.gz')

    def prepare_data(self, warehouses: int = 4, parts: int = 4):
        """
        Insert data into TiDB.
        """
        _log_step('Insert test data into TiDB')

        cmd = f'./go-tpc tpcc -H {self.tidb_host} --warehouses {warehouses} --parts {parts} prepare'
        self.ssh.exec_cmd(cmd, timeout=300)

    def clean_data(self, warehouses: int = 4):
        """
        Clean the prepared data.
        """
        _log_step('Clean the prepared data')
        cmd = f'./go-tpc tpcc -H {self.tidb_host} --warehouses {warehouses} cleanup'
        self.ssh.exec_cmd(cmd, timeout=300)

    def benchmark(self, threads: int = 25, time: int = 60, warehouses: int = 4):
        """
        Benchmark with go-tpc.
        """
        _log_step('Benchmark with go-tpc')

        cmd = (f'./go-tpc tpcc -H {self.tidb_host} '
               f'-T {threads} --time {time}s --warehouses {warehouses} run')
        self.ssh.exec_cmd(cmd)
