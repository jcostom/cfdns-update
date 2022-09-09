#!/usr/bin/env python3

import logging
import os
import os.path
import requests
import telegram
from time import strftime, sleep

# --- To be passed in to container ---
# Required Vars
IPADDR_SRC = os.getenv('IPADDR_SRC', 'https://ipv4.icanhazip.com/')
INTERVAL = os.getenv('INTERVAL', 300)
APITOKEN = os.getenv('APITOKEN')
ZONEID = str(os.getenv('ZONEID'))
RECORDS = os.getenv('RECORDS')
TTL = os.getenv('TTL', 1)

# Optional Vars
PROXIED = str(os.getenv('PROXIED', 'false'))
USETELEGRAM = int(os.getenv('USETELEGRAM', 0))
CHATID = int(os.getenv('CHATID', 0))
MYTOKEN = os.getenv('MYTOKEN', 'none')
SITENAME = os.getenv('SITENAME', 'mysite')
DEBUG = int(os.getenv('DEBUG', 0))

# --- Globals ---
VER = '0.3.1'
USER_AGENT = f"cfdns-update.py/{VER}"
IPCACHE = "/config/ip.cache.txt"

# Setup logger
logger = logging.getLogger()
ch = logging.StreamHandler()
if DEBUG:
    logger.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)

formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s',
                              datefmt='[%d %b %Y %H:%M:%S %Z]')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_current_ip(ip_url: str) -> str:
    return requests.get(ip_url).text.rstrip('\n')


def ip_changed(ip: str) -> bool:
    with open(IPCACHE, "r") as f:
        cached_ip = f.read()
        if cached_ip == ip:
            return False
        else:
            return True


def update_cache(ip: str) -> int:
    with open(IPCACHE, "w+") as f:
        f.write(ip)
    return 0


def send_notification(msg: str, chat_id: int, token: str) -> None:
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg)
    logger.info('Telegram Group Message Sent')


def break_up_records(records: str) -> dict:
    # Breakup passed list of records, strip any spaces
    # Setup dict to be populated to map record
    # Cloudflare's record_id value.
    return dict.fromkeys([record.strip() for record in records.split(',')], 'id')  # noqa E501


def create_cfdns_headers(api_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    return headers


def create_cfdns_get_req(url: str, api_token: str) -> requests.Response:
    headers = create_cfdns_headers(api_token)
    return requests.get(url, headers=headers)


def get_cfdns_domain_name(zone_id: str, api_token: str) -> str:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
    r = create_cfdns_get_req(url, api_token)
    # Locate and return the zone's name
    return r.json()['result']['name']


def get_cfdns_record_id(zone_id: str, api_token: str, record_name: str,
                        domain_name: str) -> str:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}.{domain_name}"  # noqa E501
    r = create_cfdns_get_req(url, api_token)
    return r.json()['result'][0]['id']


def update_cfdns_record(zone_id: str, api_token: str,
                        record: list, ip: str) -> requests.Response:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record[1]}"  # noqa E501
    data = f'{{"type":"A","name":"{record[0]}","content":"{ip}","ttl":{TTL},"proxied":{PROXIED}}}'  # noqa E501
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}  # noqa E501
    return requests.patch(url, headers=headers, data=data)


def send_updates(zone_id: str, api_token: str, records: dict,
                 ip: str, domain: str) -> None:
    for record in records.items():
        update_cfdns_record(zone_id, api_token, record, ip)
        if USETELEGRAM:
            now = strftime("%B %d, %Y at %H:%M")
            notification_text = f"[{SITENAME}] {record[0]}.{domain} changed on {now}. New IP == {ip}."  # noqa E501
            send_notification(notification_text, CHATID, MYTOKEN)


def main() -> None:
    # break up string of records into dict of record/id pairs
    my_records = break_up_records(RECORDS)
    my_domain = get_cfdns_domain_name(ZONEID, APITOKEN)

    # Load dict with record id's
    for record_name, id in my_records.items():
        my_records[record_name] = get_cfdns_record_id(ZONEID, APITOKEN, record_name, my_domain)  # noqa E501

    while True:
        # Grab current IP
        current_ip = get_current_ip(IPADDR_SRC)

        # check to see if cache file exists and take action
        if os.path.exists(IPCACHE):
            if ip_changed(current_ip):
                update_cache(current_ip)
                logger.info(f"IP changed to {current_ip}")
                # Update DNS & Check Telegram
                send_updates(ZONEID, APITOKEN, my_records, current_ip, my_domain)  # noqa E501
            else:
                logger.info('No change in IP, no action taken.')
        else:
            # No cache exists, create file
            update_cache(current_ip)
            logger.info(f"No cached IP, setting to {current_ip}")
            # Update DNS & Check Telegram
            send_updates(ZONEID, APITOKEN, my_records, current_ip, my_domain)  # noqa E501

        sleep(INTERVAL)


if __name__ == "__main__":
    main()
