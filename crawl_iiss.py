import datetime
import re

import httpx
from bs4 import BeautifulSoup
from pyrogram.types import Message
from pytube import YouTube

from model import CrawlPost

bloat = {
    '<hr/><p><strong> “<em>Мілітарний</em>” працює завдяки постійній підтримці Спільноти</strong></p><ul><li>Ставай '
    'патроном на\xa0<a href="https://www.patreon.com/milinua">Patreon</a> від $1</li><li>Будь спонсором на\xa0<a '
    'href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9/videos">Youtube</a> '
    'від 70 грн</li></ul><hr/><p><strong>Навіть донат в 30 грн (ціна 1 кави) допоможе нам працювати '
    'далі:</strong></p><ul><li><em>PayPal</em> - <a class="__cf_email__" '
    'data-cfemail="8dfdecf4fdece1cde0e4e1a3e4e3a3f8ec" href="/cdn-cgi/l/email-protection">['
    'email\xa0protected]</a></li><li><em>Приватбанк</em> 4149 6293 1808 2567</li><li><em>monobank</em> 4441 1144 4179 '
    '6255</li><li><em>ETH</em> 0xeEAEAd0d28ea8e0cdadB2692765365e7F54004a3</li></ul><hr/><p><strong>Будь з '
    '“Мілітарним” на всіх платформах</strong></p><p><a href="https://twitter.com/mil_in_ua">Twitter</a>\xa0||\xa0<a '
    'href="https://t.me/milinua">Telegram</a>\xa0||\xa0<a '
    'href="https://www.facebook.com/milinua">Facebook</a>\xa0||\xa0<a '
    'href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9">Youtube</a></p><hr'
    '/>',
    '<hr/><p><strong> “<em>Мілітарний</em>” працює завдяки постійній підтримці Спільноти</strong></p><ul><li>Ставай '
    'патроном на\xa0<a href="https://www.patreon.com/milinua">Patreon</a> від $1</li><li>Будь спонсором на\xa0<a '
    'href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9/videos">Youtube</a> '
    'від 70 грн</li></ul><hr/><p><strong>Навіть донат в 30 грн (ціна 1 кави) допоможе нам працювати '
    'далі:</strong></p><ul><li><em>PayPal</em> - <a class="__cf_email__" '
    'data-cfemail="91e1f0e8e1f0fdd1fcf8fdbff8ffbfe4f0" href="/cdn-cgi/l/email-protection">['
    'email\xa0protected]</a></li><li><em>Приватбанк</em> 4149 6293 1808 2567</li><li><em>monobank</em> 4441 1144 4179 '
    '6255</li><li><em>ETH</em> 0xeEAEAd0d28ea8e0cdadB2692765365e7F54004a3</li></ul><hr/><p><strong>Будь з '
    '“Мілітарним” на всіх платформах</strong></p><p><a href="https://twitter.com/mil_in_ua">Twitter</a>\xa0||\xa0<a '
    'href="https://t.me/milinua">Telegram</a>\xa0||\xa0<a '
    'href="https://www.facebook.com/milinua">Facebook</a>\xa0||\xa0<a '
    'href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9">Youtube</a></p><hr'
    '/>',
    '<strong> “<em>Мілітарний</em>” працює завдяки постійній підтримці Спільноти</strong>',
    '<hr/><p><strong> “<em>Мілітарний</em>” працює завдяки постійній підтримці Спільноти</strong></p><ul><li>Ставай '
    'патроном на\xa0<a href="https://www.patreon.com/milinua">Patreon</a> від $1</li><li>Будь спонсором на\xa0<a '
    'href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9/videos">Youtube</a> '
    'від 70 грн</li></ul><hr/><p><strong>Навіть донат в 30 грн (ціна 1 кави) допоможе нам працювати '
    'далі:</strong></p><ul><li><em>PayPal</em> - <a class="__cf_email__" '
    'data-cfemail="6e1e0f171e0f022e030702400700401b0f" href="/cdn-cgi/l/email-protection">['
    'email\xa0protected]</a></li><li><em>Приватбанк</em> 4149 6293 1808 2567</li><li><em>monobank</em> 4441 1144 4179 '
    '6255</li><li><em>ETH</em> 0xeEAEAd0d28ea8e0cdadB2692765365e7F54004a3</li></ul><hr/><p><strong>Будь з '
    '“Мілітарним” на всіх платформах</strong></p><p><a href="https://twitter.com/mil_in_ua">Twitter</a>\xa0||\xa0<a '
    'href="https://t.me/milinua">Telegram</a>\xa0||\xa0<a '
    'href="https://www.facebook.com/milinua">Facebook</a>\xa0||\xa0<a '
    'href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9">Youtube</a></p><hr'
    '/>',
    '<strong>Навіть донат в 30 грн (ціна 1 кави) допоможе нам працювати далі:</strong>',
    '<strong>Будь з “Мілітарним” на всіх платформах</strong>',
    '<a href="https://twitter.com/mil_in_ua">Twitter</a>\xa0||\xa0<a href="https://t.me/milinua">Telegram</a>\xa0||\xa0<a href="https://www.facebook.com/milinua">Facebook</a>\xa0||\xa0<a href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9">Youtube</a>',
    '<li>Ставай патроном на\xa0<a href="https://www.patreon.com/milinua">Patreon</a> від $1</li><li>Будь спонсором '
    'на\xa0<a href="https://www.youtube.com/c/%D0%9C%D1%96%D0%BB%D1%96%D1%82%D0%B0%D1%80%D0%BD%D0%B8%D0%B9/videos'
    '">Youtube</a> від 70 грн</li>',
    '<li><em>PayPal</em> - <a class="__cf_email__" data-cfemail="6e1e0f171e0f022e030702400700401b0f" '
    'href="/cdn-cgi/l/email-protection">[email\xa0protected]</a></li><li><em>Приватбанк</em> 4149 6293 1808 '
    '2567</li><li><em>monobank</em> 4441 1144 4179 6255</li><li><em>ETH</em> '
    '0xeEAEAd0d28ea8e0cdadB2692765365e7F54004a3</li>'
}


async def try_url(message: Message) -> CrawlPost:
    url = re.findall(r"https://mil\.in\.ua/.+", message.caption.html)[0]

    res = httpx.get(url)
    dom = BeautifulSoup(res.content, "html.parser").body.main.div
    if res.status_code == 200:
        print(f"found: {url}", res)
        print("--------------------")
        title = re.findall(r"^.+", message.caption.html)[0]  ##### dom.find("h1", class_="single-news__title").text
        img = dom.find("img", class_="post-banner__img")

        print(title)
        article = dom.find("div", class_='single-news__wrapper')

        paragraphs = list()
        for p in article.find_all("p"):  # todo: find way to also handle UL
            content = p.decode_contents()

            if content not in bloat:
                paragraphs.append(content)
        print("paragraphs:", paragraphs)

        text = "\n".join(paragraphs)

        text = re.sub(r"<hr/><p><strong> “<em>Мілітарний</em>”[\s\S]+", "", text).rstrip()

        # + "AAAAAAAAAAAad\nAAEF" + re.sub(r"<hr/><p><strong> “<em>Мілітарний</em>”[\s\S]+",
        #                                   "",
        #                                   text).rstrip() + "gsbbbbbbbbbbbbb\nwrstbnnnnnnnn" + re.sub(
        #   r"<hr/><p><strong> “<em>Мілітарний</em>”[\s\S]+", "", text).rstrip()

        text_split = text.splitlines()

        texts = {0: f"<b>{title}</b>"}
        index = 0

        for x in text_split:

            if index == 0:
                limit = 600
            else:
                limit = 4000

            x = f"{texts[index] if index < len(texts) else ''}\n\n{x}"

            if len(x) < limit:
                texts[index] = x
            else:
                index += 1

        print(texts)

        print("---\n\n\n\n---------")

        images = [img["data-src"]]
        for img in article.find_all("img"):
            images.append(img["src"])
        print("images:", images)

        image_urls = list()
        for i in images:
            r = httpx.get(i, timeout=20)
            # fix file not found?
            filename = f"img/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}{i.split('/')[-1]}"
            with open(filename, 'wb') as f:
                f.write(r.content)

            image_urls.append(filename)

        videos = list()
        containers = article.find_all("div", class_='video-container')
        for v in containers:
            filename = re.findall(r'https://www\.youtube\.com/embed/(.*)\?feature=oembed', v.find('iframe')['src'])[
                           0] + ".mp4"

            video_path = YouTube(v.find("iframe")["src"]).streams.filter(progressive=True,
                                                                         file_extension='mp4').order_by(
                'resolution').desc().first().download(output_path="vid", filename=filename)
            videos.append(video_path)
        print("videos:", videos)

        return CrawlPost(
            texts[0],
            list(texts.values())[1:],
            image_urls,  # careful, can be more than 10
            videos,
            url
        )

###asyncio.run(try_url("https://mil.in.ua/uk/news/cheski-volontery-vidkryly-zbir-na-rszv-rm-70/"))
