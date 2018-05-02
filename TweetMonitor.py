import re
import requests
import json
import xmltodict

class TweetMonitor:

    def __init__(self, id, start_likes=0, start_retweeters=0, start_followers_count = 0):
        self.start_likes = start_likes
        self.start_retweeters = start_retweeters
        self.likes_count = 0
        self.retweeters_count = 0
        self.actual_likes = start_likes
        self.actual_retweeters = start_retweeters
        self.id = id
        self.monitor_duration = 0
        self.hours_duration = 0
        self.topicList = []
        self.text = ""
        self.followers_count = 0
        self.start_followers_count = start_followers_count
        self.actual_followers = start_followers_count

    def set_monitor_duration(self, duration):
        self.monitor_duration = duration

    def add_hour(self):
        self.hours_duration = self.hours_duration + 1

    def get_hour(self):
        return self.hours_duration

    def set_text(self, text):
        self.text = text

    def get_text(self):
        return self.text

    def set_id(self, id):
        self.id = id

    def evaluate_topic(self, tweet_text, confidence, support):
        res = requests.get('http://model.dbpedia-spotlight.org/en/annotate?text=' + tweet_text + \
                           '&confidence=' + str(confidence) + '&support=' + str(support))
        res = xmltodict.parse(res.text)
        tweetKeyWords = dict()
        numRTs = self.get_retweeters_count()
        listOfTopics = []
        #tweetKeyWords["totalRTs"] = numRTs + self.get_retweeters_count()
        try:
            resources = res['Annotation']['Resources']['Resource']
            if isinstance(resources, list):
                for r in resources:
                    # print(r)
                    topic = r['@surfaceForm']
                    listOfTopics.append(topic)
            else:
                # print(res)
                topic = res['Annotation']['Resources']['Resource']['@surfaceForm']
                listOfTopics.append(topic)
        except KeyError:
            pass
        if "RT" in listOfTopics:
            listOfTopics.remove("RT")
        self.__set_topic(listOfTopics)

    def __set_topic(self, topic):
        self.topicList = topic

    def get_topics(self):
        return self.topicList

    def get_id(self):
        return self.id

    def set_start_likes(self, likes):
        self.start_likes = likes

    def set_start_retweeters(self, retweeters):
        self.start_retweeters = retweeters

    def get_start_likes(self):
        return self.start_likes

    def get_start_retweeters(self):
        return self.start_retweeters

    def add_like(self):
        self.likes_count = self.likes_count + 1

    def add_retweeters(self):
        self.retweeters_count = self.retweeters_count + 1

    def get_likes_count(self):
        return self.likes_count

    def get_retweeters_count(self):
        return self.retweeters_count

    def set_start_followers_count(self, start_followers_count):
        self.start_followers_count = start_followers_count

    def get_start_followers_count(self):
        return self.start_followers_count

    def add_follower(self):
        self.followers_count = self.followers_count + 1

    def get_followers_count(self):
        return self.followers_count

    def set_actual_followers(self, followers):
        if followers > self.actual_followers:
            print("New follower!")
            print("Followers: " + str(self.actual_followers))
            self.actual_followers = followers #aggiorno il numero di follower totali
            self.add_follower()

    def get_actual_followers(self):
        return self.actual_followers

    def set_actual_likes(self, likes):
        if likes > self.actual_likes:
            print("Tweet has got a like!")
            print("Likes count: ", likes)
            self.add_like()
            self.actual_likes = likes

    def set_actual_retweeters(self, retweeters):
        if retweeters > self.actual_retweeters:
            print("Tweet has been retweeted!")
            print("Retweet count:", retweeters)
            self.add_retweeters()
            self.actual_retweeters = retweeters

    def get_actual_likes(self):
        return self.actual_likes

    def get_actual_retweeters(self):
        return self.actual_retweeters