from tweepy import OAuthHandler
from SohrabCrawler import limit_handled

from keys import *
import tweepy

if __name__ == '__main__':
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    for tweet in limit_handled(tweepy.Cursor(api.user_timeline).items(), "status"):
        api.destroy_status(tweet.id)
