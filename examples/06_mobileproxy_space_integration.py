"""
Example 06: Seamless Avito Scraping with MobileProxy.space.

Real 4G/LTE mobile proxies from MobileProxy.space eliminate IP bans
because cellular carriers (MTS, Megafon, Beeline, Tele2) share millions of users
over dynamic NAT IP pools. Avito cannot ban entire mobile subnets.

Get your high-speed mobile proxy and rotation key at:
https://mobileproxy.space/?p=279117
Free 3-hour test for new clients:
https://mobileproxy.space/user.html?free&p=279117
"""

import os
from avito_sdk import AvitoClient, MobileProxySpace

# 1. Direct rotation via MobileProxySpace helper
# In your dashboard: https://mobileproxy.space/?p=279117
# Copy your proxy credentials and unique rotation key from "My Proxies":
PROXY_URL = os.getenv("AVITO_PROXY", "http://login:password@proxy-domain.space:port")
MOBILEPROXY_KEY = os.getenv("MOBILEPROXY_KEY", "your_proxy_key_here")

mps = MobileProxySpace(
    proxy_key=MOBILEPROXY_KEY,
    proxy_url=PROXY_URL,
    reconnect_delay=4.0,  # recommended 3-5s for mobile tower reconnection
)

print(f"[*] Referral portal: https://mobileproxy.space/?p=279117")
print(f"[*] Free 3h test: https://mobileproxy.space/user.html?free&p=279117")
print(f"[*] Rotation URL: {mps.change_url}")

# 2. Trigger programmatic IP rotation
# resp = mps.rotate_ip(wait_reconnect=True)
# print(f"[*] New public IP: {resp.get('new_ip')}")

# 3. Initialize AvitoClient with automatic MobileProxy.space rotation
# Whenever Avito returns 403 or 429, AvitoClient automatically invokes MobileProxy.space
# to obtain a new carrier IP, wait for connection stability, and retry the request.
client = AvitoClient(
    proxy=PROXY_URL,
    mobileproxy_key=MOBILEPROXY_KEY,  # or pass proxy_change_url directly
    timeout=25,
)

print("[*] Scraping Avito with auto-rotating mobile proxy...")
# items = list(client.search("iPhone 15 Pro", region="moskva", limit=10))
# print(f"[✓] Collected {len(items)} listings without IP bans!")
