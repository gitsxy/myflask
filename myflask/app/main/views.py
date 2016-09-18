#coding=utf-8
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, CommentForm,SubToAddForm,EditItemForm
from .. import db
from ..models import Permission, Role, User, Item, Comment,Option
from ..decorators import admin_required, permission_required


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    #form = SubToAddForm()
    if request.method == 'POST':#form.validate_on_submit():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.can(Permission.WRITE_ARTICLES):
            return redirect(url_for('.add_item'))
    page = request.args.get('page', 1, type=int)
   
    query = Item.query
    pagination = query.order_by(Item.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    items = pagination.items
    return render_template('index.html',  items=items, pagination=pagination)
#    return render_template('index.html')

@main.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        subject = request.form.get('subject')
        introduction = request.form.get('introduction')
        single = True
        if request.form.get('optionsRadios') == 'multi':
            single = False
        item = Item(subject=subject,body=introduction,single=single,author=current_user._get_current_object())
        db.session.add(item)
        for i in range(10) :
            s = "%s%d"%('option',i)
            txt = request.form.get(s)
            if txt is not None and txt != '':
                option = Option(description=txt,item=item)
                db.session.add(option)
        return render_template('addok.html')
    return render_template('add_item.html')


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.items.order_by(Item.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    items = pagination.items
    return render_template('user.html', user=user, items=items,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.signature = form.signature.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(u'您的资料已更新！')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.signature.data = current_user.signature
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.signature = form.signature.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.signature.data = user.signature
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/item/<int:id>', methods=['GET', 'POST'])
def item(id):
    form = CommentForm()
    item = Item.query.get_or_404(id)
    if current_user.is_authenticated and current_user.has_voted(item):
        options = item.options.order_by(Option.vote.desc())
    else:options = item.options.order_by(Option.id.asc())
    if form.validate_on_submit() and current_user.has_voted(item):
        comment = Comment(body=form.body.data,item=item,
                          author=current_user._get_current_object())
        db.session.add(comment)
        return redirect(url_for('.item', id=item.id, page=-1))
    
    if request.method == 'POST' and not current_user.has_voted(item):
        if item.single is True:
            op = request.form.get('optionsRadios')
            num = int(op[6])
            options[num].inc_vote_num(1)
        else:
            for i in range(len(list(options))):
                status = request.form.get("%s%d"%('option',i))
                if status == 'on': 
                    options[i].inc_vote_num(1)
        current_user.vote(item)
        return redirect(url_for('.item', id=item.id))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (item.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination_comments = item.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination_comments.items
    return render_template('item.html', item=item, form=form,
                           comments=comments,options=options,
                           pagination_comments=pagination_comments)


@main.route('/del/<int:id>', methods=['GET', 'POST'])
@login_required
def del_item(id):
    item = Item.query.get_or_404(id)
    if current_user != item.author and not current_user.can(Permission.ADMINISTER):
        flash('You have no permission!')
    comments = item.comments
    for comment in comments:
        db.session.delete(comment)
    options = item.options
    for  option in options:
        db.session.delete(option)
    
    db.session.delete(item)
    flash('The item has been deleted.')
    return redirect(url_for('.index'))



@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

