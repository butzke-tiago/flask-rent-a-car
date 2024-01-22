from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def get_entry(model, id):
    entry = db.session.get(model, id)
    return entry


def get_entry_by(model, **kwargs):
    entry = db.session.execute(
        db.select(model).filter_by(**kwargs)
    ).scalar_one_or_none()
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
