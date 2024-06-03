import logging

import httpx
from bs4 import BeautifulSoup
from pyrogram.types import Message

from model import CrawlPost

bloat = {
    'Mehr zum Thema:'
}


async def get_postillon(message: Message) -> CrawlPost:
    url = message.reply_markup.inline_keyboard[0][0].url

    res = httpx.get(url)
    logging.info(f"RES :::::::::::::: {res}", )

    if res.status_code == 302:
        logging.info(res.headers)
        res = httpx.get(res.headers["location"])

    if res.status_code == 200:
        dom = BeautifulSoup(res.content, "html.parser").body.main.div
        logging.info(f"found: {url, res}", )
        logging.info("--------------------")
        title = f"<b>{dom.find('h1', class_='entry-title').text}</b>"

        logging.info(title)
        article = dom.find("div", class_='post-body entry-content')

        paragraphs = list()
        for p in article.find_all("p"):  # todo: find way to also handle UL
            content = p.text  # .decode_contents() #wants links

            if content not in bloat and content != "":
                paragraphs.append(content)
        logging.info(f"paragraphs: {paragraphs}")

        # todo: rewrite this to append title to every text
        for p in paragraphs:
            if len(p) + len(title) < 920:
                title += f"\n\n{p}"

        title += f"\n\n<a href='{res.url}'>Mehr lesen...</a>"

        return CrawlPost(
            title,
            None,
            [message.web_page.photo.file_id],
            None,
            url
        )

# asyncio.run(try_url("https://mil.in.ua/uk/news/cheski-volontery-vidkryly-zbir-na-rszv-rm-70/"))
