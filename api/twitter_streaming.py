#
# Licensed to the Apache Software Foundation (ASF) under one or more
from __future__ import print_function

import os
import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import socket
import json
from kafka import SimpleProducer, KafkaClient

consumer_key = 'XXXX'
consumer_secret = 'XXXX'
access_token = 'XXXX'
access_secret = 'XXXX'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_status(self, status):
        print(status.text)
        return True

    def on_error(self, status_code):
        if status_code == 420:
            return False

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)
twitter_stream = Stream(auth=api.auth, listener=StdOutListener())
tweet_follows ="%s"%sys.argv[1] 
twitter_stream.filter(track=tweet_follows)
