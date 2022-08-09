from re import I
from datasette import hookimpl
from urllib.parse import quote
import hashlib
import jinja2
import urllib
import os

IMGIX_SECRET = os.environ.get("IMGIX_SECRET", "")


@hookimpl
def extra_template_vars():
    return {
        "imgix_sign": imgix_sign,
        "breadcrumbs": breadcrumbs,
    }


def imgix_sign(url):
    """
    Sign a URL with the imgix secret key.
    """
    bits = urllib.parse.urlparse(url)
    signing_value = IMGIX_SECRET + bits.path
    if bits.query:
        signing_value += "?" + bits.query
    signature = hashlib.md5(signing_value.encode("utf-8")).hexdigest()
    if "?" in url:
        signed = url + "&s=" + signature
    else:
        signed = url + "?s=" + signature
    return signed


def breadcrumbs(folder):
    folder = folder.strip("/")
    bits = folder.split("/")
    crumbs = []
    accumulated = []
    for bit in bits:
        accumulated.append(bit)
        path = "/folders/" + quote("/".join(accumulated))
        crumbs.append('<a href="{}">{}</a>'.format(path, jinja2.escape(bit)))
    return jinja2.Markup(" / ".join(crumbs))
