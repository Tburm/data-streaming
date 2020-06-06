import numpy as np

order_book = {
    'timestamp': np.datetime64,
    'updated_at': np.int64,
    'pair': str,
    'order_type': str,
    'quantity': np.float64,
    'price': np.float64
}

trades = {
    'timestamp': np.datetime64,
    'updated_at': np.int64,
    'pair': str,
    'order_type': str,
    'quantity': np.float64,
    'price': np.float64
}
