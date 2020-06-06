import os
import sys
import signal
import shutil
from datetime import datetime
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import websockets

## globals
market = os.getenv('BN_MARKET')

## logging
default_log = f'./data/log.json'
logger = logging.getLogger(__name__)

# set up handler
def rotator(source=default_log, dest=None):
    # get the last record
    print('Rotating file')
    with open(source, 'r') as  f:
        last_record = f.readlines()[-1]

        # parse the data
        last_record = json.loads(last_record)
        last_trade_id = last_record['trade_id']
        market = last_record['pair']

        f.seek(0)

    shutil.move(source, f'/data/raw/trades/{market}_{last_trade_id}.json')
    pass

handler = logging.handlers.RotatingFileHandler(default_log, maxBytes=20*(1024**2), backupCount=10)
handler.rotator = rotator

logger.addHandler(handler)
logger.setLevel(logging.INFO)

## set up websockets
async def consumer(message, market):
    message = json.loads(message)
    print(f'{message["T"]}: Started')

    # get current time for logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # set up the records for the file
    trade = {
        'timestamp': timestamp,
        'trade_id': message['a'],
        'trade_at': message['T'],
        'pair': market,
        'maker': message['m'],
        'quantity': message['q'],
        'price': message['p']
    }

    # write data to log
    data = json.dumps(trade)
    logger.info(data)

    print(f'{message["T"]}: Complete')
    pass

async def consumer_handler(websocket, market):
    async for message in websocket:
        await consumer(message, market)

async def connect(market):
    uri = f"wss://stream.binance.com:9443/ws/{market}@aggTrade"
    async with websockets.connect(uri) as websocket:
        print('connected to stream')
        await consumer_handler(websocket, market)

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
