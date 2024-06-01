import asyncio
from typing import List

import twscrape
from twscrape.utils import gather
from twscrape import Tweet
import json

import os
import resend

resend.api_key = os.environ["RESEND_API_KEY"]

with open("cache.json", "r+") as json_file:
    # Load the JSON data into a Python dictionary
    cache = json.load(json_file)


async def get_new_bookmarks(old_bookmarks: List[int]):
    api = twscrape.API()
    # add accounts here or before from cli (see README.md for examples)
    await api.pool.add_account(
        os.environ["BOOKMARK_USERNAME"], os.environ["BOOKMARK_PASSWORD"], "", ""
    )
    await api.pool.login_all()
    new_bms = {}  # init

    async for bm in api.bookmarks():
        # print(f"Printing the existing cache keys. Type: {type(old_bookmarks)}. Length: {len(old_bookmarks)}")
        # print(f"Printing the id. Type: {type(bm.id)}. Value: {bm.id}")
        if str(bm.id) not in old_bookmarks:
            new_bms.update(
                {
                    bm.id: {
                        "content": bm.rawContent,
                        "name": bm.user.displayname,
                        "photo": bm.user.profileImageUrl,
                        "reply_count": bm.replyCount,
                        "retweet_count": bm.retweetCount,
                        "view_count": bm.viewCount,
                        "like_count": bm.likeCount,
                    }
                }
            )
        else:
            break
    return new_bms


async def add_to_cache(new_bms: List[any]):
    """update the cache with new tweets"""
    # update the dictionary for cache
    cache = load_cache()
    for key in new_bms.keys():
        cache.update({key: new_bms[key]})
    # save it back to the json
    with open("cache.json", "w") as json_file:
        json.dump(cache, json_file, indent=4)
    print("cache updated with new bookmarks\n")


async def reset_cache():
    """empty the cache"""
    cache = {}
    with open("cache.json", "w") as json_file:
        json.dump(cache, json_file, indent=4)
    print("emptied the cache\n")


async def call_bookmarker():
    """calls everything with setting"""
    pass


def dict_to_html(data):
    html = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f5f8fa;
                padding: 20px;
            }
            .tweet {
                background-color: #fff;
                border: 2px solid #e1e8ed;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                display: flex;
            }
            .tweet img {
                border-radius: 50%;
                width: 48px;
                height: 48px;
                margin-right: 15px;
            }
            .tweet .content {
                flex: 1;
            }
            .tweet .name {
                font-weight: bold;
                color: #14171a;
                margin-bottom: 5px;
            }
            .tweet .text {
                color: #14171a;
                margin-bottom: 10px;
            }
            .tweet .metadata {
                color: #657786;
                font-size: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .tweet .metadata .date {
                margin-right: 10px;
            }
            .tweet .metadata .stats {
                display: flex;
            }
            .tweet .metadata .stats div {
                margin-left: 15px;
            }
        </style>
    </head>
    <body>
    """

    for tweet_id, tweet_data in data.items():
        html += f"""
        <div class="tweet">
            <img src="{tweet_data['photo']}" alt="{tweet_data['name']}">
            <div class="content">
                <div class="name">{tweet_data['name']}</div>
                <div class="text">{tweet_data['content']}</div>
                <div class="metadata">
                    <div class="date">April 21, 2024</div>
                    <div class="stats">
                        <div class="replies">
                            <span class="count">{tweet_data['reply_count']}</span>
                            <span class="label">Replies</span>
                        </div>
                        <div class="retweets">
                            <span class="count">{tweet_data['retweet_count']}</span>
                            <span class="label">Retweets</span>
                        </div>
                        <div class="likes">
                            <span class="count">{tweet_data['like_count']}</span>
                            <span class="label">Likes</span>
                        </div>
                        <div class="views">
                            <span class="count">{tweet_data['view_count']}</span>
                            <span class="label">Views</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return html


async def send_email(in_email, content):
    params = {
        "from": "Acme <onboarding@resend.dev>",
        "to": [in_email],
        "subject": "🚨 Your daily Twitter bookmarks 🚨",
        "html": dict_to_html(content),
    }
    email = resend.Emails.send(params)
    print("email sent\n")


def load_cache() -> dict:
    with open("cache.json", "r+") as json_file:
        # Load the JSON data into a Python dictionary
        cache = json.load(json_file)
    return cache


if __name__ == "__main__":
    # asyncio.run(reset_cache())
    cache = load_cache()
    new_bms = asyncio.run(get_new_bookmarks(cache.keys()))
    asyncio.run(add_to_cache(new_bms))
    IN_EMAIL = "harry.mayne@oii.ox.ac.uk"
    asyncio.run(send_email(IN_EMAIL, new_bms))
