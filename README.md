## Data Streaming

This repository is a collection of Docker images that connect to openly available data sources. The following images will stream data from these sources and process the data into a usable format.

### Binance

Binance is a cryptocurrency exchange with many available websocket data streams. The included Docker compose file can be used to configure many containers to connect to these streams and store the data.

- `get_order_book`: Connect to the order book depth data stream and write the results to files.
- `get_trades`: Connect to the trades data stream and write the results to files.
- `data_loader`: Process the raw json files by validating schema and writing to partitioned parquet files.
