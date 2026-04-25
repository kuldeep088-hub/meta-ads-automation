from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adset import AdSet

from api.client import get_account
import config
from utils.logger import get_logger

log = get_logger("api.ads")

AD_FIELDS = [
    "id", "name", "status", "adset_id", "campaign_id",
    "creative", "created_time", "updated_time",
]


def list_ads(adset_id: str) -> list:
    adset = AdSet(adset_id)
    ads = adset.get_ads(fields=AD_FIELDS)
    return [dict(a) for a in ads]


def create_ad_creative(
    name: str,
    headline: str,
    body: str,
    cta: str,
    image_url: str,
    link: str,
    page_id: str = None,
) -> dict:
    account = get_account()
    page_id = page_id or config.META_PAGE_ID

    link_data = {
        "message": body,
        "link": link,
        "name": headline,
        "call_to_action": {
            "type": cta,
            "value": {"link": link},
        },
    }
    if image_url:
        link_data["picture"] = image_url

    params = {
        AdCreative.Field.name: name,
        AdCreative.Field.object_story_spec: {
            "page_id": page_id,
            "link_data": link_data,
        },
    }
    creative = account.create_ad_creative(params=params)
    log.info(f"AdCreative created: {creative['id']}")
    return dict(creative)


def create_ad(
    name: str,
    adset_id: str,
    creative_id: str,
    status: str = "PAUSED",
) -> dict:
    account = get_account()
    params = {
        Ad.Field.name: name,
        Ad.Field.adset_id: adset_id,
        Ad.Field.creative: {"creative_id": creative_id},
        Ad.Field.status: status,
    }
    ad = account.create_ad(params=params)
    log.info(f"Ad created: {ad['id']}  -  {name}")
    return dict(ad)


def pause_ad(ad_id: str) -> bool:
    Ad(ad_id).api_update(params={Ad.Field.status: "PAUSED"})
    log.info(f"Ad paused: {ad_id}")
    return True


def resume_ad(ad_id: str) -> bool:
    Ad(ad_id).api_update(params={Ad.Field.status: "ACTIVE"})
    log.info(f"Ad resumed: {ad_id}")
    return True
