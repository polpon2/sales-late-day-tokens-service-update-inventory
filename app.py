import asyncio, aio_pika, json
from db.engine import SessionLocal, engine
from db import crud, models

async def process_message(
    message: aio_pika.abc.AbstractIncomingMessage,
    connection: aio_pika.Connection,  # Add connection parameter
) -> None:
    async with message.process():
        body: dict = json.loads(message.body)

        username: str = body['username']
        amount: int = body['amount']

        print(f" [x] Received {body}")

        # Manage Inventory.
        async with SessionLocal() as db:
            update = await crud.update_inventory(db=db, token_name="late_token", amount=1)
            if (update):
                routing_key = "from.inventory"

                channel = await connection.channel()

                await channel.default_exchange.publish(
                    aio_pika.Message(body=message.body),
                    routing_key=routing_key,
                )
                print(f"update inventory success")
                await db.commit()
            else:
                print(f"roll back")




async def main() -> None:
    connection = await aio_pika.connect_robust(
        "amqp://rabbit-mq",
    )

    # Init the tables in db
    async with engine.begin() as conn:
        # Drop all table every time
        await conn.run_sync(models.Base.metadata.drop_all)

        # Init all table every time
        await conn.run_sync(models.Base.metadata.create_all)

        # Init Value
        await conn.execute(
            models.Inventory.__table__.insert(), [{"token_name": "late_token", "total_amount": 500}]
        )

    queue_name = "to.inventory"

    # Creating channel
    channel = await connection.channel()

    # Maximum message count which will be processing at the same time.
    await channel.set_qos(prefetch_count=10)

    # Declaring queue
    queue = await channel.declare_queue(queue_name, arguments={
                                                    'x-message-ttl' : 1000,
                                                    'x-dead-letter-exchange' : 'dlx',
                                                    'x-dead-letter-routing-key' : 'dl'
                                                    })

    print(' [*] Waiting for messages. To exit press CTRL+C')

    await queue.consume(lambda message: process_message(message, connection))

    try:
        # Wait until terminate
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())