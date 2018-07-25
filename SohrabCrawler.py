# consumer_key, consumer_secret, access_token and access_token_secret are stored here
from keys import *

import time
import tweepy
from tweepy import OAuthHandler
import datetime
from pymongo import MongoClient


def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.error.TweepError:
            print(datetime.datetime.now())
            time.sleep(15 * 60)


class Crawler:
    api, collection_tweeters, collection_users = None

    def __init__(self):
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

        client = MongoClient()
        db = client['twitter']
        self.collection_tweeters = db['tweeters']
        self.collection_users = db["users"]

    def retweeters(self, tweet_id):
        rets = []
        for ret in tweepy.Cursor(self.api.retweeters, id=tweet_id).items():
            rets.append(str(ret))
        return rets

    def measure_influence(self, user_id):   # user_id is an Integer
        influ = {}
        influence = {}

        for liked in limit_handled(tweepy.Cursor(self.api.favorites, id=user_id).items(100)):
            is_ret = False
            if liked._json["retweet_count"] != 0:
                is_ret = str(user_id) in self.retweeters(liked._json["id_str"])
            try:
                influ[liked._json["user"]["screen_name"]][0] += 1
                if is_ret:
                    influ[liked._json["user"]["screen_name"]][1] += 1
            except KeyError:
                if is_ret:
                    influ[liked._json["user"]["screen_name"]] = [1, 1]
                else:
                    influ[liked._json["user"]["screen_name"]] = [1, 0]

        for liked in influ:
            influence[liked] = influ[liked][1] / influ[liked][0]

        return influence

    def construct_collections(self):

        def add_to_users(user_id):
            if self.collection_users.find({"user_id": user_id}).count() == 0:
                self.collection_users.insert_one({
                    "user_id": user_id,
                    "received_influence": self.measure_influence(user_id)
                })

        for i in self.api.trends_place(23424977)[0]["trends"]:  # WOEID of LA is 23424977
            current_item = {"trend": i["name"]}
            tweeters = []
            for tweet in limit_handled(tweepy.Cursor(self.api.search, q=i["name"] + ' -filter:retweets').items(100)):

                id_str = tweet._json["id_str"]
                retweeters_id = self.retweeters(id_str)
                user_id = str(tweet._json["user"]['id'])
                post = {    # for tweeter collection
                    "user_id": user_id,
                    "id_str": id_str,
                    "retweeters_id": retweeters_id
                }
                tweeters.append(post)

                # adding new users to users collection
                add_to_users(user_id)
                for user in retweeters_id:
                    add_to_users(user)

            current_item["tweeters"] = tweeters
            self.collection_tweeters.insert_one(current_item)
