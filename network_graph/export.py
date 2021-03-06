import os
from datetime import timezone, timedelta, datetime
import json
import csv

def read_directory(directory_name):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(directory_name):
        files.extend(filenames)
        break

    return files


def read_file(filename):
    is_tweet = lambda json_object: 'verb' in json_object and (json_object['verb'] == 'post' or json_object['verb'] == 'share')

    tweets = []

    with open(filename) as f:
        for line in f:
            if len(line.strip()) < 1:
                continue

            json_object = json.loads(line)
            if is_tweet(json_object):
                tweets.append(json_object)
            else:
                # this is a checksum line
                activity_count = int(json_object['info']['activity_count'])
                assert len(tweets) == activity_count

    return tweets


def get_sentiment_file(filename):
    relevance = dict()
    sentiment = dict()

    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            relevance[row['id']] = row['relevance']
            sentiment[row['id']] = row['sentiment']

    return relevance, sentiment

# Read directory
DIRECTORY = './network_graph/input/tweets'
LABELLED_TWEETS = './network_graph/input/sentiment.csv'

relevance_labels, sentiment_labels = get_sentiment_file(LABELLED_TWEETS)
assert len(relevance_labels.keys()) == 2612018
assert len(sentiment_labels.keys()) == 2612018

tweets = set(list(relevance_labels.keys()) + list(sentiment_labels.keys()))
assert len(tweets) == 2612018

convert_to_full_path = lambda p: '{}/{}'.format(DIRECTORY, p)
files = list(map(convert_to_full_path, read_directory(DIRECTORY)))
assert len(files) == 21888

# Logs
dot = lambda: print('.', end='', flush=True)
skip = lambda: print('-', end='', flush=True)
changed = lambda: print('+', end='', flush=True)

# Periods
'''
02 Nov 2015 - First outbreak (after report "Chipotle temporarily closes 43 units after E. coli outbreak" by Jennings, Lisa)
20 Nov 2015 - Second outbreak (after report "Chipotle E. coli outbreak includes three new states" by Jennings, Lisa)
10 Dec 2015 - CEO apology (TV)
16 Dec 2015 - CEO apology (Newspaper)
'''
'''
              ┌───────────┐        ┌───────────┐        ┌───────────┐        ┌───────────┐
              │02-Nov-2015│        │20-Nov-2015│        │10-Dec-2015│        │16-Dec-2015│
              └───────────┘        └───────────┘        └───────────┘        └───────────┘
                    ▲                    ▲                    ▲                    ▲
                    │                    │                    │                    │
┌──────────────────┐│┌──────────────────┐│┌──────────────────┐│┌──────────────────┐│┌──────────────────┐
│   Before first   │││  Before second   │││Before CEO apology│││Before CEO apology│││After CEO apology │
│     outbreak     │││     outbreak     │││       (TV)       │││   (Newspaper)    │││   (Newspaper)    │
│                  │││                  │││                  │││                  │││                  │
│     Block #0     │││     Block #1     │││     Block #2     │││     Block #3     │││     Block #4     │
└──────────────────┘│└──────────────────┘│└──────────────────┘│└──────────────────┘│└──────────────────┘
                    │                    │                    │                    │
'''
EASTERN = timezone(-timedelta(hours=5))
MILESTONES = [datetime(2015, 11, 2, tzinfo=EASTERN),
              datetime(2015, 11, 20, tzinfo=EASTERN),
              datetime(2015, 12, 10, tzinfo=EASTERN),
              datetime(2015, 12, 16, tzinfo=EASTERN)]

print_date = lambda dt: dt.isoformat(timespec='microseconds')
print('Milestones:', list(map(print_date, MILESTONES)))


# Split
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_date_string(date_str, milestones=MILESTONES):
    dt = datetime.strptime(date_str, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
    for b in range(0, len(milestones)):
        if dt < milestones[b]:
            return b
    return 4


def read_and_export(filename, tweet_set, relevance_labels, sentiment_labels):
    tweets = read_file(filename)

    for t in tweets:
        process_tweet(tweet_set, relevance_labels, sentiment_labels, t)


USERS_FILE = './network_graph/output/users.csv'
TWEETS_FILE = './network_graph/output/tweets.csv'
RETWEETS_FILE = './network_graph/output/retweets.csv'
REPLIES_FILE = './network_graph/output/replies.csv'
RELATIONSHIP_FILE = './network_graph/output/relation.csv'

users_file = open(USERS_FILE, 'w')
tweets_file = open(TWEETS_FILE, 'w')
retweets_file = open(RETWEETS_FILE, 'w')
replies_file = open(REPLIES_FILE, 'w')
relationship_file = open(RELATIONSHIP_FILE, 'w')

users_file.write('userId:ID,link,preferred_username\n')
tweets_file.write('tweetId:ID,link,posted_time,period,relevance,sentiment\n')
retweets_file.write('tweetId:ID,link,posted_time,period,relevance,sentiment\n')
replies_file.write('tweetId:ID,link,posted_time,period,relevance,sentiment\n')
relationship_file.write(':START_ID,:END_ID,:TYPE\n')


is_reply = lambda tweet: 'inReplyTo' in tweet.keys() and tweet['inReplyTo']
is_retweet = lambda tweet: tweet['verb'] == 'share'
print_user = lambda user_id, user_link, user_preferred_username: users_file.write(
    '{},"{}","{}"\n'.format(user_id, user_link, user_preferred_username))
print_tweet = lambda tweet_id, tweet_link, tweet_posted_time, tweet_period, relevance, sentiment: tweets_file.write(
    '"{}","{}",{},{},{},{}\n'.format(tweet_id, tweet_link, tweet_posted_time, tweet_period, relevance, sentiment))
print_retweet = lambda retweet_id, retweet_link, retweet_posted_time, retweet_period, relevance, sentiment: retweets_file.write(
    '"{}","{}",{},{},{},{}\n'.format(retweet_id, retweet_link, retweet_posted_time, retweet_period, relevance, sentiment))
print_reply = lambda reply_id, reply_link, reply_posted_time, reply_period, relevance, sentiment: replies_file.write(
    '"{}","{}",{},{},{},{}\n'.format(reply_id, reply_link, reply_posted_time, reply_period, relevance, sentiment))


def process_tweet(labelled_set, relevance_labels, sentiment_labels, tweet):
    tweet_id = tweet['id']
    if tweet_id not in labelled_set:
        return

    user_id = tweet['actor']['id']
    user_link = tweet['actor']['link']
    user_preferred_username = tweet['actor']['preferredUsername']
    print_user(user_id, user_link, user_preferred_username)

    if is_retweet(tweet):
        # Save original tweet user details
        user_id = tweet['object']['actor']['id']
        user_link = tweet['object']['actor']['link']
        user_preferred_username = tweet['object']['actor']['preferredUsername']
        print_user(user_id, user_link, user_preferred_username)

    tweet_user = user_id
    tweet_link = tweet['link']
    tweet_posted_time = tweet['postedTime']
    tweet_period = test_date_string(tweet_posted_time)

    tweet_relevance = relevance_labels[tweet_id]
    tweet_sentiment = sentiment_labels[tweet_id]

    relationship_file.write('"{}","{}",{}\n'.format(tweet_user, tweet_id, 'POSTED'))
    if is_retweet(tweet):
        retweet_of = tweet['object']['id']
        print_retweet(tweet_id, tweet_link, tweet_posted_time, tweet_period, tweet_relevance, tweet_sentiment)
        relationship_file.write('"{}","{}",{}\n'.format(tweet_id, retweet_of, 'OF'))
    elif is_reply(tweet):
        reply_link = tweet['inReplyTo']['link']
        reply_to = 'tag:search.twitter.com,2005:' + reply_link.split('/')[5]
        print_reply(tweet_id, tweet_link, tweet_posted_time, tweet_period, tweet_relevance, tweet_sentiment)
        relationship_file.write('"{}","{}",{}\n'.format(tweet_id, reply_to, 'REPLY_TO'))
    else:
        print_tweet(tweet_id, tweet_link, tweet_posted_time, tweet_period, tweet_relevance, tweet_sentiment)

for f in files:
    read_and_export(f, tweets, relevance_labels, sentiment_labels)
    dot()


users_file.close()
tweets_file.close()
retweets_file.close()
replies_file.close()
relationship_file.close()
