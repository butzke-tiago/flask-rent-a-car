from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import ColumnExpressionArgument

db = SQLAlchemy()


def get_entry(model, id: int):
    entry = db.session.get(model, id)
    return entry


def get_entry_by(model, **kwargs):
    entry = db.session.execute(
        db.select(model).filter_by(**kwargs)
    ).scalar_one_or_none()
    return entry


def get_entries(model, ids: list):
    entries = (
        db.session.execute(db.select(model).where(model.id.in_(ids))).scalars().all()
    )
    return entries


def add_entry(entry):
    try:
        db.session.add(entry)
        db.session.commit()
    except:
        db.session.rollback()
        raise


def delete_entry(model, id):
    entry = db.session.get(model, id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return entry


def get_all_entries(model):
    entries = (
        db.session.execute(
            db.select(
                model,
            )
        )
        .scalars()
        .all()
    )
    return entries


def get_entries_filtered(model, **kwargs):
    entries = (
        db.session.execute(
            db.select(
                model,
            ).filter_by(**kwargs)
        )
        .scalars()
        .all()
    )
    return entries


def get_entries_joined_filtered(*models, filter: ColumnExpressionArgument[bool]):
    query = db.session.query(models[0])
    for model in models[1:]:
        query = query.join(model)
    query = query.filter(filter)
    return query.all()
