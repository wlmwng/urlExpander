"""
This module extends the package's core functions to collect information related to news articles.
The NewsContent class acts as a template which is filled out by the fetching functions.
The output of every fetching function is a stringified JSON object, which can be
written to a .jsonl file or passed to a database.
"""

__all__ = [
    "request_active_url",
    "request_archived_url",
    "fetch_url",
    "fetch_urls",
    "fetch_urls_to_file",
    "load_fetched_from_file",
]

import datetime
import inspect
import json
import logging
import os
import re
import time
from random import randint

import newspaper
import waybackpy
from newsplease import NewsPlease
from urlexpander.core import api, constants, url_utils
from waybackpy.exceptions import URLError, WaybackError

LOGGER = logging.getLogger(__name__)


class NewsContent:
    """The fetching functions hydrate instances of this class.

    :param original_url: URL
    :type original_url: str
    :param **kwargs:
        - each kwarg is added as an attribute along with its provided value.
        - both the argument and the value must be JSON serializable: see to_json().
        - e.g., if "outlet=CNN" is a kwarg, "self.outlet" is added with a value of "CNN".

    """

    def __init__(
        self,
        original_url,
        **kwargs,
    ):

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.article_maintext = ""
        self.original_url = original_url
        # self.response_url = ""
        self.resolved_url = ""
        self.resolved_domain = ""
        self.resolved_netloc = ""
        self.standardized_url = ""
        self.is_generic_url = ""

        # for troubleshooting
        self.response_code = ""
        self.response_reason = ""
        self.fetch_error = ""
        # processed response text (HTML):
        # backup option which can be parsed if `article_maintext` returns None
        self.resolved_text = ""
        # https://stackoverflow.com/a/5067654
        self.FETCH_FUNCTION = inspect.currentframe().f_back.f_code.co_name
        self.FETCH_AT = datetime.datetime.now(datetime.timezone.utc)

    def set_article_maintext(self):
        """Extract the article text from the HTML with NewsPlease"""

        try:
            article = NewsPlease.from_html(
                html=self.resolved_text, url=self.resolved_url
            )
            self.article_maintext = article.maintext
        except newspaper.article.ArticleException as exc:
            LOGGER.info(
                f"Failed to extract article's maintext due to ArticleException, {str(exc)}",
            )
            self.article_maintext = ""
        except Exception as exc:
            LOGGER.info(
                f"Failed to extract article's maintext due to unknown exception, {str(exc)}",
            )
            self.article_maintext = ""

    def set_fetch_error_ind(self):
        """Set indicator for whether a fetch attempt resulted in an error"""
        is_err = False
        if self.FETCH_FUNCTION == "request_active_url":
            if "ERROR" in self.resolved_url:
                is_err = True
        elif self.FETCH_FUNCTION == "request_archived_url":
            if self.response_reason != "OK":
                is_err = True
        self.fetch_error = is_err

    def set_url_versions(self):
        """Set URL versions"""
        url = self.resolved_url
        self.resolved_netloc = url_utils.standardize_url(
            url=url,
            remove_scheme=True,
            replace_netloc_with_domain=False,
            remove_path=True,
            remove_query=True,
            remove_fragment=True,
            to_lowercase=True,
        )
        self.standardized_url = url_utils.standardize_url(
            url=url,
            remove_scheme=True,
            replace_netloc_with_domain=False,
            remove_path=False,
            remove_query=False,
            remove_fragment=True,
            to_lowercase=True,
        )

    def set_generic_url_ind(self):
        """Set indicator for whether a URL is generic"""
        self.is_generic_url = url_utils.is_generic_url(self.resolved_url)

    def to_json(self):
        """Convert NewsContent instance into a JSON string"""
        # https://stackoverflow.com/a/27058505
        class CustomEncoder(json.JSONEncoder):
            """
            Default JSON serializable types are bool, int, float, and str.
            CustomEncoder is a subclass of json.JSONEncoder.
            It modifies datetime and dictionary types to make them JSON serializable.
            Modify this subclass to address other non-primitive types.
            """

            def default(self, o):
                if isinstance(o, datetime.datetime):
                    # https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat
                    # Return a string representing the date and time in ISO 8601 format
                    # e.g., '2019-05-18T15:17:00+00:00'
                    return o.isoformat()
                elif isinstance(o, dict):
                    return json.dumps(o)
                return json.JSONEncoder.default(self, o)

        fetched = self.__dict__
        fetched_json = json.dumps(fetched, cls=CustomEncoder)
        return fetched_json


def load_fetched_from_file(path, filename):
    """Load fetched content from .jsonl file.

    :param path: path to the directory
    :type path: str
    :param filename: name of the file
    :type filename: str
    :returns data: fetched content as stringified JSON object
    :rtype data: Generator[str]

    """
    json_file = os.path.join(path, filename)
    if json_file and os.path.exists(json_file):
        with open(file=json_file, mode="r", encoding="utf-8") as file:
            for line in file:
                data = line  # json.loads(line)
                yield data


def fetch_urls_to_file(
    urls,
    fetch_function,
    path="",
    filename="fetched.jsonl",
    write_mode="a",
    verbose=1,
):
    """Fetch the webpage contents for one URL or multiple URLs.
    Outputs file where each line contains a URL's fetched content (stringified JSON object).

    :param urls: URL(s) to fetch
        - required: 'url' key
        - optional: additional key-value pairs are passed along to the output
    :param fetch_function: request_active_url, request_archived_url, fetch_url
    :type fetch_function: function
    :param path: output directory path (Default value = "")
    :type path: str
    :param filename:  (Default value = "fetched.jsonl")
    :type filename: str
    :param write_mode: "a" to append (Default value = "a")
    :type write_mode: str
    :param verbose: 0 - don't print progress, 1 - print progress (Default value = 1)
    :type verbose: bool
    :returns: None

    """

    if isinstance(urls, dict):
        urls = [urls]

    for n, url_dict in enumerate(urls):
        # dictionaries are mutable so work off a copy to avoid modifying the input
        d = url_dict.copy()
        try:
            # Collect the value of the 'url' key if it exists and
            # remove it from the dictionary before calling fetch_function.
            # the remaining key-values are passed as optional kwargs.
            url = d.pop("url")
            LOGGER.info((f"url {n}, {fetch_function.__name__}: {url}"))

            msg = f"url {n}, {fetch_function.__name__}: {url}"
            LOGGER.info(msg)
            if verbose:
                print(msg)

            data = fetch_function(url=url, **d)
            with open(
                file=os.path.join(path, filename), mode=write_mode, encoding="utf-8"
            ) as file:
                # https://stackoverflow.com/a/12451465
                file.write(data + "\n")

        except KeyError:
            LOGGER.error(
                "Fetch failed to start, please provide a 'url' key-value in the input dictionary."
            )


def fetch_urls(urls, fetch_function, verbose=1):
    """Fetch the webpage contents for one URL or multiple URLs.

    :param urls: URL(s) to fetch
        - required: 'url' key
        - optional: additional key-value pairs are passed along to the output
    :param fetch_function: request_active_url, request_archived_url, fetch_url
    :type fetch_function: function
    :param verbose: 0 - don't print progress, 1 - print progress (Default value = 1)
    :type verbose: bool
    :returns data: fetched content as stringified JSON object
    :rtype data: Generator[str]

    """

    if isinstance(urls, dict):
        urls = [urls]

    for n, url_dict in enumerate(urls):
        # dictionaries are mutable so work off a copy to avoid modifying the input
        d = url_dict.copy()
        try:
            # Collect the value of the 'url' key if it exists and
            # remove it from the dictionary before calling fetch_function.
            # the remaining key-values are passed as optional kwargs.
            url = d.pop("url")

            msg = f"url {n}, {fetch_function.__name__}: {url}"
            LOGGER.info(msg)
            if verbose:
                print(msg)

            data = fetch_function(url=url, **d)
            yield data

        except KeyError:
            LOGGER.error(
                "Fetch failed to start, please provide a 'url' key-value in the input dictionary."
            )


def fetch_url(url, timeout=10, **kwargs):
    """Fetch the URL directly or from an archive.
    First try to fetch the content directly from the URL domain's servers.
    If it fails, then try to fetch the content from an archived version of the URL.

    :param url: URL
    :type url: str
    :param timeout:  (Default value = 10)
    :param **kwargs:
    :returns: fetched-> fetched content as stringified JSON object
    :rtype: str
    """
    LOGGER.info(f"fetching URL: {url}")

    active_json = request_active_url(
        url=url,
        timeout=timeout,
        **kwargs,
    )

    active_data = json.loads(active_json)
    if active_data["fetch_error"]:
        archived_json = request_archived_url(
            url=url,
            **kwargs,
        )

        fetched = archived_json
        LOGGER.info(
            "Failed with request_active_url, returning fetched content from request_archived_url."
        )

    else:
        fetched = active_json
        LOGGER.info("Succeeded with request_active_url, returning fetched content.")

    return fetched


def request_active_url(url, timeout=10, **kwargs):
    """Request the webpage directly from the URL domain

    :param url: URL
    :type url: str
    :param timeout: how many seconds to wait for a response (Default value = 10)
    :type timeout: int
    :param **kwargs:
    :returns: fetched-> as stringified JSON object
    :rtype: str

    """

    fetched = NewsContent(
        original_url=url,
        **kwargs,
    )

    # urlExpander.expand_with_content already includes a time delay

    # send the request
    LOGGER.info(f"request_active_url: {url}")
    r = api.expand_with_content(url=url, timeout=timeout)

    # hydrate the instance with the response info
    fetched.resolved_url = r["resolved_url"]
    fetched.resolved_domain = r["resolved_domain"]
    fetched.resolved_text = r["resolved_text"]

    # fetched.response_url = r["response_url"]
    fetched.response_code = r["response_code"]
    fetched.response_reason = r["response_reason"]

    fetched.set_fetch_error_ind()
    fetched.set_article_maintext()
    fetched.set_url_versions()
    fetched.set_generic_url_ind()

    fetched_json = fetched.to_json()
    return fetched_json


def request_archived_url(url, **kwargs):
    """Request the oldest version of the webpage from the Internet Archive's Wayback Machine

    :param url: URL
    :type url: str
    :param **kwargs:
    :returns: fetched-> as stringified JSON object
    :rtype: str

    """

    fetched = NewsContent(original_url=url, **kwargs)

    # canonicalize, remove common ad analytics query params, remove fragment
    # this step may help improve the archive hit rate
    url = url_utils.standardize_url(
        url=url,
        remove_scheme=False,
        replace_netloc_with_domain=False,
        remove_path=False,
        remove_query=False,
        remove_fragment=True,
        to_lowercase=False,
    )

    time.sleep(randint(constants.MIN_DELAY, constants.MAX_DELAY))

    try:
        # send the request
        LOGGER.info(f"request_archived_url: {url}")
        wayback = waybackpy.Url(url, constants.headers["User-Agent"])
        archive = wayback.oldest()
        wbm_url = archive.archive_url
        wbm_html = archive.get()
        # fetched.response_url = wbm_url
        # remove prefix URL from Wayback Machine
        fetched.resolved_url = re.sub(
            "^http(s)?:\/\/web\.archive\.org\/web\/\d+\/", "", wbm_url
        )
        fetched.resolved_domain = url_utils.get_domain(fetched.resolved_url)
        fetched.resolved_text = wbm_html
        fetched.response_code = 200
        fetched.response_reason = "OK"

    # https://github.com/akamhy/waybackpy/blob/6c71dfbe41ce8791ebd352817e6cfc0833f38140/waybackpy/exceptions.py
    except WaybackError:  # 'Can not find archive for ___'
        msg = "WaybackError, API down or invalid arguments"
        LOGGER.warning(msg)
        fetched.response_code = float("nan")
        fetched.response_reason = msg

    except URLError:
        msg = "URLError, malformed URL"
        LOGGER.warning(msg)
        fetched.response_code = float("nan")
        fetched.response_reason = msg

    except Exception as exc:
        msg = f"Unknown error, {str(exc)}"
        LOGGER.warning(msg)
        fetched.response_code = float("nan")
        fetched.response_reason = msg

    fetched.set_fetch_error_ind()
    fetched.set_article_maintext()
    fetched.set_url_versions()
    fetched.set_generic_url_ind()

    fetched_json = fetched.to_json()
    return fetched_json
