from flask import url_for
from .models import UserRole


def NAV_CATEGORIES():
    return (url_for("category.Categories"), "Categories")


def NAV_MAKES():
    return (url_for("make.Makes"), "Makes")


def NAV_MODELS():
    return (url_for("model.Models"), "Models")


def NAV_STORES():
    return (url_for("store.Stores"), "Stores")


def get_nav_by_role(role):
    if role == UserRole.ADMIN:
        return [NAV_STORES(), NAV_CATEGORIES(), NAV_MAKES(), NAV_MODELS()]
    elif role == UserRole.FRANCHISEE:
        return [NAV_STORES(), NAV_CATEGORIES(), NAV_MAKES(), NAV_MODELS()]
    elif role == UserRole.CLIENT:
        return [NAV_STORES()]
    else:
        return []
