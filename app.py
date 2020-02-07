from flask import Flask, render_template, url_for, request, redirect, session, g
import config
from exts import db
from models import *
import functools
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)


def login_required(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        author_id = session.get('author_id')
        if not author_id:
            return redirect(url_for('login'))
        else:
            g.author_id = author_id
            return func(*args, **kwargs)

    return inner


@app.route('/')
def index():
    context = {
        'questions': Question.query.order_by(Question.id.desc()).all()
    }
    return render_template('index.html', **context)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        telephone = request.form.get('telephone').strip()
        password = request.form.get('password').strip()

        if not telephone:
            return '手机号码不能为空'
        elif not password:
            return '密码不能为空'
        else:
            author = Author.query.filter(Author.telephone == telephone).first()
            if author and author.check_password(password):
                session['author_id'] = author.id
                return redirect(url_for('index'))
            else:
                return '用户名或密码错误'


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        telephone = request.form.get('telephone').strip()
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        if not telephone:
            return '手机号码不能为空'
        elif not username:
            return '用户名不能为空'
        elif not password:
            return '密码不能为空'
        elif not confirm_password:
            return '确认密码不能为空'
        elif password != confirm_password:
            return '两次输入密码不一致'
        else:
            exist = Author.query.filter(Author.telephone == telephone).first()
            if exist:
                return '用户已经存在'
            else:
                author = Author(telephone=telephone, username=username, password=password)
                db.session.add(author)
                db.session.commit()
                return redirect(url_for('login'))


@app.route('/logout/')
def logout():
    if session.get('author_id'):
        session.pop('author_id')

    return render_template('login.html')


@app.route('/question/', methods=['GET', 'POST'])
@login_required
def question():
    if request.method == 'GET':
        return render_template('question.html')
    else:
        title = request.form.get('title').strip()
        content = request.form.get('content').strip()

        if not title:
            return '标题不能为空'
        elif len(title) > 100:
            return '标题长度不能大于100'
        elif not content:
            return '问题内容不能为空'
        else:
            author_id = session.get('author_id')
            ques = Question(title=title, content=content, author_id=author_id)
            db.session.add(ques)
            db.session.commit()
            return redirect(url_for('index'))


@app.route('/qd/<question_id>/')
def question_detail(question_id):
    ques = Question.query.filter(Question.id == question_id).first()
    print(ques.comments.count)
    return render_template('question_detail.html', question=ques)


@app.route('/ac/<question_id>', methods=['POST'])
@login_required
def add_comment(question_id):
    content = request.form.get('add_comment').strip()
    if content:
        if question_id:
            comment = Comment(content=content, question_id=question_id, author_id=g.author_id)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('question_detail', question_id=question_id))
        else:
            return '问题编号不能我空'
    else:
        return '评论内容不能为空'


@app.route('/s/')
def search():
    q = request.args.get('q').strip()
    if q:
        questions = Question.query.filter(or_(Question.title.contains(q), Question.content.contains(q)))\
            .order_by(Question.id.desc()).all()
        return render_template('index.html', questions=questions)
    else:
        return redirect(url_for('index'))


@app.context_processor
def my_context_processor():
    author_id = session.get('author_id')
    if author_id:
        author = Author.query.filter(Author.id == author_id).first()
        if author:
            return {'author': author}

    return {}


if __name__ == '__main__':
    app.run()
