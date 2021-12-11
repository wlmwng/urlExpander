"""These are variables that are useful to reference.
There are several curated lists of link shortening domains,
the url of datasets for tutorials.
"""

__author__ = "Leon Yin"


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Connection": "close",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,*",
}

# https://github.com/psf/requests/issues/5742#issuecomment-772885630
# use the requests library's default headers to expand t.co URLs
headers_tw = {
    "User-Agent": "python-requests/2.26.0",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

# number of seconds to sleep before sending a request
MIN_DELAY = 8
MAX_DELAY = 12

"""
Google Analytics
 - https://ga-dev-tools.appspot.com/campaign-url-builder/
 - https://www.jeeshenlee.com/2020/02/google-analytics-exclude-query.html
Adobe Analytics
 - http://www.kotaraindustries.com/2016/03/does-adobe-analytics-have-its-own-version-of-googles-custom-utm-urls-for-campaign-tracking/
Hubspot
 - https://knowledge.hubspot.com/ads/ad-tracking-in-hubspot
 - https://knowledge.hubspot.com/reports/why-do-i-see-so-many-urls-for-the-same-page-in-google-analytics-for-visits-from-hubspot-emails
"""
analytics_parameters = [
    "utm_campaign",
    "utm_medium",
    "utm_source",
    "utm_term",
    "utm_content",
    "__twitter_impression",
    "fbclid",
    "amp",
    "camp",
    "cid",
    "cmpid",
    "custom_click",
    "dkt_nbr",  # newsmax
    "ns_mail_job",
    "ns_mail_uid",
    "can_id",
    "email_referrer",
    "email_subject",
    "link_id",
    "source",
    "platform",
    "_amp",
    "hsa_ol",
    "hsa_la",
    "hsa_cam",
    "hsa_grp",
    "hsa_mt",
    "hsa_src",
    "hsa_ad",
    "hsa_acc",
    "hsa_net",
    "hsa_kw",
    "hsa_tgt",
    "hsa_ver",
    "__hssc",
    "__hstc",
    "hsCtaTracking",
    "_hsenc",
    "_hsmi",
    "hss_channel",
]

# these domains need a redirect (Leon Yin + UnshortenIT 2018)
short_domain_ad_redirects = [
    "sh.st",
    "adf.ly",
    "lnx.lu",
    "adfoc.us",
    "j.gs",
    "q.gs",
    "u.bb",
    "ay.gy",
    "atominik.com",
    "tinyium.com",
    "microify.com",
    "linkbucks.com",
    "www.linkbucks.com",
    "jzrputtbut.net",
    "any.gs",
    "cash4links.co",
    "cache4files.co",
    "dyo.gs",
    "filesonthe.net",
    "goneviral.com",
    "megaline.co",
    "miniurls.co",
    "qqc.co",
    "seriousdeals.net",
    "theseblogs.com",
    "theseforums.com",
    "tinylinks.co",
    "tubeviral.com",
    "ultrafiles.net",
    "urlbeat.net",
    "whackyvidz.com",
    "yyv.co",
    "href.li",
    "anonymz.com",
    "festyy.com",
    "ceesty.com",
    "tiny.cc",
]

# these are standard domain shorteners (Leon Yin 2018)
short_domain = [
    "dlvr.it",
    "bit.ly",
    "buff.ly",
    "ow.ly",
    "goo.gl",
    "shar.es",
    "ift.tt",
    "fb.me",
    "washex.am",
    "smq.tc",
    "trib.al",
    "is.gd",
    "paper.li",
    "waa.ai",
    "tinyurl.com",
    "ht.ly",
    "1.usa.gov",
    "deck.ly",
    "bit.do",
    "lc.chat",
    "urls.tn",
    "soo.gd",
    "s2r.co",
    "clicky.me",
    "budurl.com",
    "bc.vc",
    "branch.io",
    "capsulink.com",
    "ux9.de",
    "fuck.it",
    "t2m.io",
    "shrt.li",
    "elbo.in",
    "shrtfly.com",
    "hiveam.com",
    "slink.be",
    "plu.sh",
    "cutt.ly",
    "zii.bz",
    "munj.pw",
    "t.co",
    "go.usa.gov",
    "on.fb.me",
    "j.mp",
    "amp.twimg.com",
    "ofa.bo",
    "apne.ws",
]

# there are domain shorteners for common news outlets (Leon Yin 2018).
short_domain_media = [
    "on.rt.com",
    "wapo.st",
    "hill.cm",
    "dailym.ai",
    "cnn.it",
    "nyti.ms",
    "politi.co",
    "fxn.ws",
    "usat.ly",
    "huff.to",
    "nyp.st",
    "cbsloc.al",
    "wpo.st",
    "on.wsj.com",
    "nydn.us",
    "on.wsj.com",
    "abcn.ws",
    "cbsn.ws",
    "cbsloc.al",
    "cnb.cx",
    "reut.rs",
    "hann.it",
    "cs.pn",
]

# there are link shorteners with the actual link appended on the end
url_appenders = ["ln.is", "linkis.com"]

all_short_domains = short_domain_ad_redirects + short_domain + url_appenders

congress_dataset_url = (
    "https://raw.githubusercontent.com/SMAPPNYU/"
    "urlExpander/master/datasets/"
    "congress_sample_links.csv"
)

us_nation_domain_url = (
    "https://raw.githubusercontent.com/SMAPPNYU/"
    "urlExpander/master/datasets/"
    "us_national_domains.csv"
)
