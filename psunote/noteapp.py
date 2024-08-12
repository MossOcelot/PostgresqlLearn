import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>", methods=["POST", "GET"])
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()


    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

@app.route("/tags/<tag_name>/delete", methods=["POST", "GET"])
def delete_tag(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    
    if tag:
        notes_to_delete = db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag.id))
        ).scalars().all()

        for note in notes_to_delete:
            db.session.delete(note)

        
        db.session.delete(tag)
        db.session.commit()
        flask.flash(f"Tag '{tag_name}' has been deleted.", "success")
    else:
        flask.flash(f"Tag '{tag_name}' not found.", "danger")
    return flask.redirect(flask.url_for("index"))

@app.route("/tags/<tag_name>/delete_note/<int:note_name>", methods=["POST", "GET"])
def delete_note(tag_name, note_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_name)
    ).scalars().first()

    print(note)
    
    db.session.delete(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route("/tags/<tag_name>/edit", methods=["GET", "POST"])
def edit_tag(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    
    if not tag:
        flask.flash(f"Tag '{tag_name}' not found.", "danger")
        return flask.redirect(flask.url_for("index"))

    if flask.request.method == "POST":
        new_tag_name = flask.request.form.get("tag_name")
        if new_tag_name:
            existing_tag = (
                db.session.execute(db.select(models.Tag).where(models.Tag.name == new_tag_name))
                .scalars()
                .first()
            )
            if existing_tag:
                flask.flash(f"Tag '{new_tag_name}' already exists.", "danger")
            else:
                tag.name = new_tag_name
                db.session.commit()
                flask.flash(f"Tag name changed to '{new_tag_name}'.", "success")
                return flask.redirect(flask.url_for("tags_view", tag_name=new_tag_name))

    return flask.render_template(
        "edit-tag.html",
        tag=tag,
    )

@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def edit_note(note_id):
    db = models.db
    note = (
        db.session.execute(db.select(models.Note).where(models.Note.id == note_id))
        .scalars()
        .first()
    )
    
    if not note:
        flask.flash(f"Note with ID {note_id} not found.", "danger")
        return flask.redirect(flask.url_for("index"))

    form = forms.NoteForm2(obj=note)  # ตรวจสอบว่ามีการสร้างฟอร์ม
    print(form.validate_on_submit())
    if form.validate_on_submit():
        # Update only note's title and description
        print("Check:", note)
        form.populate_obj(note)
        db.session.commit()
        flask.flash("Note updated successfully.", "success")
        return flask.redirect(flask.url_for("index"))

    return flask.render_template(
        "notes-edit.html",
        form=form,  # ตรวจสอบว่ามีการส่งฟอร์ม
        note=note,
    )


if __name__ == "__main__":
    app.run(debug=True)
