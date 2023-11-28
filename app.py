from typing import List
import pika, sys, os, json
from dotenv import load_dotenv

import os
from requests import Session

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from db import crud, models
from db.engine import SessionLocal, engine


load_dotenv()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def callback(ch, method, properties, body):
    body: dict = json.loads(body)

    username: str = body['username']
    token_name: str = body['token_name']
    amount: int = body['amount']

    print(f" [x] Received {body}")

    # update inventory.
    db: Session = get_db()

    update = crud.update_inventory(db=db, token_name=token_name, amount=amount)
    if (update):
        print(f"update inventory success")
    else:
        print(f"roll back")


    ch.queue_declare(queue='from.inventory')

    ch.basic_publish(exchange='',
                        routing_key='from.inventory',
                        body=json.dumps(body))

    print(f" [x] Sent {json.dumps(body)}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

    return


def main():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbit-mq', port=5672))
    except:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

    models.Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    update = crud.create_inventory(db=db, token_name='token1', amount=100)

    channel = connection.channel()

    channel.queue_declare(queue='to.inventory', arguments={
                          'x-message-ttl' : 1000,
                          'x-dead-letter-exchange' : 'dlx',
                          'x-dead-letter-routing-key' : 'dl'
                          })

    channel.basic_consume(queue='to.inventory', on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)