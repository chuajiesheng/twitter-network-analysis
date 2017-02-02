# Network Analysis using Twitter Data

This project is using Twitter JSON data downloaded from GNIP.

It is part of my master capstone project to analyse various trend 
(from a communication standpoint) on various corporate crisis.

## Event milestones
```
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
```
1. 02 Nov 2015 - First outbreak (after report "Chipotle temporarily closes 43 units after E. coli outbreak" by Jennings, Lisa)
1. 20 Nov 2015 - Second outbreak (after report "Chipotle E. coli outbreak includes three new states" by Jennings, Lisa)
1. 10 Dec 2015 - CEO apology (TV)
1. 16 Dec 2015 - CEO apology (Newspaper)

Various milestone have been identified and tweets before and after the milestone is being split into blocks.

[tweet_period/split_by_period.py](tweet_period/split_by_period.py) will split the JSON files from the 
[source](tweet_period/input) and place the file (named according to the blocks) to the [destination](tweet_period/output) 