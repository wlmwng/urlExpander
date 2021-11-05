"""Functions for parsing and standardizing URLs.
"""

__all__ = ["is_short", "get_domain"]

import logging
import re
import urllib.parse

import tldextract
import w3lib.url
from urlexpander.core import constants

LOGGER = logging.getLogger(__name__)


def is_short(url, list_of_domains=constants.all_short_domains):
    """Check if a URL domain is a shortened one.

    Make sure that domain and list_of_domains is preprocessed (or not at all), in the same way.

    :param url: URL
    :type url: str
    :param list_of_domains: URL domains (Default value = constants.all_short_domains)
    :type list_of_domains: list
    :returns: is_short_url-> Returns True if a domain is a in a list of specified domains.
    :rtype: bool

    """

    try:
        domain = get_domain(url)

        is_short_url = False
        if domain in list_of_domains:
            is_short_url = True
        return is_short_url

    except Exception as exc:
        LOGGER.info(
            f"urlexpander.url_utils.is_short_url() failed with {url}, {str(exc)}"
        )
        return "ERROR"


def get_domain(url):
    """Returns domain name of a URL (and removes "www.")

    e.g. 'https://www.nytimes.com/2016/12/23/upshot/...' to 'nytimes.com'

    :param url: URL
    :type url: str
    :returns: domain-> domain name of URL
    :rtype: str

    """
    try:
        extracted = tldextract.extract(url)
        if extracted.suffix == "" or extracted.domain == "":
            domain = url
        elif extracted.subdomain == "":
            domain = f"{extracted.domain}.{extracted.suffix}"
        else:
            domain = f"{extracted.domain}.{extracted.suffix}"
        domain = domain.lower()
        return domain

    except Exception as exc:
        LOGGER.info(f"urlexpander.url_utils.get_domain() failed with {url}, {str(exc)}")
        return "ERROR"

