import html
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from lxml import etree, html as tree
from requests import get


def crawl(url: str):
    dom = tree.fromstring(get(url).content)

    # print(soup,dom)

    #  text = [el.strip() for el in dom.xpath('//p/text()[ancestor::div[@class="entry-content"]][normalize-space()]')]
    #  print(text)

    # print(''.join(dom.xpath('//*[@class="entry-content"]/p/[normalize-space()]')))

    for elem in dom.xpath('//div[@class="entry-content"]'):
        print(html.unescape(etree.tostring(elem, pretty_print=True).decode("utf-8")))


crawl("https://www.icbuw.eu/depleted-uranium-weapons-state-of-affairs-2022/")
