FROM python:3.8-slim

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD exec python get_order_book.py
