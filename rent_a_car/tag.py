# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .factory import EndpointMixinFactory
from .schemas import TagSchema, TagSchemaNested
from .services import tag_service, DuplicateTagError
from .user import login_as_admin_required, login_as_operator_required
from .utils.nav import *

# misc
from marshmallow import Schema, INCLUDE


def NAV_CREATE_TAG():
    return (url_for(str(Tag())), "Create Tag")


blp = Blueprint("tag", __name__, url_prefix="/tag")

EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip)


@blp.route("/")
class Tag(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
            schema=TagSchema,
            info={},
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(TagSchema, location="form")
    def post(self, tag_input):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {tag_input}.")
        nav = get_nav_by_user(current_user)
        try:
            tag = tag_service.create(**tag_input)
        except DuplicateTagError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=TagSchema,
                    info=tag_input,
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
                    schema=TagSchema,
                    info=tag_input,
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully created {type(self).__name__} with id #{tag.id}."
            )
            flash(f"{type(self).__name__} {tag.name!r} created!")
            return redirect(url_for(str(Tags())))


@blp.route("/all")
class Tags(MethodView, EndpointMixin):
    @login_required
    @login_as_operator_required
    def get(self):
        tags = tag_service.get_all()
        nav = get_nav_by_user(current_user)
        if current_user.is_admin():
            nav = [NAV_CREATE_TAG()] + nav
        nav.remove(NAV_TAGS())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
                "name": "tags",
                "headers": ["name"],
                "rows": [
                    {
                        "name": tag.name,
                    }
                    for tag in tags
                ],
                "refs": [
                    {"name": url_for(str(TagId()), tag_id=tag.id)} for tag in tags
                ],
            },
        )


@blp.route("/<tag_id>")
class TagId(MethodView, EndpointMixin):
    @login_required
    @login_as_operator_required
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, tag_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{tag_id}.")
        tag = tag_service.get(tag_id)
        if tag:
            is_owner = current_user.is_admin()
            update = is_owner and "edit" in kwargs
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=tag.name,
                submit="Update",
                nav=nav,
                schema=TagSchema if update else TagSchemaNested,
                info={
                    "name": tag.name,
                    "categories": tag.categories,
                    "models": tag.models,
                },
                info_lists_url={
                    "categories": {"url_prefix": "/category/"},
                    "models": {"url_prefix": "/model/"},
                },
                is_owner=is_owner,
                update=update,
            )
        else:
            message = f"Tag #{tag_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @login_required
    @login_as_admin_required
    @blp.arguments(TagSchema, location="form")
    def post(self, tag_info, tag_id):
        app.logger.info(f"Updating {self.blp.name} #{tag_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {tag_info}.")
        tag = tag_service.get(tag_id)
        if not tag:
            abort(404)
        try:
            tag = tag_service.update(tag_id, **tag_info)
        except DuplicateTagError as e:
            tag = tag_service.get(tag_id)
            flash(f"{e}", "error")
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=tag.name,
                submit="Update",
                nav=nav,
                schema=TagSchema,
                info={
                    "name": tag_info["name"],
                },
                is_owner=True,
                update=True,
            )
        return redirect(url_for(str(TagId()), tag_id=tag_id))

    @login_required
    @login_as_admin_required
    def delete(self, tag_id):
        app.logger.info(f"Deleting {self.blp.name} #{tag_id}.")
        tag = tag_service.delete(tag_id)
        if not tag:
            abort(404)
        return redirect(url_for(str(Tags()))), 303
