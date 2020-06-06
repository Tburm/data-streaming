import os
import sys
import signal
import shutil
from datetime import datetime
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import requests
import websockets

## globals
market = os.getenv('BN_MARKET')
order_book = None

## logging
default_log = f'./data/log.json'
logger = logging.getLogger(__name__)

# set up handler
def rotator(source, dest):
    # get the last record
    print('Rotating file')
    with open(source, 'r') as  f:
        last_record = f.readlines()[-1]

        # parse the data
        last_record = json.loads(last_record)
        updated_at = last_record['updated_at']
        market = last_record['pair']

        f.seek(0)

    shutil.move(source, f'/data/raw/order_book/{market}_{updated_at}.json')

handler = logging.handlers.RotatingFileHandler(default_log, maxBytes=100*(1024**2), backupCount=10)
handler.rotator = rotator

logger.addHandler(handler)
logger.setLevel(logging.INFO)

## set up websockets
async def consumer(message, market, order_book):
    message = json.loads(message)
    print(f'{message["u"]}: Started')

    # update the order book
    for b in message['b']:
        if b[1] == '0.00000000':
            order_book['bids'].pop(b[0], None)
        else:
            order_book['bids'][b[0]] = b[1]

    for a in message['a']:
        if a[1] == '0.00000000':
            order_book['asks'].pop(a[0], None)
        else:
            order_book['asks'][a[0]] = a[1]

    order_book['last_updated'] = str(message['u'])

    # get current time for logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # set up the records for the file
    send_bids = [{
        'timestamp': timestamp,
        'updated_at': message['u'],
        'pair': market,
        'order_type': 'bid',
        'quantity': b[1],
        'price': b[0]
    } for b in order_book['bids'].items()]

    send_asks = [{
        'timestamp': timestamp,
        'updated_at': message['u'],
        'pair': market,
        'order_type': 'ask',
        'quantity': a[1],
        'price': a[0]
    } for a in order_book['asks'].items()]

    # create a file buffer and write data to it
    send_data = send_bids + send_asks

    for o in send_bids + send_asks:
        data = json.dumps(o)
        logger.info(data)

    print(f'{message["u"]}: Complete')
    pass

def get_order_book(market):
    ob = requests.get(f'https://www.binance.com/api/v3/depth?symbol={market.upper()}&limit=100')
    if ob.status_code == 200:
        ob = ob.json()
        order_book = {
            'asks': dict(ob['asks']),
            'bids': dict(ob['bids'])
        }
        order_book['last_updated'] = ob['lastUpdateId']
        return order_book

async def consumer_handler(websocket, market, order_book):
    async for message in websocket:
        await consumer(message, market, order_book)

async def connect(market):
    uri = f"wss://stream.binance.com:9443/ws/{market}@depth@1000ms"
    async with websockets.connect(uri) as websocket:
        order_book = get_order_book(market)
        await consumer_handler(websocket, market, order_book)

def send_last_file(default_log=default_log):
    if os.path.exists(default_log):
        rotator(default_log, None)

def last_file_handler(signum, frame):
    send_last_file()
    print('last file sent')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, last_file_handler)
    signal.signal(signal.SIGTERM, last_file_handler)

    asyncio.get_event_loop().run_until_complete(connect(market))
    asyncio.get_event_loop().run_forever()
