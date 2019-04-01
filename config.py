import sys

HOST = 'https://www.ptt.cc'
BOARD = sys.argv[1] or 'Gossiping'
PAGE = int(sys.argv[2])
NO_PAGE = int(sys.argv[3])
TOTAL_PAGE = ''
ES_URL = "10.30.0.121:9200"
ES_INDEX = "ptt-v1"
