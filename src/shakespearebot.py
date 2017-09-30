import tweepy
import configparser
from random import choice
from random import randint
from nltk.corpus import shakespeare
from textblob import TextBlob
import time
import yaml
import datetime

#Initialize parser for reading config file
config = configparser.ConfigParser()

#Read from config file in the above directory
config.read('../config.ini')

#Uses keys defined in the config.ini file to authenticate connection with twitter account
#Don't forget to add your keys to config.ini
auth = tweepy.OAuthHandler(config['OAuth']['public'], config['OAuth']['private'])
auth.set_access_token(config['AccessToken']['public'],config['AccessToken']['private'])

#Initialize Tweepy api with authentication keys
api = tweepy.API(auth)


def main():

    while True:
        error = False

        if not error and time_range(datetime.time(8, randint(0, 59), 0), datetime.time(22, randint(0, 59), 0)):
            print('Doing some tweeting')
            #error = generateTweet()

        if error:
            print("Rate limit reached\nCooling off...")
            time.sleep(120)

        print("Follow users")
        #error = follow_users()

        if error:
            print("Rate limit reached\nCooling off...")
            time.sleep(120)

        #Check for mentions and reply to them
        mentions = None
        since_id = config['ID']['since_id']
        while True:
            try:
                mentions = api.search(q='@RealBillyShake' + '-filter:retweets', count=100, since_id=since_id)
                if not mentions:
                    print("No mentions found")
                    break
                for tweet in mentions:

                    if int(tweet.id) > int(since_id):
                        since_id = tweet.id
                        reply_tweets(tweet)

            except tweepy.TweepError as e:
                print("some error : " + str(e))
                break
        config.set('ID', 'since_id', str(since_id))

        with open('../config.ini', 'w') as configfile:
            config.write(configfile)

        sleep = randint(120, 14400)
        print('Sleeping for ' + str(sleep) + "\nStarted at " + str(datetime.datetime.now().time()))
        time.sleep(sleep)



def generateTweet():
    files = list(shakespeare.fileids())
    randFile = choice(files)

    play = shakespeare.xml(randFile)

    characters = list(speaker.text for speaker in play.findall('*/*/*/SPEAKER'))
    character = choice(characters)

    error = False
    # loop through text of the selected play
    for x in play:
        if error:
            break
        text = list(x.itertext())
        for y in range(0, len(text) - 1):
            # Find text that matches the selected characters name
            if text[y].lower() == character.lower():
                # Add this characters lines to the tweet
                add = 2
                tweet = ''
                tweet += text[y + add]
                add += 1
                newLine = False
                # Continue adding lines till ending punctuation . or ! or ? is found
                try:

                    while not tweet.endswith('.') or not tweet.endswith('!') or not tweet.endswith('?'):
                        #Check for new line character occurring twice
                        if '\n' in text[y + add] and newLine:
                            break
                        #Check for first occurrence of new line char
                        if '\n' in text[y + add]:
                            newLine = True

                        #If it isn't a new line char add to the tweet
                        if not '\n' in text[y + add]:
                            tweet += ' ' + text[y + add]
                            newLine = False
                        add += 1

                except IndexError:
                    pass
                try:
                    # Randomly select if a tweet should be posted and insure proper length
                    if randint(0, 15) == 2 and len(tweet) <= 140 and len(tweet) != 0:
                        print(tweet)
                        api.update_status(tweet)

                        time.sleep(240)
                        if not time_range(datetime.time(randint(8), randint(0, 59), 0), datetime.time(22, randint(0, 59), 0)):
                             return error
                except tweepy.error.RateLimitError:
                    error = True
                    break
    return error

#TODO: Add logic for reply tweets
def reply_tweets(mention):
    '''Reply to mentions on twitter'''
    #Analyze parts of speech of mention and get sentiment
    analysis = TextBlob(mention.text)
    sent = analysis.sentiment

    #Say something mean
    if sent.polarity < 5.0 or mention.lower().contains('roastme'):
        #Generate random insult
        insults = yaml.load(open('../insults.yml'))
        insult = '@' + mention.user.screen_name + ' thou ' + choice(insults['column1']) + ' ' \
                 + choice(insults['column2']) + ' ' + choice(insults['column3'])
        print(insult)
        #api.update_status(insult, mention.id)
    #Say something nice
    elif sent.polarity >= 5.0:
        comps = yaml.load(open('../insults.yml'))
        compliment = '@' + mention.user.screen_name + ' thou ' + choice(comps['column1']) + ' ' \
                 + choice(comps['column2']) + ' ' + choice(comps['column3'])
        print(compliment)
        #api.update_status(compliment, mention.id)



#TODO: Add logic for replying to direct messages
def direct_message_reply():
    pass



#TODO: Add logic for tagging people in tweets
def tagged_tweet():
    pass


def delete_tweets():
    '''Deletes 20 most recent tweets'''
    for x in api.user_timeline():
        print("Delete")
        api.destroy_status(x.id)


def follow_users():
    '''Finds random users to follow'''
    try:
        count = 0
        for friend in api.me().friends():
            for x in friend.friends():
                if not x.following:
                    print("Now following " + x.screen_name)
                    api.create_friendship(x.screen_name)
                    count += 1
                if count >= 10:
                    return False
                time.sleep(60)
    except tweepy.error.RateLimitError:
        return True

    return False


def time_range(start, end):
    '''Stops will from tweeting past bed time'''
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end

main()
