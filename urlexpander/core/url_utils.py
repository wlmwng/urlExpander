"""Functions for parsing and standardizing URLs.
"""

__all__ = ["is_short", "get_domain", "standardize_url", "is_generic_url"]

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


def standardize_url(
    url,
    remove_scheme=True,
    replace_netloc_with_domain=False,
    remove_path=False,
    remove_query=False,
    remove_fragment=True,
    to_lowercase=True,
):
    """Standardize the URL.
    At minimum, the URL is canonicalized and and common advertising analytics params are removed.
    The URL is then parsed into five components for further cleaning using urllib.parse.urlsplit().
    If the default options are used, only the scheme and fragment are removed.

    "URL Syntactic Components": <scheme>://<net_loc>/<path>;<params>?<query>#<fragment>
    https://www.rfc-editor.org/rfc/rfc1808.html#section-2.1

    Note: urllib.parse.urlsplit() does not split <params> from the URL because
    "more recent URL syntax allows parameters to be applied to each segment of the path portion of the URL".
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlsplit

    :param url: URL
    :type url: str
    :param remove_scheme: remove the scheme (e.g., http, https)
    :type remove_scheme: bool
    :param replace_netloc_with_domain: replace the network location with its domain name
        - e.g., replaces "amp.dailycaller.com" with "dailycaller.com"
    :type replace_netloc_with_domain: bool
    :param remove_path: remove the path
    :type remove_path: bool
    :param remove_query: remove the query params
    :type remove_query: bool
    :param remove_fragment: remove the fragment
        - a fragment isn't officially a URL component, but it is recognized by parsers
    :type remove_fragment: bool
    :param to_lowercase: lowercase the standardized version of the URL
    :type to_lowercase: bool
    :returns link: the standardized version of the URL
        - depending on the selected cleaning steps, this link may not conform to RFC 1808 Section 2.1
    :rtype: str
    """

    try:

        # 1) canonicalize the URL
        # https://w3lib.readthedocs.io/en/latest/w3lib.html#w3lib.url.canonicalize_url
        link = w3lib.url.canonicalize_url(url)

        # 2) remove advertising campaign parameters
        link = w3lib.url.url_query_cleaner(
            link, constants.analytics_parameters, remove=True
        )

        # remove google amp prefix if it exists
        # https://www.theverge.com/2019/4/16/18402628/google-amp-url-problem-signed-exchange-original-chrome-cloudflare
        link = re.sub("^http(s)?:\/\/www\.google\.com\/amp\/s\/", "", link)

        # 3) parse the URL into its components and modify as needed
        parsed = urllib.parse.urlsplit(link)
        scheme = parsed.scheme
        netloc = parsed.netloc
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment

        if remove_scheme:
            scheme = ""
        if replace_netloc_with_domain:
            netloc = get_domain(link)
        if remove_path:
            path = ""
        if remove_query:
            query = ""
        if remove_fragment:
            fragment = ""

        link = parsed._replace(
            scheme=scheme,
            netloc=netloc,
            path=path,
            query=query,
            fragment=fragment,
        )

        # 4) put the components back together
        link = urllib.parse.urlunsplit(link)

        # 5) remove extra slashes which may exist
        if remove_scheme:
            # remove double forward slashes if they are at the front of the string
            link = re.sub("^\/\/", "", link)

        # remove the front-slash at the end of the string
        link = re.sub("\/$", "", link)

        # 6) lowercase the string
        if to_lowercase:
            link = link.lower()

        return link

    except Exception as exc:
        LOGGER.info(
            f"urlexpander.url_utils.standardize_url() failed with {url}, {str(exc)}"
        )
        return "ERROR"


def is_generic_url(url):
    """Check if a URL likely leads to a generic homepage (e.g., 'cnn.com')

    This indicator can be helpful for filtering out noise in the scraped data;
    e.g., when a server can't provide the originally requested page and
    redirects to a homepage.

    :param url: URL
    :type url: str
    :returns: is_generic-> True if the standardized URL equals the base URL
    :rtype: bool

    """

    standardized_url = standardize_url(
        url=url,
        remove_scheme=True,
        replace_netloc_with_domain=False,
        remove_path=False,
        remove_query=False,
        remove_fragment=True,
        to_lowercase=True,
    )

    base_url = standardize_url(
        url=url,
        remove_scheme=True,
        replace_netloc_with_domain=False,
        remove_path=True,
        remove_query=True,
        remove_fragment=True,
        to_lowercase=True,
    )

    if all(
        [standardized_url != "ERROR", base_url != "ERROR", standardized_url == base_url]
    ):
        is_generic = True
    else:
        is_generic = False

    return is_generic
