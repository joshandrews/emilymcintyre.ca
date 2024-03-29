#!/usr/bin/env python

import web
import blog
import user
import hashlib
import os
import shutil
import htmltruncate
import re
import config
import MySQLdb
import random
import string
import espresso
import install
import markdown
import sys
import blogutils
from PIL import Image

### Url mappings

web.config.debug = False

urls = (
    '/', 'Index',
    '/login', 'Login',
    '/logout', "Logout",
    '/work', 'Work',
    '/americano', 'Americano',
    '/blog', 'Blog',
    '/blog/(\d+)/(.*)', 'BlogPost',
    '/blog/new', 'New',
    '/blog/delete/(\d+)', 'Delete',
    '/blog/edit/(\d+)', 'Edit',
    '/blog/edit/clear-image/(\d+)', "ClearImage",
    '/work/(.*)', "WorkPage",
    '/install', 'Install',
    '/favicon.ico', "Favicon",
    '/upload/post-image/(\d+)', "Upload",
    '/blog/edit/live-save-body/(\d+)/(\d+)', "LiveSaveBody",
    '/blog/edit/live-save-title/(\d+)/(\d+)', "LiveSaveTitle",
    '/install/step/(\d+)', "InstallSubmit",
    '/settings', "Settings",
    '/settings-auth', "SettingsAuth",
    '/trash', 'Trash',
    '/blog/put-back/(\d+)', 'PutBack',
    '/trash/empty', 'EmptyTrash'
)


app = web.application(urls, globals())

### Authentication
store = web.session.DiskStore('sessions')
session = web.session.Session(app, store, initializer={'login': 0, 'privilege': 0})


class Auth:
    def __init__(self):
        self.val = False
        self.onpage = False

auth = Auth()

### Templates
t_globals = {
    'datestr': web.datestr,
    'url': blogutils.title_to_url,
}
render = web.template.render('templates/common', cache=blog.cache, globals=t_globals)
def check_installed():
    con = config.Config()
    if int(con.ConfigSectionMap("Info")["installed"]) is not 3:
        raise web.seeother('/install')

def gen_head():
    if session.login==1:
        if session.privilege == 2:
            render = web.template.render('templates/admin', globals=t_globals)
            return render.header()
        else:
            render = web.template.render('templates/common', globals=t_globals)
            return render.header()
    else:
        render = web.template.render('templates/common', globals=t_globals)
        return render.header()

def gen_offleft():
    if session.login==1:
        if session.privilege == 2:
            render = web.template.render('templates/admin', globals=t_globals)
            return render.offleft()
        else:
            render = web.template.render('templates/common', globals=t_globals)
            return render.offleft()
    else:
        render = web.template.render('templates/common', globals=t_globals)
        return render.offleft()

class Favicon:
    def GET(self):
        f = open("static/images/favicon.ico", 'rb')
        return f.read()

class WorkPage:
     def GET(self, page):
        check_installed()
        workpage = web.template.frender('templates/common/work-pages/'+page+".html")
        return workpage(gen_head(), gen_offleft())

class Upload:
    def POST(self, id):
        size = 128, 128
        x = web.input(myfile={})
        filedir = 'static/images/uploads/'+id+"/" # change this to the directory you want to store the file in.

        if 'myfile' in x: # to check if the file-object is created
            filepath=x.myfile.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
            filename=filepath.split('/')[-1] # splits the and chooses the last part (the filename with extension)

            if os.path.exists(filedir):
                shutil.rmtree(filedir)

            os.makedirs(filedir)

            fout = open(filedir + filename,'w') # creates the file where the uploaded file should be stored
            fout.write(x.myfile.file.read()) # writes the uploaded file to the newly created file.
            fout.close() # closes the file, upload complete.

            size = 512, 512

            im = Image.open(filedir + filename)
            im.thumbnail(size)
            im.save(filedir + filename.split(',')[0]+"-thumb.jpg")
            blog.update_thumb_for_post(id, "/"+filedir + filename.split(',')[0]+"-thumb.jpg")


class Login:

    def GET(self):
        check_installed()
        if user.logged(session):
            render = user.create_render(session)
            raise web.seeother('/americano')
        else:
            render = user.create_render(session)
            return '%s' % render.login(gen_head(), gen_offleft())

    def POST(self):
        username, passwd = web.input().user, web.input().passwd
        ident = blog.get_user()[0]
        if hashlib.sha1(ident['salt']+passwd).hexdigest() == ident['passwd']:
            session.login = 1
            session.privilege = ident['privilege']
            render = user.create_render(session)
            raise web.seeother('/americano')
        else:
            session.login = 0
            session.privilege = 0
            render = user.create_render(session)
            return render.login_error()

class SettingsAuth:
    def GET(self):
        auth.val = False
        auth.onpage = False
        check_installed()
        if user.logged(session):
            settingsAuth = web.template.frender("templates/admin/settings-auth.html")
            return settingsAuth(gen_head(), gen_offleft())
        else:
            raise web.seeother('/login')

    def POST(self):
        password = web.input().password
        ident = blog.get_user()[0]
        if hashlib.sha1(ident['salt']+password).hexdigest() == ident['passwd']:
            auth.val = True
            raise web.seeother('/settings')
        else:
            auth.val = False
            raise web.seeother('/settings-auth')

class Settings:
    def GET(self):
        check_installed()
        if not auth.val:
            raise web.seeother('/settings-auth')

        if user.logged(session):
            auth.val = False
            auth.onpage = True
            ident = blog.get_user()[0]
            con = config.Config()
            render = user.create_render(session)
            return render.settings(gen_head(), gen_offleft(), con.ConfigSectionMap("Info")["name"], ident['user'],
                                   ident['email'], con.ConfigSectionMap("Preferences")["indexbackgroundurl"])
        else:
            raise web.seeother('/login')

    def POST(self):
        print auth.onpage
        if auth.onpage:
            con = config.Config()
            new_name = web.input().name
            new_username = web.input().username
            new_password = web.input().password
            new_email = web.input().email
            new_url = web.input().hpImageURL
            ident = blog.get_user()[0]
            old_password = ident['passwd']
            old_name = con.ConfigSectionMap("Info")["name"]
            old_url = con.ConfigSectionMap("Preferences")["indexbackgroundurl"]
            hash_password = hashlib.sha1(ident['salt']+new_password).hexdigest()
            if hash_password is not ident['passwd'] and str(new_password) is not "" and new_password is not None:
                old_password = hash_password

            blog.update_user(new_username, old_password, new_email)

            if new_name is not old_name:
                con.setName(new_name)
                espresso.generateHeader(new_name)
            if new_url is not old_url:
                con.setIndexBackgroundUrl(new_url)

            raise web.seeother('/americano')
        else:
            raise web.seeother('/settings-auth')



class Install:
    def GET(self):
        con = config.Config()
        if int(con.ConfigSectionMap("Info")["installed"]) is not 3:
            render = web.template.render('templates/common', globals=t_globals)
            return render.install(con.ConfigSectionMap("Info")["installed"])
        else:
            raise web.seeother('/')

class InstallSubmit:
    def POST(self, step):
        con = config.Config()
        if int(con.ConfigSectionMap("Info")["installed"]) is not 3:
            if int(step) is 1:
                name = web.input().name
                username = web.input().username
                password = web.input().password
                con.setName(name)
                genpass = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(8))
                con.setMySQLPassword(genpass)
                con.setMySQLUsername("americano")
                con.setMySQLDatabase("americano")
                create_americano_database(username, password, genpass)
                con.setInstalled("2")
                espresso.generateHeader(name)
            if int(step) is 2:
                username = web.input().username
                password = web.input().password
                email = web.input().email
                blog.generateUser(username, password, email)
                con.setInstalled("3")


class Americano:
    
    def GET(self):
        check_installed()
        if user.logged(session):
            published_posts = blog.get_published_posts()
            unpublished_posts = blog.get_unpublished_posts()
            render = user.create_render(session)
            return render.americano(gen_head(), gen_offleft(), published_posts, unpublished_posts, htmltruncate)
        else:
            raise web.seeother('/login')

class Logout:

    def GET(self):
        check_installed()
        session.login = 0
        session.kill()
        raise web.seeother('/blog')


class Index:
    def GET(self):
        con = config.Config()
        check_installed()
        render = web.template.render('templates/common', globals=t_globals)
        return render.index(gen_head(), gen_offleft(), con.ConfigSectionMap("Preferences")["indexbackgroundurl"])


class Blog:

    def GET(self):
        check_installed()
        posts = blog.get_published_posts()
        render = web.template.render('templates/common', globals=t_globals)
        return render.blog(gen_head(), gen_offleft(), posts)


class BlogPost:

    def GET(self, id, name):
        check_installed()
        post = blog.get_post(int(id))
        idname = blogutils.title_to_url(post.title)
        if idname != name:
            web.seeother("/blog/"+id+"/"+idname)
        render = web.template.render('templates/common', globals=t_globals)
        filedir = 'static/images/uploads/'+id+"/" # change this to the directory you want to store the file in.
        heroURL = ''
        if os.path.exists(filedir):
            for file in os.listdir(filedir):
                if (file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".gif") or file.endswith(".png")) and not "thumb" in file:
                    heroURL = "/"+filedir+file
                    break
        if post.published == 0:
            if user.logged(session):
                if session.privilege == 2:
                    if heroURL == '':
                        return render.blogpostsimple(gen_head(), gen_offleft(), post)
                    else:
                        return render.blogpost(gen_head(), gen_offleft(), post, heroURL)
        else:
            if heroURL == '':
                return render.blogpostsimple(gen_head(), gen_offleft(), post)
            else:
                return render.blogpost(gen_head(), gen_offleft(), post, heroURL)


class New:

    def POST(self):
        title, body, published = web.input().title, web.input().body, int(web.input().published)
        if user.logged(session):
            if session.privilege == 2:
                if title == "" or body == "":
                    render = user.create_render(session)
                    return render.new(gen_head(), gen_offleft())
                blog.new_post(title, body, published)
        if published == 1:
            raise web.seeother('/blog')
        else:
            raise web.seeother('/americano')


class Delete:

    def POST(self, id):
        self.do_delete(id)

    def GET(self, id):
        self.do_delete(id)

    def do_delete(self, id):
        if user.logged(session):
            if session.privilege == 2:
                blog.throw_away(int(id))
                ClearImage.POST(ClearImage(), int(id))
        raise web.seeother('/americano')


class PutBack:
    def POST(self, id):
        if user.logged(session):
            if session.privilege == 2:
                blog.put_back(int(id))
        raise web.seeother('/trash')

class ClearImage:
    def POST(self, id):
        if user.logged(session):
            if session.privilege == 2:
                filedir = 'static/images/uploads/'+str(id)+"/" # change this to the directory you want to store the file in.
                blog.update_thumb_for_post(id, None)

                if os.path.exists(filedir):
                    shutil.rmtree(filedir)

class Work:

    def GET(self):
        check_installed()
        render = web.template.render('templates/common', globals=t_globals)
        return render.work(gen_head(), gen_offleft())


class Edit:

    def GET(self, id):
        check_installed()
        post = blog.get_post(int(id))
        if post is None:
            post_id = blog.new_post("", 0)
            raise web.seeother("/blog/edit/"+str(post_id))
        render = user.create_render(session)
        return render.edit(gen_head(), gen_offleft(), post, post.markdown)


    def POST(self, id):
        title, body, published = web.input().title, web.input().body, int(web.input().published)
        if user.logged(session):
            if session.privilege == 2:
                post = blog.get_post(int(id))
                if re.sub('<[^<]+?>', '', title) == "" or body == "" or title is None or body is None:
                    Delete.POST(self, int(id))
                else:
                    update_blog_post_in_correct_format(id, title, body, published)
        if published == 1:
            raise web.seeother('/blog')
        else:
            raise web.seeother('/americano')

class Trash:
    def GET(self):
        check_installed()
        if user.logged(session):
            trashed_posts = blog.get_trashed_posts()
            render = user.create_render(session)
            return render.trash(gen_head(), gen_offleft(), trashed_posts, htmltruncate)
        else:
            raise web.seeother('/login')

class EmptyTrash:

    def POST(self):
        check_installed()
        if user.logged(session):
            blog.empty_trash()
            raise web.seeother('/trash')
        else:
            raise web.seeother('/login')

class LiveSaveBody:
    def POST(self, id, published):
        body = web.input().textarea
        update_blog_post_in_correct_format(id, None, body, published)

class LiveSaveTitle:
    def POST(self, id, published):
        title = web.input().title
        blog.update_post_title(int(id), title)

def create_americano_database(user, password, genpass):
    dbs = MySQLdb.connect(user=user, passwd=password)
    cur = dbs.cursor()
    cur.execute('CREATE DATABASE americano;')
    db = MySQLdb.connect(host="localhost", user=user, passwd=password, db="americano")
    cur = db.cursor()
    cur.execute("GRANT ALL PRIVILEGES ON americano.* To 'americano'@'localhost' IDENTIFIED BY '"+genpass+"';")
    cur.execute("FLUSH PRIVILEGES;")
    for line in open('schema.sql','r'):
        cur.execute(line)

def update_blog_post_in_correct_format(id, title, body, published):
    if "<code>" in body and "</code>" in body:
        # Need to render the code block in safe mode
        start = re.search('(.*?)<code>', body, re.DOTALL)
        if start:
            start = start.group(1)
        else:
            start = ""
        codeBlock = re.search('<code>(.*?)</code>', body, re.DOTALL)
        if codeBlock:
            codeBlock = codeBlock.group(1)
        else:
            codeBlock = ""
        end = re.search('</code>(.*)', body, re.DOTALL)
        if end:
            end = end.group(1).replace('<code>', "").replace("</code>", "")
        else:
            end = ""
        markedStart = markdown.markdown(start.replace('%2b', '+'))
        md = markdown.Markdown(safe_mode='escape')
        markedCodeBlock = md.convert(codeBlock.replace('%2b', '+'))
        markedEnd = markdown.markdown(end.replace('%2b', '+'))
        if title != None:
            blog.update_post(int(id), title, body.replace('%2b', '+'), markedStart+"<code>"+markedCodeBlock+"</code>"+markedEnd, published)
        else:
            blog.update_post_body(int(id), body.replace('%2b', '+'), markedStart+"<code>"+markedCodeBlock+"</code>"+markedEnd, published)
    else:
        if title != None:
            blog.update_post(int(id), title, body.replace('%2b', '+'), markdown.markdown(body.replace('%2b', '+')), published)
        else:
            blog.update_post_body(int(id), body.replace('%2b', '+'), markdown.markdown(body.replace('%2b', '+')), published)


if __name__ == '__main__':
    if not len(sys.argv) is 3:
        web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    elif sys.argv[2] == "--dev" or sys.argv[2] == "--d" or sys.argv[2] == "-d":
        print "Starting americano on port "+sys.argv[1]+" in development mode"
    else:
        print "Invalid argument"
    app.run()