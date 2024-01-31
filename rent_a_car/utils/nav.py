from flask import url_for


def NAV_CATEGORIES():
    return (url_for("category.Categories"), "Categories")


def NAV_MAKES():
    return (url_for("make.Makes"), "Makes")


def NAV_MODELS():
    return (url_for("model.Models"), "Models")


def NAV_STORES():
    return (url_for("store.Stores"), "Stores")


def NAV_TAGS():
    return (url_for("tag.Tags"), "Tags")


def NAV_VEHICLES():
    return (url_for("vehicle.Vehicles"), "Vehicles")


def get_nav_by_user(user):
    if user.is_anonymous:
        return []
    elif user.is_admin():
        return [
            NAV_STORES(),
            NAV_CATEGORIES(),
            NAV_MAKES(),
            NAV_MODELS(),
            NAV_TAGS(),
            NAV_VEHICLES(),
        ]
    elif user.is_franchisee():
        return [
            NAV_STORES(),
            NAV_CATEGORIES(),
            NAV_MAKES(),
            NAV_MODELS(),
            NAV_TAGS(),
            NAV_VEHICLES(),
        ]
    elif user.is_client():
        return [
            NAV_STORES(),
            NAV_CATEGORIES(),
            NAV_MODELS(),
        ]
    else:
        return []
