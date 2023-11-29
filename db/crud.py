from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import NoResultFound
from . import models


async def get_inventory(db: AsyncSession, token_name: str):
    result = await db.execute(models.Inventory.__table__.select().where(models.Inventory.token_name == token_name))
    if result is not None:
        return result.fetchone()
    return None

async def update_inventory(db: AsyncSession, token_name: str, amount: int):
    inventory = await get_inventory(db=db, token_name="late_token")
    if inventory:
        if inventory.total_amount - amount > 0:
            await db.execute(models.Inventory.__table__.update().where(models.Inventory.token_name == token_name).values({'total_amount': inventory.total_amount - amount}))
            return True
        return False
    return False

async def roll_back_inventory(db: AsyncSession, token_name: str, amount: int):
    inventory = await get_inventory(db=db, token_name="late_token")
    if inventory:
        await db.execute(models.Inventory.__table__.update().where(models.Inventory.token_name == token_name).values({'total_amount': inventory.total_amount + amount}))
        return True
    return False

async def create_inventory(db: AsyncSession, amount: int):
    inventory = await get_inventory(db=db, token_name="late_token")
    if inventory is None:
        db_inventory = models.Inventory(token_name="late_token", total_amount=amount)
        db.add(db_inventory)
        await db.flush()
        await db.commit()
        await db.refresh()
        return db_inventory
    return inventory
