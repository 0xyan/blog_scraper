import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()


def fetch_blog_titles_and_links(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <h1> tags specifically identified for articles
    blog_posts = soup.find_all("h1", attrs={"data-testid": "article-header"})

    titles_and_links = []
    for title in blog_posts:
        # Attempt to find the parent container that includes both the <h1> and <a> tags
        parent_container = title.find_parent(
            "div",
            class_="px-4 md:px-6 lg:px-8 xl:px-6 2xl:px-12 relative h-full lg:pb-8 xl:pb-6 2xl:pb-14",
        )
        if parent_container:
            # Find the <a> tag inside the parent container
            link_tag = parent_container.find(
                "a",
                class_="group grid cursor-pointer grid-cols-auto/1fr items-center justify-start gap-x-[.4em] underline decoration-1 underline-offset-[0.375rem] mt-12 text-18 lg:hidden",
            )
            if link_tag and "href" in link_tag.attrs:
                link = urljoin(url, link_tag["href"])
            else:
                link = None
        else:
            link = None

        title_text = title.get_text(strip=True)
        titles_and_links.append((title_text, link))

    return titles_and_links


def check_new_titles(url, storage_file="posts.json"):
    try:
        with open(storage_file, "r") as file:
            old_posts = json.load(file)
    except FileNotFoundError:
        old_posts = []

    current_posts = fetch_blog_titles_and_links(url)
    new_posts = [post for post in current_posts if post not in old_posts]

    with open(storage_file, "w") as file:
        json.dump(current_posts, file)

    return new_posts


def send(token_tg, id_tg, text):
    url = "https://api.telegram.org/bot" + token_tg + "/sendMessage"
    params = {"chat_id": id_tg, "text": text}
    response = requests.get(url, params=params)
    return response.json()


def notify(token_tg, id_tg, posts):
    for title, link in posts:
        text = f"New WLD blog post: {title}\n{link}"
        send(token_tg, id_tg, text)


def main(url, interval):
    token_tg = os.getenv("token")
    id_tg = os.getenv("id_tg")

    while True:
        new_posts = check_new_titles(url)
        if new_posts:
            notify(token_tg, id_tg, new_posts)
        time.sleep(interval)


if __name__ == "__main__":
    blog_url = "https://worldcoin.org/blog/announcements"
    main(blog_url, interval=3600)  # Adjusted interval to a more reasonable value
