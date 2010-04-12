import datetime
import hashlib
import os
import random
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

# 発言者モデル
class Author(db.Model):
  name = db.StringProperty(required=True)
  description = db.StringProperty()
  date_on = db.DateTimeProperty(auto_now_add=True)

# 名言モデル
class Meigen(db.Model):
  text = db.StringProperty(required=True)
  date_on = db.DateTimeProperty(auto_now_add=True)
  author = db.ReferenceProperty(Author)

# メール送信宛先モデル
class Mail(db.Model):
  mailaddress = db.StringProperty(required=True)
  nickname = db.StringProperty()
  date_on = db.DateTimeProperty(auto_now_add=True)

# インデックスページを表示します
CONTENT_TYPE = 'text/html; charset=utf-8'
INDEX_HTML = 'index.html'
REGISTER_HTML = 'register.html'
ERROR_MSG = '発言者と名言は両方入力してくださいね。'
class MainHandler(webapp.RequestHandler):
  def get(self):
    path = os.path.join( os.path.dirname(__file__), INDEX_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, {'authors': Author.all(), 'meigens': Meigen.all()}) )

  def post(self):
    # パラメータ取得
    author_value = self.request.get("author")
    text_value = self.request.get("text")
    template_value = {'name': author_value, 'text': text_value}

    # テンプレート、出力設定
    path = os.path.join( os.path.dirname(__file__), REGISTER_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE

    # パラメタが不正なときは一覧画面へリダイレクトする
    if (author_value == '' or text_value == ''):
      self.redirect("/")
      return

    # 発言者登録
    author_obj = Author.get_or_insert( author_value, name=author_value)
    meigen_obj = Meigen.get_or_insert( text_value, text=text_value, author=author_obj)

    # 一覧ページへリダイレクトする
    self.redirect("/")

# 発言者を管理します
AUTHOR_HTML = 'author.html'
class AuthorListHandler(webapp.RequestHandler):
  # 発言者一覧ページを表示します
  def get(self):
    path = os.path.join( os.path.dirname(__file__), AUTHOR_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, {'authors': Author.all()}) )

  # 発言者を登録します
  def post(self):
    author_name = self.request.get('name')
    author_description = self.request.get('name')
    # 入力が無ければ発言者一覧へリダイレクトする
    if (not author_name):
    	self.redirect('/author/')

    # 発言者が登録します
    author_obj = Author.get_or_insert( author_name, name=author_name, description=author_description)

    path = os.path.join( os.path.dirname(__file__), AUTHOR_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, {'authors': Author.all()}) )

# 発言者を削除します
class AuthorDeleteHandler(webapp.RequestHandler):
  def post(self):
    template_value = {'message': '', 'authors': ''}

    # 削除対象の発言者idsを取得する
    author_ids = self.request.get("author_id", allow_multiple=True)
    for author_id in author_ids:
      # 発言者の登録有無を確認
      author = Author.get( author_id )
      if (not author):
        break

      # 発言者が名言を所持していなければ削除する
      meigens = Meigen.all()
      meigens_of_author = meigens.filter('author =', author)
      if (0 == meigens_of_author.count()):
        template_value['message'] += 'deleted : ' + author.name + '<br/>'
        db.delete( author )
      else:
        template_value['message'] += "can't delete : " + author.name + '. because meigen exists!<br/>'

    # 発言者一覧を取得する
    template_value['authors'] = Author.all()

    # 発言者一覧画面を表示する
    path = os.path.join( os.path.dirname(__file__), AUTHOR_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, template_value) )

# 名言を削除します
RESULT_HTML = 'result.html'
class DeleteHandler(webapp.RequestHandler):
  def post(self):
    path = os.path.join( os.path.dirname(__file__), RESULT_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE

    # 指定数分削除処理を実行する
    template_value = {'message': ''}
    meigen_ids = self.request.get("meigen_id", allow_multiple=True)
    for meigen_id in meigen_ids:
      # 名言登録確認
      meigen = Meigen.get( meigen_id )
      if (not meigen):
        break

      # 名言削除
      meigen_author = meigen.author
      template_value['message'] += 'delete : ' + meigen.text + ' by ' + meigen.author.name + '<br/>'
      meigen.delete()

      # 発言者の名言が 0 の場合は、発言者も削除する
      meigens = Meigen.all()
      meigens_of_author = meigens.filter('author =', meigen_author)
      if (0 == meigens_of_author.count()):
        author = Author.all()
        author.filter('name=', meigen_author.name)
        db.delete( author )

    # 一覧画面へリダイレクトする
    self.response.out.write( template.render(path, template_value) )

# メールの送信先を管理します
MAIL_HTML = 'mail.html'
class MailaddressHandler(webapp.RequestHandler):
  def get(self):
    path = os.path.join( os.path.dirname(__file__), MAIL_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, {'mails': Mail.all()}) )

  # 送信先を登録します
  def post(self):
    mailaddress = self.request.get('mailaddress')
    nickname = self.request.get('nickname')

    # 入力が無ければ送信先一覧へリダイレクトする
    if (not mailaddress):
    	self.redirect('/mail/')

    # 送信先を登録します
    mail_obj = Mail.get_or_insert( mailaddress, mailaddress=mailaddress, nickname=nickname)

    path = os.path.join( os.path.dirname(__file__), MAIL_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, {'mails': Mail.all()}) )

# 送信先を削除します
class MailaddressDeleteHandler(webapp.RequestHandler):
  def post(self):
    # 指定数分削除処理を実行する
    template_value = {'message': ''}
    mail_ids = self.request.get('mail_id', allow_multiple=True)
    for mail_id in mail_ids:
      # 名言登録確認
      mail = Mail.get( mail_id )
      if (not mail):
        break

      # 送信先削除
      template_value['message'] += 'delete : ' + mail.nickname + ' &lt;' + mail.mailaddress + '&gt;<br/>'
      mail.delete()

    # 送信先一覧画面を表示する
    path = os.path.join( os.path.dirname(__file__), MAIL_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, template_value) )

# メールを送信します
FROM_ADDRESS = 'sadao.oyama@gmail.com'
class SendMailHandler(webapp.RequestHandler):
  def get(self):
    path = os.path.join( os.path.dirname(__file__), RESULT_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE

    # 送信先が無ければ終了
    mails = Mail.all()
    if (0 == mails.count()):
      self.response.out.write( template.render(path, {'message': '送信先が登録されていません。'}) )
      return

    # データをランダムに取得する
    meigens = Meigen.all()
    if (0 == meigens.count()):
      self.response.out.write( template.render(path, {'message': '名言が登録されていません。'}) )
      return

    meigen_number = random.randint(1, meigens.count())
    meigen = meigens.fetch( 1, offset=(meigen_number - 1) )

    # 送信宛先分処理する
    for mail_obj in mails:
      # メール送信
      message = mail.EmailMessage(sender  = FROM_ADDRESS,
                                  to      = mail_obj.nickname + ' <' + mail_obj.mailaddress + '>',
                                  subject = "今日の言葉")
      message.body = meigen[0].text
      message.send()

    # 出力
    path = os.path.join( os.path.dirname(__file__), RESULT_HTML )
    self.response.headers['Content-Type'] = CONTENT_TYPE
    self.response.out.write( template.render(path, {'message': 'メールを送りました！'}) )

# webapp フレームワークのURLマッピングです
application = webapp.WSGIApplication(
                                     [
                                       ('/', MainHandler),
                                       ('/author/', AuthorListHandler),
                                       ('/author/delete/', AuthorDeleteHandler),
                                       ('/delete/', DeleteHandler),
                                       ('/mail/', MailaddressHandler),
                                       ('/mail/delete/', MailaddressDeleteHandler),
                                       ('/mail/send/', SendMailHandler)
                                     ],
                                     debug=True)

# WebApp フレームワークのメインメソッドです
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()