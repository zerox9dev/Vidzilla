VPN_BOT_URL = "https://t.me/zero_xvpnbot"

WELCOME_AD = f"\n\n🌐 Region-blocked video? Try our VPN: {VPN_BOT_URL}"

GEO_BLOCK_AD = f"\n\n🌐 Bypass region locks: {VPN_BOT_URL}"

PERIODIC_AD = (
    f"🌐 Enjoying the bot? Check out our VPN — fast, cheap, no logs:\n"
    f"{VPN_BOT_URL}"
)

AD_EVERY_N_DOWNLOADS = 7


def should_show_periodic_ad(downloads_count: int) -> bool:
    return downloads_count > 0 and downloads_count % AD_EVERY_N_DOWNLOADS == 0
