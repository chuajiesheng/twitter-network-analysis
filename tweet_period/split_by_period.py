import os
from datetime import timezone, timedelta, datetime
import json

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

# Verify files
dot = lambda: print('.', end='', flush=True)
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

BASE_FILE_OUT = './tweet_period/output/block_{}.json'
split_to_files = [BASE_FILE_OUT.format(i) for i in range(0, len(MILESTONES) + 1)]
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def write_to(block, json_object, list_of_files=split_to_files):
    with open(list_of_files[block], 'a') as f:
        json.dump(json_object, f)


def read_and_split(filename):
    tweets = read_file(filename)
    for t in tweets:
        posted_time = datetime.strptime(t['postedTime'], DATETIME_FORMAT).replace(tzinfo=timezone.utc)
        block = test_date(posted_time)
        write_to(block, t)

for f in files:
    read_and_split(f)
    dot()
