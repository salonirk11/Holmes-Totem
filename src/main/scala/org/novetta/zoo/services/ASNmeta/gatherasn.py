import dns
import dns.name
import dns.query
import dns.resolver
import ipaddress

class GatherASN:
    def _reverse_address(self, ipaddress, version):
        if version == 4:
            return ".".join(ipaddress.split(".")[::-1])
        elif version == 6:
            ip = ipaddress.replace('::', '+')
            ip = ip.replace(':', '')
            if '+' in ip:
                iplength = len(ip) - 1
                ip = ip.replace('+', '0'*(32 - iplength))
            return '.'.join(ip[::-1])
        return None    


    def _get_version(self, ipaddress):
        return ipaddress.ip_address(ipaddress).version

    def _parse_results(self, data):
        return [out.strip() for out in data.rrset[0].strings[0].split('|')]


    def _perform_query(self, domain, rdtype):
        """
        Performs a DNS (UDP) query with flags and configurations parameters.

        Args: 
            domain (str): sdomain i.e. google.com
            nnserver (str): nameserver to query
            rtype (str or int): rtype to query http://en.wikipedia.org/wiki/List_of_DNS_record_types
            timeout (int): time to wait before timeout        

        """
        domain = dns.name.from_text(domain)

        try:
            result = self.resolver.query(domain, rdtype=rdtype)
        except dns.resolver.NoAnswer:
            print("%s : The response did not contain a answer for %s." % (rdtype, domain))
        except dns.resolver.NXDOMAIN:
            print("%s : The query name does not exist for %s." % (rdtype, domain))
        except dns.resolver.Timeout:
            print("%s : The query could not be found in the specified lifetime for %s." % (rdtype, domain))
        except dns.resolver.NoNameservers:
            print("%s : No non-broken nameservers are available to answer the question using nameserver %s" % (rdtype, domain))
        else:
            print("%s : Queried %s successfully!" % (rdtype, domain))
            return result
        return None


    def query_asn_name(self, asn):
        parsed_ip = "{0}.{1}".format(asn, self.servername) 

        query_result = self._perform_query(parsed_ip, 'TXT')

        temp = self._parse_results(query_result)
        self.data['asn_number']     = temp[0]
        self.data['cc']             = temp[1]
        self.data['registry']       = temp[2]
        self.data['data_allocated'] = temp[3]
        self.data['asn_name']       = temp[4]


    def query_asn_origin(self, ipaddress):
        version = self._get_version(ipaddress)
        reversed_ip = self._reverse_address(ipaddress, version)
        
        if version == 4:
            parsed_ip = "{0}.{1}".format(reversed_ip, self.serverv4) 
        elif version == 6:
            parsed_ip = "{0}.{1}".format(reversed_ip, self.serverv6) 

        query_result = self._perform_query(parsed_ip, 'TXT')

        temp = self._parse_results(query_result)
        self.data['asn_number'] = temp[0]
        self.data['bgp_prefix'] = temp[1]
        self.data['cc']         = temp[2]
        self.data['registry']   = temp[3]
        self.data['data_allocated'] = temp[4]


    def query_asn_peer(self, ipaddress):
        version = self._get_version(ipaddress)
        reversed_ip = self._reverse_address(ipaddress, version)
        
        parsed_ip = "{0}.{1}".format(reversed_ip, self.serverpeer) 

        query_result = self._perform_query(parsed_ip, 'TXT')

        temp = self._parse_results(query_result)
        self.data['asn_peers']  = temp[0].split(' ')
        self.data['bgp_prefix'] = temp[1]
        self.data['cc']         = temp[2]
        self.data['registry']   = temp[3]
        self.data['data_allocated'] = temp[4]


    def get_asn_name(self):
        return self.data.get('asn_name', None)


    def get_asn_number(self):
        return self.data.get('asn_number', None)


    def get_asn_peers(self):
        return self.data.get('asn_peers', None)


    def get_bgp_prefix(self):
        return self.data.get('bgp_prefix', None)


    def get_cc(self):
        return self.data.get('cc', None)


    def get_registry(self):
        return self.data.get('registry', None)


    def get_date_allocated(self):
        return self.data.get('data_allocated', None)


    def get_all_known_data(self):
        return self.data

    
    def __init__(self, nsserver, serverv4, serverv6, serverpeer, servername, timeout=10):
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [nsserver]
        self.resolver.timeout = timeout
        self.resolver.lifetime = 50
        self.serverv4 = serverv4
        self.serverv6 = serverv6
        self.serverpeer = serverpeer
        self.servername = servername

        self.data = {}