from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import NoResultFound

from . import models



def get_inventory(db: Session, token_name: str):
    return db.query(models.Inventory).filter(models.Inventory.token_name == token_name).first()

def update_inventory(db: Session, token_name: str, amount: int):
    inventory = get_inventory(db=db, token_name=token_name)
    if (inventory):
        if (inventory.total_amount - amount > 0):
            db.query(models.Inventory).filter(models.Inventory.token_name == token_name).update({'total_amount': inventory.total_amount - amount})
            db.commit()
            return True
        return False
    return False

def create_inventory(db: Session, token_name: str, amount: int):
    inventory = get_inventory(db=db, token_name=token_name)
    if (inventory is None):
        db_inventory = models.Inventory(token_name=token_name, total_amount=amount)
        db.add(db_inventory)
        db.commit()
        db.refresh(db_inventory)
        return db_inventory