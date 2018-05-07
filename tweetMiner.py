import datetime
import re
import time
import tweepy,json,io
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener, Stream
import twitter
import time
import pandas as pd

from TweetMonitor import TweetMonitor
CONFIDENCE = 0.3
SUPPORT = 20
HOUR = 3600 #secondi
WAITING_HOURS = 6 #cambiare questo valore per determinare le ore di monitoring

"""Questa funzione serve a rimuovere le emoticons dai tweet"""
def remove_emoji(string):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)

class MyListener(StreamListener):

    def __init__(self):
        self.tweet_id = 0

    def get_tweet_id(self):
        return self.tweet_id

    def on_data(self, raw_data):
        try:
            '''convertiamo i dati da tweet in un dictionary, preleviamo i tweet (escludendo i retweet).
            Dopodichè, controlliamo i trend (cioè gli hashtag) inclusi in ogni tweet, il quale viene salvato
            nei file corrispondenti a quei trend'''
            datadict = json.loads(raw_data)
            print("A tweet has been tweeted!")
            print("Tweet id:", datadict['id'])
            if datadict['id'] is not None:
                self.tweet_id = datadict['id']

                """tweet_timestamp = datadict['created_at']
                #tweet_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(tweet_timestamp,'%a %b %d %H:%M:%S +0000 %Y'))
                tweet_timestamp2 = datetime.datetime.strptime(tweet_timestamp, '%a %b %d %H:%M:%S +0000 %Y')
                ts = datetime.datetime.utcnow()
                print(ts - tweet_timestamp2)
                print(tweet_timestamp)
                print(tweet_timestamp2)
                print(ts)"""
                return False
            return True
        except BaseException as e:
            print('Error on_data: %s' % str(e))
        return True
    
    def on_error(self, status_code):
        print(status_code)
        return True

#Dati di accesso alle API di Twitter
consumer_key="IunBnF5zX9ckCz4JWDy0BR4tv"
consumer_secret="PvHyFqRCK9BJZr0MP4w2NtYGAwnNbX8uVdEmUtoWZAswvyhxwD"
access_token="542574402-cTY4jCE0HUzOzqznZ6U0pX0JRNTyPCcTBzMSbf82"
access_secret="CeiEH8RTBNH6F3lNe2WXf2lfbKTQrpcVw8d82v1BJY2z0"

auth = OAuthHandler(consumer_key, consumer_secret)

auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

#Cambiare l'user da seguire
user = "CocaCola"
tweet_user = api.get_user(screen_name=user)
print("Searching tweet in the user timeline of ", tweet_user.screen_name)

#nel caso in cui si voglia procedere in stream decommentare queste linee di codice
#mystreamer = MyListener()
#twitterStream = Stream(auth, mystreamer)
#twitterStream.filter(follow=[str(tweet_user.id)])
#tweet_id = mystreamer.get_tweet_id()
#==================================================================================




passed_hours = 0 #contatore delle ore passate a monitorare il tweet
startmonitoring = datetime.datetime.today() #timestamp del tempo di inizio monitoring
print("Start monitoring at:", startmonitoring)
while(True):
    oldtime = time.time() #mi prendo il numero di secondi così dopo posso tenere traccia del tempo che passa.

    tweet_monitors = [] #lista di oggetti TweetMonitor
    print("Checking ", tweet_user.screen_name, "...")
    print("\tFollowers count: ", tweet_user.followers_count)
    print("\tUser id:", tweet_user.id)
    print("Last tweet:")
    tweet_id = api.user_timeline(id=tweet_user.id, exclude_replies=True)[0].id #mi prendo l'ultimo tweet della timeline
    tweet_status = api.get_status(tweet_id)
    print("\tTweet id: ", tweet_id)
    print("\tText:", tweet_status.text)

    print("\tTweet likes:", int(tweet_status._json['favorite_count']))
    print("\tTweet retweeters count:", tweet_status._json['retweet_count'])
    #valori iniziali da memorizzare sul dataset insieme a start_monitoring_at
    prev_likes_count = int(tweet_status._json['favorite_count']) #like al momento in cui si inizia a monitorare il tweet
    prev_followers_count = int(tweet_user.followers_count) #numero di follower nel momento in cui si inizia a monitorare il tweet
    prev_retweeters_count = int(tweet_status._json['retweet_count'])#numero di retweeters nel momento in cui si inizia a monitorare il tweet

    #inizializzazione dei contatori
    new_likes_count = 0 #contatore dei like ricevuti
    new_retweet_count = 0 #contatore dei retweeters ricevuti
    new_followers_count = 0 #contatore di followers ricevuti

    #Istanzio l'oggetto TweetMonitor
    tweetMonitor = TweetMonitor(id=tweet_id,
                                start_likes=prev_likes_count,
                                start_retweeters=prev_retweeters_count,
                                start_followers_count=prev_followers_count)
    tweet_text = remove_emoji(tweet_status.text) #rimuovo tutto ciò che non è testo
    print("Text without emoji:", tweet_text)
    tweetMonitor.set_text(tweet_text)
    tweetMonitor.evaluate_topic(tweet_text, confidence=CONFIDENCE, support=SUPPORT) #calcolo il topic del tweet
    print("\tTweet topic:", tweetMonitor.get_topics())
    tweet_monitors.append(tweetMonitor)
    while True:
        #prendo sempre l'ultimo tweet dello user
        new_tweet_id = api.user_timeline(id=tweet_user.id, exclude_replies=True)[0].id
        #se ha un id differente dal tweet attuale che si sta monitorando, vuol dire che è stato pubblicato un nuovo tweet
        if new_tweet_id != tweet_id:
            print("New Tweet has been published!")
            tweet_status = api.get_status(new_tweet_id)
            print("\tTweet id: ", new_tweet_id)
            print("\tText:", tweet_status.text)
            print("\tTweet likes:", int(tweet_status._json['favorite_count']))
            print("\tTweet retweeters count:", tweet_status._json['retweet_count'])
            #istanzio un altro oggetto TweetMonitor
            tweetMonitor = TweetMonitor(id=new_tweet_id,
                                        start_likes=tweet_status._json['favorite_count'],
                                        start_retweeters=tweet_status._json['retweet_count'],
                                        start_followers_count=prev_followers_count)
            tweet_text = remove_emoji(tweet_status.text)
            # print("Text without emoji:", tweet_text)
            tweetMonitor.set_text(tweet_text)
            tweetMonitor.evaluate_topic(tweet_text, confidence=CONFIDENCE, support=SUPPORT)
            tweet_monitors.append(tweetMonitor) #aggiungo alla lista dei tweet da monitorare anche questo nuovo tweet
            tweet_id = new_tweet_id #aggiorno l'id del tweet più recente

        #Per ogni tweet in monitoraggio controllo i like ricevuti e i retweeters.
        for tweetMonitor in tweet_monitors:
            tweet_status = api.get_status(tweetMonitor.get_id())
            tweetMonitor.set_actual_likes(int(tweet_status._json['favorite_count']))
            tweetMonitor.set_actual_retweeters(int(tweet_status._json['retweet_count']))
            tweetMonitor.set_actual_followers(int(tweet_user.followers_count))

        #Mi prendo il numero attuale di followers
        #followers_count = int(tweet_user.followers_count)
        #Se il numero di followers nell'ultima chiamata supera il numero di followers ottenuto nel ciclo precedente
        #vuol dire che ci è stato un nuovo follower
        # if followers_count > prev_followers_count:
        #     print(str(tweet_user.screen_name) + " has got a new follower!")
        #     print("Followers: " + str(tweet_user.followers_count))
        #     prev_followers_count = followers_count #aggiorno il numero di follower totali
        #     new_followers_count = new_followers_count + 1 #incremento il contatore dei follower ottenuti
        #print("Waiting 10 secs...")

        time.sleep(10) #attendo 10 secondi

        # Verifico quanto tempo è passato, in particolare se la differenza è maggiore di un'ora cioè di 3600 secondi
        #time.time() restituisce il tempo in secondi.
        if time.time() - oldtime > HOUR:
            passed_hours = passed_hours + 1 #incremento il numero di ore passate
            oldtime = time.time()
            print("it has been a hour")
            for tweetMonitor in tweet_monitors:
                tweetMonitor.add_hour() #aggiorno ogni TweetMonitor in modo tale da tenere traccia del tempo di monitoring per ogni tweet

        if passed_hours == WAITING_HOURS:
            break
    if passed_hours == WAITING_HOURS:
        break

stopmonitoring = datetime.datetime.today()#timestamp del tempo in cui fermiamo il monitoring
print("Stop monitoring at:", stopmonitoring)
print(tweet_user.screen_name + " has got +" + str(new_followers_count) + " followers")
print("\t+", len(tweet_monitors), "Tweets have been tweeted")


data = pd.read_csv("dataset/tweet_dataset.csv", sep=",")#leggo il csv relativo al dataset

#mi creo la riga da inserire nel dataframe
row = {"user_id": tweet_user.id,
       "screen_name": tweet_user.screen_name}

for tweetMonitor in tweet_monitors:
    print("Tweet status:")
    print("ID:", tweetMonitor.get_id())
    print("The tweet within ", passed_hours, " hours has got:")
    print("\t+", tweetMonitor.get_likes_count(), " likes")
    print("\t+", tweetMonitor.get_retweeters_count(), " retweeters")
    weight = new_followers_count/tweet_user.followers_count +\
             tweetMonitor.get_likes_count()/tweetMonitor.get_actual_likes() +\
             tweetMonitor.get_retweeters_count()/tweetMonitor.get_actual_retweeters()
    print("\t Weight: ", weight)
    print("\tTopic list:", tweetMonitor.get_topics())

    row['followers_count'] = tweetMonitor.get_start_followers_count()
    row['tweet_id'] = tweetMonitor.get_id()
    row['tweet_text'] = tweetMonitor.get_text()
    row['start_retweeters_count'] = tweetMonitor.get_start_retweeters()
    row['start_tweet_likes_count'] = tweetMonitor.get_start_likes()
    row['start_monitoring_at'] = str(startmonitoring)
    row['stop_monitoring_at'] = str(stopmonitoring)
    row['num_hours'] = passed_hours
    row['new_followers_count'] = tweetMonitor.get_actual_followers()
    row['new_retweeters_count'] = tweetMonitor.get_actual_retweeters()
    row['new_tweet_likes_count'] = tweetMonitor.get_actual_likes()
    row['num_likes'] = tweetMonitor.get_likes_count()
    row['num_retweeters'] = tweetMonitor.get_retweeters_count()
    row['num_followers'] = tweetMonitor.get_followers_count()
    row['topic'] = tweetMonitor.get_topics()
    row['weight'] = weight

    data = data.append(row, ignore_index=True)


#print(data)
data.to_csv("dataset/tweet_dataset.csv", index=False)

print("Monitoring di", WAITING_HOURS,"ore terminato!")