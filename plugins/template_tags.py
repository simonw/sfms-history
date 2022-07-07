from re import I
from datasette import hookimpl
import hashlib
import urllib
import os

IMGIX_SECRET = os.environ.get("IMGIX_SECRET", "")


@hookimpl
def extra_template_vars():
    return {
        "imgix_sign": imgix_sign,
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
