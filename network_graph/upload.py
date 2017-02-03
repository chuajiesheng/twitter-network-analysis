import os
from datetime import timezone, timedelta, datetime
import json
from py2neo import Graph, Node, Relationship, NodeSelector

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


# Read directory
DIRECTORY = './tweet_period/input'
convert_to_full_path = lambda p: '{}/{}'.format(DIRECTORY, p)
files = list(map(convert_to_full_path, read_directory(DIRECTORY)))
assert len(files) == 21888


# Logs
dot = lambda: print('.', end='', flush=True)
skip = lambda: print('-', end='', flush=True)
changed = lambda: print('+', end='', flush=True)

# Verify files
VERIFY_FILES = False
if VERIFY_FILES:
    for f in files:
        read_file(f)
        dot()

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
PACIFIC = timezone(-timedelta(hours=8))
MILESTONES = [datetime(2015, 11, 2, tzinfo=PACIFIC),
              datetime(2015, 11, 20, tzinfo=PACIFIC),
              datetime(2015, 12, 10, tzinfo=PACIFIC),
              datetime(2015, 12, 16, tzinfo=PACIFIC)]

print_date = lambda dt: dt.isoformat(timespec='microseconds')
print('Milestones:', list(map(print_date, MILESTONES)))


# Split
def test_date(dt, milestones=MILESTONES):
    for b in range(0, len(milestones)):
        if dt < milestones[b]:
            return b
    return 4

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def setup():
    ENDPOINT = 'bolt://localhost:7687'
    USERNAME = 'neo4j'
    PASSWORD = '!abcd1234'
    graph = Graph(password=PASSWORD)
    return graph


def find_user(graph, name):
    selector = NodeSelector(graph)
    return selector.select('TwitterUser', name=name).first()


def find_user_by_display_name(graph, display_name):
    selector = NodeSelector(graph)
    return selector.select('TwitterUser', display_name=display_name).first()


def add_user(graph, name, display_name, link):
    existing_user = find_user(graph, name)
    if existing_user:
        skip()
        return existing_user

    node = Node('TwitterUser', name=name, display_name=display_name, link=link)
    graph.create(node)
    changed()
    return node


def find_relation(graph, start_node, link):
    for rel in graph.match(start_node=start_node):
        if rel['link'] == link:
            return rel

    return None


def add_relation(graph, source_node, destination_node, rel_type, tweet_id, link, block):
    existing_rel = find_relation(graph, source_node, link)
    if existing_rel:
        skip()
        return existing_rel

    rls = Relationship(source_node, rel_type, destination_node, tweet_id=tweet_id, link=link, block=block)
    graph.create(rls)
    changed()
    return rls

graph = setup()
DUMMY_USER = 'empty'
dummy_user = add_user(graph, DUMMY_USER, DUMMY_USER, DUMMY_USER)


def read_and_export(filename):
    tweets = read_file(filename)

    rejected_tweets = []
    for t in tweets:
        rejected_tweets.append(process_tweet(t))

    return rejected_tweets


def process_tweet(tweet):
    is_reply = lambda tweet: 'inReplyTo' in tweet.keys() and tweet['inReplyTo']
    is_retweet = lambda tweet: tweet['verb'] == 'share'

    posted_time = datetime.strptime(tweet['postedTime'], DATETIME_FORMAT).replace(tzinfo=timezone.utc)
    tweet_id = tweet['id'][tweet['id'].rindex(':') + 1:]

    if not is_reply(tweet) and not is_retweet(tweet):
        u = add_user(graph, tweet['actor']['id'], tweet['actor']['preferredUsername'], tweet['actor']['link'])
        add_relation(graph, u, dummy_user, 'tweet', tweet_id, tweet['link'], test_date(posted_time))
    elif is_reply(tweet):
        replying_to_tweet = tweet['inReplyTo']['link']
        replying_to_user = replying_to_tweet.split('/')[3]

        reply_to = find_user_by_display_name(graph, replying_to_user)
        if not reply_to:
            return tweet

        u = add_user(graph, tweet['actor']['id'], tweet['actor']['preferredUsername'], tweet['actor']['link'])
        add_relation(graph, u, reply_to, 'reply', tweet_id, tweet['link'], test_date(posted_time))
    elif is_retweet(tweet):
        src = add_user(graph, tweet['actor']['id'], tweet['actor']['preferredUsername'], tweet['actor']['link'])
        dest = add_user(graph, tweet['object']['actor']['id'], tweet['object']['actor']['preferredUsername'], tweet['object']['actor']['link'])
        add_relation(graph, src, dest, 'retweet', tweet_id, tweet['link'], test_date(posted_time))
    else:
        print('Alien:', tweet['id'])


all_rejected_tweets = []
for f in files:
    rejected = read_and_export(f)
    all_rejected_tweets += rejected
    dot()

new_rejected_tweets = []
tries_left = 10
while tries_left > 0:
    print('Tries:', tries_left, 'Rejected:', len(all_rejected_tweets), end='', flush=True)

    for t in all_rejected_tweets:
        rejected = process_tweet(t)
        new_rejected_tweets.append(rejected)

    all_rejected_tweets = new_rejected_tweets
    new_rejected_tweets = []

print('Remaining rejected:', len(all_rejected_tweets))
