# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .factory import EndpointMixinFactory
from .schemas import CategorySchema, CategorySchemaNested, TagSchema, TagInputSchema
from .services import category_service, DuplicateCategoryError, tag_service
from .user import login_as_admin_required
from .utils.nav import *


# misc
from marshmallow import Schema, INCLUDE
from urllib.parse import unquote


def NAV_CREATE_CATEGORY():
    return (url_for(str(Category())), "Create Category")


blp = Blueprint("category", __name__, url_prefix="/category")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip, float=float)


@blp.route("/")
class Category(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
            schema=CategorySchema,
            info={},
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(CategorySchema, location="form")
    def post(self, category):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {category}.")
        nav = get_nav_by_user(current_user)
        try:
            category = category_service.create(**category)
        except DuplicateCategoryError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=CategorySchema,
                    info=category,
                ),
                409,
            )
        except Exception as e:
            app.logger.error(e)
            flash(
                f"An unexpected error {type(e).__name__!r} happened! Details: {e.__cause__}",
                "error",
            )
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=CategorySchema,
                    info=category,
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully created {self.blp.name} with id #{category.id}."
            )
            flash(f"{self.blp.name.capitalize()} {category.name!r} created!")
            return redirect(url_for(str(Categories())))


@blp.route("/all")
class Categories(MethodView, EndpointMixin):
    def get(self):
        categories = category_service.get_all()
        nav = get_nav_by_user(current_user)
        if current_user.is_admin():
            nav = [NAV_CREATE_CATEGORY()] + nav
        nav.remove(NAV_CATEGORIES())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
                "name": "categories",
                "headers": ["name", "fare", "models"],
                "rows": [
                    {
                        "name": category.name,
                        "fare": category.fare,
                        "models": len(list(category.models)),
                    }
                    for category in categories
                ],
                "refs": [
                    {"name": url_for(str(CategoryId()), category_id=category.id)}
                    for category in categories
                ],
            },
        )


@blp.route("/<category_id>")
class CategoryId(MethodView, EndpointMixin):
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, category_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{category_id}.")
        category = category_service.get(category_id)
        if category:
            is_owner = current_user.is_authenticated and current_user.is_admin()
            update = is_owner and "edit" in kwargs
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=category.name,
                submit="Update",
                nav=nav,
                schema=CategorySchema if update else CategorySchemaNested,
                info=CategorySchemaNested().dump(category),
                info_lists_url={"tags": {"url_prefix": "/tag/", "has_button": True}},
                is_owner=is_owner,
                update=update,
                tables=[
                    {
                        "name": "models",
                        "headers": ["picture", "name", "make"],
                        "rows": [
                            {
                                "name": model.name,
                                "make": model.make.name,
                                "picture": model.picture or "",
                            }
                            for model in category.models
                        ],
                        "refs": [
                            {
                                "name": url_for(
                                    str("model.ModelId"), model_id=model.id
                                ),
                                "make": url_for(
                                    str("make.MakeId"), make_id=model.make.id
                                ),
                            }
                            for model in category.models
                        ],
                        "pics": ["picture"],
                    },
                ],
            )
        else:
            message = f"{self.blp.name.capitalize()} #{category_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @login_required
    @login_as_admin_required
    @blp.arguments(CategorySchema, location="form")
    def post(self, category_info, category_id):
        app.logger.info(f"Updating {self.blp.name} #{category_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {category_info}.")
        try:
            category = category_service.update_category(category_id, **category_info)
        except DuplicateCategoryError as e:
            category = category_service.get(category_id)
            flash(f"{e}", "error")
            nav = [NAV_CREATE_CATEGORY()] + get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=category.name,
                submit="Update",
                nav=nav,
                schema=CategorySchema,
                info=category_info,
                is_owner=True,
                update=True,
            )
        if not category:
            abort(404)
        return redirect(url_for(str(CategoryId()), category_id=category_id))

    @login_required
    @login_as_admin_required
    def delete(self, category_id):
        app.logger.info(f"Deleting {self.blp.name} #{category_id}.")
        category = category_service.delete(category_id)
        if not category:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Categories()))), 303


@blp.route("/<category_id>/tags/")
class CategoryTags(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self, category_id):
        app.logger.info(f"Editing tags for {blp.name} #{category_id}.")
        category = category_service.get(category_id)
        if not category:
            app.logger.error(f"{blp.name.capitalize()} not found!")
            abort(404)
        tags = tag_service.get_all()
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/tags.html",
            title=f"{category.name}'s tags",
            submit="Update",
            nav=nav,
            schema=TagSchema,
            info=category.tags,
            tags=tags,
            is_owner=True,
            update=True,
            map=map_tags(category),
            done=url_for(str(CategoryId()), category_id=category_id),
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(TagInputSchema, unknown=INCLUDE, location="form", as_kwargs=True)
    def post(self, category_id, **kwargs):
        app.logger.info(f"Updating tags for {blp.name} #{category_id}.")
        category = category_service.get(category_id)
        if not category:
            app.logger.error(f"{blp.name.capitalize()} not found!")
            abort(404)
        app.logger.debug(f"Current tags are {[str(tag) for tag in category.tags]}.")
        if "available" in kwargs:
            tag_ids = kwargs["available"]
            app.logger.info(f"Adding tags #{tag_ids}.")
            tags = tag_service.get_many(tag_ids)
            if len(tags) != len(tag_ids):
                app.logger.error(
                    f"Some tags do not exist: {list(set(tag_ids).difference(set([tag.id for tag in tags])))}."
                )
                abort(400)
            app.logger.debug(f"Added tags are {[tag.name for tag in tags]}.")
            try:
                category_service.add_tags(category_id, tags)
            except ValueError as e:
                abort(400, e)
            except Exception as e:
                abort(500, e)
        if "assigned" in kwargs:
            tag_ids = kwargs["assigned"]
            app.logger.info(f"Removing tags #{tag_ids}.")
            tags = tag_service.get_many(tag_ids)
            if len(tags) != len(tag_ids):
                app.logger.error(
                    f"Some tags do not exist: {list(set(tag_ids).difference(set([tag.id for tag in tags])))}."
                )
                abort(400)
            app.logger.debug(f"Removed tags are {[tag.name for tag in tags]}.")
            try:
                category_service.remove_tags(category_id, tags)
            except ValueError as e:
                abort(400, e)
            except Exception as e:
                abort(500, e)
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/tags.html",
            title=f"{category.name}'s tags",
            submit="Update",
            nav=nav,
            schema=TagSchema,
            info=category.tags,
            is_owner=True,
            update=True,
            map=map_tags(category),
            done=url_for(str(CategoryId()), category_id=category_id),
        )


def map_tags(category):
    all_tags = tag_service.get_all()
    [all_tags.remove(tag) for tag in category.tags]
    return {
        "tags": {
            "assigned": {
                "name": "tags",
                "url": unquote(url_for("tag.TagId", tag_id={})),
                "options": (
                    {
                        "value": tag.id,
                        "name": tag.name,
                    }
                    for tag in sorted(category.tags, key=lambda x: x.name)
                ),
                "submit": {"text": ">>", "position": "right"},
            },
            "available": {
                "name": "tags",
                "url": unquote(url_for("tag.TagId", tag_id={})),
                "options": (
                    {
                        "value": tag.id,
                        "name": tag.name,
                    }
                    for tag in sorted(all_tags, key=lambda x: x.name)
                ),
                "submit": {"text": "<<", "position": "left"},
            },
        },
        "width": max([len(t.name) for t in all_tags + category.tags]),
    }
