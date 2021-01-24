"""
Install and benchmark TiDB via the ControlServer.
"""
from libs.ssh import SSH, SFTP


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

    def _put_ssh_key(self):
        # All EC2 instances share the same key, so copy the private key to ControlServer
        rsa_path = f'/home/{self.username}/.ssh/id_rsa'
        SFTP(self.host, 22, self.username, self.keyfile).put(self.keyfile, rsa_path)
        self.ssh.exec_cmd(f'chmod 600 {rsa_path}')

    def install_tiup(self):
        """
        Add SSH key, install sshpass and TiUP.
        """
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
        Install TiDB with TiUP.
        """
        yaml = f'/home/{self.username}/tidb-template.yaml'
        SFTP(self.host, 22, self.username, self.keyfile).put(template_path, yaml)

        cmd = f"yes | tiup cluster deploy tidb-test {version} {yaml} --user {self.username}"
        self.ssh.exec_cmd(cmd)
