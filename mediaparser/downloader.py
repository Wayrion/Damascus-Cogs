import instaloader
import json
import os

import re

from redvid import Downloader

from datetime import datetime
import yt_dlp
from urllib.parse import urlparse, urlunparse

import httpx
import random
from fake_useragent import UserAgent

from bs4 import BeautifulSoup as bs4
from pathlib import Path
import aiofiles

# import logging

# logging.getLogger("httpx").setLevel(logging.ERROR)
# Or logging.ERROR or logging.CRITICAL
# Or, to completely disable:
# logging.getLogger("httpx").propagate = False
# logging.getLogger("httpx").addHandler(logging.NullHandler())


async def get_content(
    url: str, output: str = "video.mp4", cookies: httpx.Cookies = None
):
    client = httpx.AsyncClient()
    result = await client.get(
        url,
        headers={"User-Agent": UserAgent().random},
        cookies=cookies,
    )
    async with aiofiles.open(output, "wb") as w:
        async for content in result.aiter_bytes(chunk_size=1024):
            await w.write(content)


async def musicaldown(url: str, output: str):
    """
    url: tiktok video url
    output: output file name
    """
    try:
        headers = {"User-Agent": UserAgent().random}
        ses = httpx.AsyncClient(headers=headers)
        res = await ses.get("https://musicaldown.com/en")
        parsing = bs4(res.text, "html.parser")
        allInput = parsing.findAll("input")
        data = {}
        for i in allInput:
            if i.get("id") == "link_url":
                data[i.get("name")] = url
                continue

            data[i.get("name")] = i.get("value")

        res = await ses.post(
            "https://musicaldown.com/download", data=data, follow_redirects=True
        )
        if res.text.find("Convert Video Now") >= 0:
            data = re.search(r"data: '(.*?)'", res.text).group(1)
            urlSlider = re.search(r"url: '(.*?)'", res.text).group(1)
            res = await ses.post(urlSlider, data={"data": data})
            if res.text.find('"success":true') >= 0:
                urlVideo = res.json()["url"]
                res = await get_content(urlVideo, output)
                return True

            return False

        parsing = bs4(res.text, "html.parser")
        urls = parsing.findAll(
            "a", attrs={"class": "btn waves-effect waves-light orange download"}
        )
        if len(urls) <= 0:
            return False

        i = random.randint(0, 1)
        urlVideo = urls[i].get("href")
        res = await get_content(urlVideo, output)
        return True

    except Exception as e:
        print(f"musicaldown error : {e}")
        return False


async def get_video_detail(url: str):
    """
    url: str -> tiktok video url

    return video_id / None
    """
    path = Path(url)
    post_id = path.stem
    headers = {
        "User-Agent": UserAgent().random,
    }
    ses = httpx.AsyncClient(headers=headers)
    if not post_id.isdigit():
        result = await ses.get(url, follow_redirects=False)
        if result.text.startswith('<a href="'):
            post_url = result.text.split('<a href="')[1].split("?")[0]
            post_id = Path(post_url).stem
    result = await ses.get(
        f"https://tiktok.com/@i/video/{post_id}", follow_redirects=True
    )
    cookies = result.cookies
    # print(cookie)
    open("tiktok_get_result.html", "w", encoding="utf-8").write(result.text)
    parser = bs4(result.text, "html.parser")
    infotag = parser.find("script", attrs={"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
    if infotag is None:
        return None
    infoload = json.loads(infotag.text)
    video_detail = infoload.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {})
    video_id = video_detail.get("itemInfo", {}).get("itemStruct", {}).get("id")
    author = video_detail.get("itemInfo", {}).get("itemStruct", {}).get("author", {})
    video = video_detail.get("itemInfo", {}).get("itemStruct", {}).get("video", {})
    image_post = (
        video_detail.get("itemInfo", {}).get("itemStruct", {}).get("imagePost", {})
    )
    images = image_post.get("images")
    author_id = author.get("id")
    author_username = author.get("uniqueId")
    video_url = video.get("playAddr")
    return video_id, author_id, author_username, video_url, images, cookies


async def tiktok_downloader(url: str) -> str:
    current_file_path = os.path.realpath(__file__)
    current_dir = os.path.dirname(current_file_path)

    # Generate the output file path with timestamp to avoid hash collision
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    output_dir = os.path.join(current_dir, "temp", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    title = os.path.join(output_dir, f"tiktok_{timestamp}.mp4")

    await musicaldown(url, title)

    return output_dir


async def get_real_instagram_url(share_url: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(share_url, follow_redirects=True)
            return str(response.url)  # This is the real post URL
    except Exception as e:
        print(f"Error fetching real Instagram URL: {e}")
        return None


async def instagram_downloader(url: str, mail: str, password: str):

    InstaLoader = instaloader.Instaloader()
    if mail and password:
        InstaLoader.login(mail, password)

    current_file_path = os.path.realpath(__file__)
    current_dir = os.path.dirname(current_file_path)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    output_dir = os.path.join(current_dir, "temp", timestamp)

    os.makedirs(output_dir, exist_ok=True)

    InstaLoader.dirname_pattern = output_dir

    real_url = await get_real_instagram_url(url)  # Fetch the real post url
    # Remove query parameters from the real_url
    parsed_url = urlparse(real_url)
    real_url = urlunparse(parsed_url._replace(query=""))

    match = re.search(r"instagram\.com/[^/]+/([^/]+)/", real_url)
    if not match:
        print(f"Error extracting shortcode from URL: {real_url}")
        return None
    shortcode = match.group(1)

    post = instaloader.Post.from_shortcode(InstaLoader.context, shortcode)

    InstaLoader.download_post(post, target=output_dir, silent=True)

    return output_dir


async def reddit_downloader(url: str):
    current_file_path = os.path.realpath(__file__)
    current_dir = os.path.dirname(current_file_path)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    output_dir = os.path.join(current_dir, "temp", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    reddit_downloader = Downloader(max_q=True)
    reddit_downloader.url = url
    reddit_downloader.path = output_dir

    try:
        reddit_downloader.download()
        print(f"Reddit video downloaded successfully to {output_dir}.")
        return output_dir

    except BaseException:
        print("No video in post")
        return None

    except Exception as e:
        print(f"Error downloading Reddit video: {e}")
        return None


async def youtube_downloader(url: str):
    current_file_path = os.path.realpath(__file__)
    current_dir = os.path.dirname(current_file_path)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    output_dir = os.path.join(current_dir, "temp", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"YouTube video downloaded successfully to {output_dir}.")
        return output_dir
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None
