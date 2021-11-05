"""
This is the main module of the urlExpander package.
It has the multi-threaded expand function, which is the crux of this package.
"""

__all__ = ["expand", "multithread_function"]
__author__ = "Leon Yin"

import concurrent.futures
import json
import logging
import os
import time
from random import randint

import numpy as np
import pandas as pd
import requests
import unshortenit
from tqdm import tqdm
from urlexpander.core import constants, url_utils

LOGGER = logging.getLogger(__name__)

def _chunks(lst, chunksize):
    """Yield successive n-sized chunks from lst.
    Taken from https://stackoverflow.com/a/312464/5094480

    :param lst: the list to break up into smaller chunks
    :type lst: list
    :param chunksize: the number of items to include in each chunk
    :type chunksize: int

    """
    for i in range(0, len(lst), chunksize):
        yield lst[i : i + chunksize]

def _parse_error(error, verbose=False):
    """Parse error messages from the server response, to try to figure out what website the bit-link was intended to re-direct to.
        Although some redirects no longer work, we can still use the response from the error to figure out where it would have gone.

    :param error: error response from expand()
    :type error: str
    :param verbose: print error messages (Default value = False)
    :type verbose: bool
    :returns: domain-> the domain parsed from the error string
    :rtype: str, -1

    """
    if "ConnectionPool" in error:
        if verbose:
            print("ConnectionPool")
        vals = error.split("ConnectionPool(host='")[1].split("',")
        domain = vals[0]
        url_endpoint = (
            vals[1].split("Max retries exceeded with url: ")[-1].split(" (Caused by")[0]
        )
        url_endpoint = os.path.join("http://", domain, "__CONNECTIONPOOL_ERROR__")
        LOGGER.info(f"ConnectionPool, __CONNECTIONPOOL_ERROR__: {error}")

    elif "Client Error: " in error or "Server Error" in error:
        if verbose:
            print("ConnectionError or Server Error")
        url_endpoint = error.split(" for url: ")[-1]
        domain = url_utils.get_domain(url_endpoint)
        url_endpoint = os.path.join("http://", domain, "__CLIENT_ERROR__")
        LOGGER.info(f"ConnectionError or Server Error, __CLIENT_ERROR__: {error}")

    else:
        if verbose:
            print("Unknown error")
        domain, url_endpoint = -1, None
        LOGGER.info(f"Unknown error: {error}")

    return domain, url_endpoint



def _expand(url, timeout=2, verbose=False, use_head=True, **kwargs):
    """Expands a URL, while taking into consideration: special URL shortener or analytics platforms that either need a sophisticated
    redirect(st.sh), or parsing of the url (ln.is)

    :param url: URL to expand
    :type url: str
    :param timeout: number of seconds to wait for a response (Default value = 10)
    :type timeout: int
    :param verbose: print messages (Default value = False)
    :type verbose: bool
    :param use_head: if True, use HEAD request. If False, use GET request. (Default value = True)
    :type use_head: bool
    :param **kwargs:
    :rtype: a dictionary containing the following keys
      - original_url (str): the input URL
      - resolved_url (str): expanded URL, processed for errors
      - resolved_domain (str): extracted URL domain
    """
    if use_head:
        http_op = requests.head
    else:
        http_op = requests.get
    try:
        r = http_op(
            url,
            allow_redirects=True,
            timeout=timeout,
                    **kwargs)
        r.raise_for_status()
        url_long = r.url
        domain = url_utils.get_domain(url_long)
        if verbose:
            print("First expansion OK")

    except requests.exceptions.RequestException as exc:
        if verbose:
            print("First expansion Failed")
        domain, url_long = _parse_error(str(exc), verbose=verbose)

    if domain in constants.url_appenders:
        if verbose:
            print("domain in url appenders")
        url_long = url_long.replace(domain, "")
        domain = url_utils.get_domain(url_long)

    elif domain in constants.short_domain_ad_redirects or domain == -1:
        if verbose:
            print("domain in ad redirect")
        url_long = unshortenit.UnshortenIt().unshorten(url, timeout=timeout)
        domain = url_utils.get_domain(url_long)

    return dict(
        original_url=url,
        resolved_url=url_long,
        resolved_domain=domain,
    )


def expand(
    urls_to_expand,
    chunksize=1280,
    n_workers=1,
    cache_file=None,
    random_seed=303,
    verbose=0,
    filter_function=None,
    **kwargs,
):
    """Calls expand with multiple (``n_workers``) threads to unshorten a list of urls. Unshortens all urls by default, unless one sets a ``filter_function``.

    :param chunksize: chunks urls_to_expand, which makes computation quicker with larger inputs (Default value = 1280)
    :type chunksize: int
    :param n_workers: how many threads (Default value = 1)
    :type n_workers: int
    :param cache_file: a path to a json file to read and write results in (Default value = None)
    :type cache_file: str
    :param random_seed: initializes the random state for shuffling the input (Default value = 303)
    :type random_seed: int
    :param verbose: whether to print updates and errors. 0 is silent. 1 is progress bar. 2 is progress bar and errors. (Default value = 0)
    :type verbose: int
    :param filter_function: a boolean used to filter url shorteners out (Default value = None)
    :type filter_function: func
    :param **kwargs:
    :returns: unshortened_urls_-> resolved URLs
    :rtype: list

    """

    if isinstance(urls_to_expand, str):
        return _expand(urls_to_expand, **kwargs)["resolved_url"]

    else:
        urls_to_expand_ = urls_to_expand.copy()

        # get uniques
        if isinstance(urls_to_expand, list):
            urls_to_expand = list(set(urls_to_expand))
        elif isinstance(urls_to_expand, pd.Series):
            urls_to_expand = urls_to_expand.unique().tolist()

        # shuffle the inputs, this is to reduce the chances of making requests to the same domain.
        np.random.seed(random_seed)
        np.random.shuffle(urls_to_expand)

        # filter for URLs that need to be shortened according to some boolean function.
        if filter_function:
            urls_to_expand = [_ for _ in urls_to_expand if filter_function(_)]

        # read cache file
        expanded_urls = []
        if cache_file and os.path.exists(cache_file):
            with open(cache_file, "r") as f_:
                for line in f_:
                    expanded_urls.append(json.loads(line))
                abd_ = [_["original_url"] for _ in expanded_urls]
                urls_to_expand = list(
                    set(abd_).symmetric_difference(set(urls_to_expand))
                )

        # chunk the list of arguments
        if verbose:
            print("There are {} URLs to expand".format(len(urls_to_expand)))
            total = (len(urls_to_expand) // chunksize) + 1
            chunk_iter = tqdm(_chunks(urls_to_expand, chunksize=chunksize), total=total)
        else:
            chunk_iter = _chunks(urls_to_expand, chunksize=chunksize)

        for chunk in chunk_iter:
            # create n_workers threads, and map chunked argumnets to them
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=n_workers
            ) as executor:
                future_to_url = {
                    executor.submit(_expand, url, **kwargs): url for url in chunk
                }
                for i, future in enumerate(
                    concurrent.futures.as_completed(future_to_url)
                ):
                    try:
                        data = future.result()
                    except Exception as exc:
                        data = str(type(exc))
                        # error.append({chunk[i] : str(type(exc))})
                        if verbose == 2:
                            print(
                                "{} failed to resolve due to error: {}".format(
                                    chunk[i], str(type(exc))
                                )
                            )
                    finally:
                        if isinstance(data, dict):
                            expanded_urls.append(data)
                            # save the results
                            if cache_file:
                                with open(cache_file, "a") as f_:
                                    f_.write(json.dumps(data) + "\n")

        # reorder the urls (or join them into OG list)
        resolved_dict = {_["original_url"]: _["resolved_url"] for _ in expanded_urls}
        expanded_urls_ = [resolved_dict.get(_, _) for _ in urls_to_expand_]

        return expanded_urls_


def multithread_function(
    urls_to_expand,
    function,
    cache_col,
    chunksize=1280,
    n_workers=64,
    cache_file=None,
    random_seed=303,
    verbose=0,
    **kwargs,
):
    """Calls 'function' with multiple (n_workers) threads.

    :param urls_to_expand: a list of URLs (str) to unshorten
    :type urls_to_expand: list
    :param function:
    :param chunksize: chunks urls_to_expand, which makes computation quicker with larger inputs (Default value = 1280)
    :type chunksize: int
    :param n_workers: how many threads (Default value = 64)
    :type n_workers: int
    :param cache_col: the unique key-name to use to save cached rows.
    :type cache_col: str
    :param cache_file: a path to a json file to read and write results in (Default value = None)
    :type cache_file: str
    :param random_seed: initializes the random state for shuffling the input (Default value = 303)
    :type random_seed: int
    :param verbose: whether to return errors and updates (Default value = 0)
    :type verbose: bool
    :param **kwargs:
    :returns: expanded_urls-> a list of dictionaries perfect for Pandas Dataframes.
    :rtype: list

    """
    # shuffle the inputs, this is to reduce the changes of making requests to the same domain.
    np.random.seed(random_seed)
    np.random.shuffle(urls_to_expand)

    # read cache file
    expanded_urls = []
    error = []
    if cache_file and os.path.exists(cache_file):
        with open(cache_file, "r") as f_:
            for line in f_:
                expanded_urls.append(json.loads(line))
            abd_ = [_[cache_col] for _ in expanded_urls]
            urls_to_expand = [url for url in urls_to_expand if url not in abd_]

    if verbose:
        chunk_iter = tqdm(_chunks(urls_to_expand, chunksize=chunksize))
    else:
        chunk_iter = _chunks(urls_to_expand, chunksize=chunksize)

    for chunk in chunk_iter:
        # create n_workers threads, and map chunked arguments to them
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            future_to_url = {
                executor.submit(function, url, **kwargs): url for url in chunk
            }
            for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
                try:
                    data = future.result()
                except Exception as exc:
                    data = str(type(exc))
                    if verbose:
                        print(
                            "{} failed to resolve due to error: {}".format(
                                chunk[i], str(type(exc))
                            )
                        )
                finally:
                    if isinstance(data, dict):
                        expanded_urls.append(data)
                        # save the results
                        if cache_file:
                            with open(cache_file, "a") as f_:
                                f_.write(json.dumps(data) + "\n")

    return expanded_urls
