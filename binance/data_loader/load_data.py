import os
import shutil
import time
import schemas
from dask.distributed import Client
import dask.dataframe as dd

TABLE_NAME = os.environ['TABLE_NAME']
SOURCE = f'/data/raw/{TABLE_NAME}'
DESTINATION = f'/data/default/{TABLE_NAME}'

if __name__ == '__main__':
    # start the client
    client = Client()

    # find the files that exist
    fnames = [f'{SOURCE}/{fname}' for fname in os.listdir(SOURCE)]

    # read in existing data
    df = dd.read_json(
        fnames,
        dtype=getattr(schemas, TABLE_NAME)
    )

    # add a column for partitions
    df['hour'] = df['timestamp'].dt.floor('h')

    # write out files
    start_time = time.time()
    df.to_parquet(
        DESTINATION,
        engine='fastparquet',
        append=True,
        compression='gzip',
        partition_on=['pair', 'hour'],
        write_index=False
    )
    duration = time.time() - start_time
    print(f'That took {duration} seconds')

    # clean up files
    for f in fnames:
        shutil.copy(f, f'/archive/raw/{TABLE_NAME}/{f.split("/")[-1]}')
        os.remove(f)
