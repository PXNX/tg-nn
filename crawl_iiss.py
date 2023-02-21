import asyncio
import random
import string

import httpx
from bs4 import BeautifulSoup


async def try_url():
    url= "https://mil.in.ua/uk/news/cheski-volontery-vidkryly-zbir-na-rszv-rm-70/"


    res = httpx.get(url)
    dom = BeautifulSoup(res.content, "html.parser").body.main.div
    if res.status_code == 200:
        print(f"found: {url}",res)
        print("--------------------")
        title =dom.find("h1",class_="single-news__title").text

        paragraphs = list()
        images=list()

        print(title)
        article = dom.find("div", class_='single-news__wrapper')

        for p in article.find_all("p"):
            paragraphs.append(p.decode_contents())

        for img in article.find_all("img"):
            images.append(img["src"])
        print(images)


        print(paragraphs)




asyncio.run(try_url())