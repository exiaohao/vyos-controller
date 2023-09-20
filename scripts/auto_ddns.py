import os
import socket
from vyos.configsession import ConfigSession
from vyos.util import get_interface_config

TUNNEL_NAME = "tun0"
LOCAL_DOMAIN = "LOCAL-DOMAIN"
REMOTE_DOMAIN = "REMOTE-DOMAIN"

TYPE_TUN = 1


class UpdateAddress:
    INTERFACE_MAP = {
        TYPE_TUN: ["tunnel", {"local":"source-address", "remote":"remote"}],
    }

    def __init__(self, interface_type, interface_name, local_domain, remote_domain):
        self.interface_type = interface_type
        self.interface_name = interface_name
        self.local_domain = local_domain
        self.remote_domain = remote_domain
        self.check_and_update()

    def check_and_update(self):
        need_update_local, need_update_remote = self._is_address_changed()
        if need_update_local:
            local = self.INTERFACE_MAP.get(self.interface_type)[1]["local"]
            self._update_address(local, self.local_domain_ip)
        else:
            print("Same local address, skip update")

        if need_update_remote:
            remote = self.INTERFACE_MAP.get(self.interface_type)[1]["remote"]
            self._update_address(remote, self.remote_domain_ip)
        else:
            print("Same remote address, skip update")

    def _is_address_changed(self):
        existing_tunnel = get_interface_config(self.interface_name)

        self.local_domain_ip = socket.gethostbyname(self.local_domain)
        self.remote_domain_ip = socket.gethostbyname(self.remote_domain)

        if existing_tunnel is None:
            print("no such interface:", self.interface_name) # todo
            os.Exit(-1)

        info_data = existing_tunnel["linkinfo"]["info_data"]
        print("Current\tLocal:{}\t<>\t{}\r\n\tRemote:{}\t<>\t{}".format(
            info_data.get("local"),
            self.local_domain_ip,
            info_data.get("remote"),
            self.remote_domain_ip,
        ))
        return info_data.get("local") != self.local_domain_ip, info_data.get("remote") != self.remote_domain_ip

    def _update_address(self, param, address):
        _cfg_path = "/config/config.boot"
        _int_type = self.INTERFACE_MAP[self.interface_type][0]

        session = ConfigSession(os.getpid())
        session.migrate_and_load_config(_cfg_path)
        session.set(["interfaces", _int_type, self.interface_name, param], address)
        session.commit()
        session.save_config(_cfg_path)
        print("Update interface<{}> {} to {}".format(self.interface_name, param, address))


if __name__ == "__main__":
    ua = UpdateAddress(TYPE_TUN, TUNNEL_NAME, LOCAL_DOMAIN, REMOTE_DOMAIN)

