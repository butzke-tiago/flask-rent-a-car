from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def get_all_entries(model):
    entries = [
        entry[0]
        for entry in db.session.execute(
            db.select(
                model,
            )
        ).all()
    ]
    return entries


def get_entries_filtered(model, **kwargs):
    entries = [
        entry[0]
        for entry in db.session.execute(
            db.select(
                model,
            ).filter_by(**kwargs)
        ).all()
    ]
    return entries
