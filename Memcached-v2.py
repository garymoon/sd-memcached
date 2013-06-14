#!/usr/bin/env python
import sys
import getopt
import telnetlib
import re
import socket
import time
import StringIO

class Memcached:
    def __init__(self, agentConfig, checksLogger, rawConfig):
        self.agentConfig = agentConfig
        self.checksLogger = checksLogger
        self.rawConfig = rawConfig

        if self.agentConfig is None:
            self.set_default_config()

        if ('Memcached' not in self.agentConfig):
            self.set_default_config()

    def set_default_config(self):
        self.agentConfig = {}
        self.agentConfig['Memcached'] = {'host': 'localhost', 'port': '11211'}

    def run(self):
        stats = {}
        
        host = self.agentConfig['Memcached']['host']
        port = int(self.agentConfig['Memcached']['port'])
        
        ts = str(int(time.time()))
        ts_len = len(ts)

        try:
            telnet = telnetlib.Telnet()
            telnet.open(host, port)
            telnet.write('stats\r\n')

            out = telnet.read_until("END", 1)

            telnet.write('set __monitor_test__ 0 10 %s\r\n' % ts_len)
            telnet.write('%s\r\n' % ts)
            test_set = telnet.read_until("STORED", 1)

            telnet.write('gets __monitor_test__\r\n')
            test_get = telnet.read_until("END", 1)

            telnet.write('quit\r\n')
            telnet.close()
        except socket.error, reason:
            sys.stderr.write("%s\n" % reason)
            sys.stderr.write("Is memcached running?\n")
            return { "status": "Memcache unreachable" }

        for stat in StringIO.StringIO(out):
            if not "STAT" in stat: continue
            stat = stat.strip().split(' ')
            stats[stat[1]] = stat[2]
            
        if "STORED" not in test_set:
            sys.stderr.write("Couldn't store ts\n")
            stats['status'] = "Couldn't store"
            return stats

        if ts not in test_get:
            sys.stderr.write("Couldn't get ts\n")
            stats['status'] = "Couldn't get"
            return stats

        stats['status'] = "1"

        return stats

if __name__ == '__main__':
    import pprint
    plugin = Memcached(None, None, None)
    pprint.pprint(plugin.run())
