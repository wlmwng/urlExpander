"""This module has utility functions for parsing text from HTML.
It helps extract the title, description (e.g., what shows up on Google), paragraphs, and images.
A URL and the HTML of its associated webpage can be collected using expand_with_content().
"""
__all__ = [
    "search_webpage_title",
    "search_webpage_description",
    "search_webpage_paragraphs",
    "search_webpage_image",
    "search_webpage_meta",
]
__author__ = "Leon Yin"

import re
import html


def search_webpage_title(text):
    """Collect the webpage's title

    :param text: HTML
    :type text: str
    :returns title: webpage's title
    :rtype: str, None

    """
    title = None
    regex = re.compile("<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
    try:
        title = regex.search(text).group(1)
        title = html.unescape(title)
    except:
        pass
    return title


def search_webpage_description(text):
    """Collect the webpage's description

    :param text: HTML
    :type text: str
    :returns desc: webpage's description
    :rtype: str, None

    """
    desc = None
    regex = re.compile(
        '<meta property="og?:description" content="(.*?)>', re.IGNORECASE | re.DOTALL
    )
    try:
        desc = regex.search(text).group(1).rstrip("/").rstrip(" ").rstrip('"')
        desc = html.unescape(desc)
    except:
        pass
    return desc


def search_webpage_paragraphs(text):
    """Collect the webpage's paragraphs

    :param text: HTML
    :type text: str
    :returns paragraphs: webpage paragraphs
    :rtype: list

    """
    paragraphs = []
    try:
        paragraphs = re.findall(r"<p>(.*?)</p>", text)
        paragraphs = [html.unescape(p) for p in paragraphs]
    except:
        pass
    return paragraphs


def search_webpage_image(text):
    """Collect the webpage's images

    :param text: HTML
    :type text: str
    :returns title: webpage's images
    :rtype: str, None

    """
    img_url = None
    regex = re.compile(
        '<meta property="og?:image" content="(.*?)>', re.IGNORECASE | re.DOTALL
    )
    try:
        img_url = regex.search(text).group(1).rstrip("/").rstrip(" ").rstrip('"')
        img_url = html.unescape(img_url)
    except:
        pass
    return img_url


def search_webpage_meta(url, text):
    """Collect title, description, and image.

    :param url: URL
    :type url: str
    :param text: HTML
    :type text: str
    :returns meta: extracted info from the webpage
    :rtype: dict

    """
    meta = dict(
        url=url,
        title=search_webpage_title(text),
        description=search_webpage_description(text),
        image_url=search_webpage_image(text),
    )
    return meta
