from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

import config
from utils.logger import get_logger

log = get_logger("api.client")

_api = None


def init_api() -> FacebookAdsApi:
    global _api
    if _api is not None:
        return _api

    missing = [k for k in ["META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]
               if not getattr(config, k)]
    if missing:
        raise EnvironmentError(
            f"Missing required env vars: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your Meta credentials."
        )

    _api = FacebookAdsApi.init(
        app_id=config.META_APP_ID,
        app_secret=config.META_APP_SECRET,
        access_token=config.META_ACCESS_TOKEN,
        api_version=config.API_VERSION,
    )
    log.debug("Meta API initialized.")
    return _api


def get_account() -> AdAccount:
    init_api()
    account_id = config.META_AD_ACCOUNT_ID
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    return AdAccount(account_id)
