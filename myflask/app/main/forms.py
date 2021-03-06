#coding=utf-8
from flask_wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField,SelectMultipleField,FieldList,FormField,RadioField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User


class NameForm(Form):
    name = StringField(u'您的姓名', validators=[Required()])
    submit = SubmitField(u'提交')


class EditProfileForm(Form):
    name = StringField(u'真实姓名', validators=[Length(0, 64)])
    signature = StringField(u'个性签名', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关于我')
    submit = SubmitField(u'提交')


class EditProfileAdminForm(Form):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField(u'用户名', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField(u'验证')
    role = SelectField(u'权限', coerce=int)
    name = StringField(u'真实姓名', validators=[Length(0, 64)])
    signature = StringField(u'个性签名', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关于我')
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError(u'这个邮箱已经被注册！')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError(u'这个用户名已经被使用！')


class SubToAddForm(Form):
    submit = SubmitField(u'添加投票')

class EditItemForm(Form):
    subject = StringField('Subject', validators=[Length(0, 64)])
    body = TextAreaField('Introduction')
    submit = SubmitField('Edit Item')


class CommentForm(Form):
    body = StringField(u'请输入评论内容', validators=[Required()])
    submit = SubmitField(u'提交')
