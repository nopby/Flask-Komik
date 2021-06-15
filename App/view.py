from App import db
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from flask import abort
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user
from flask_login import current_user
import zipfile 
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from .model import Users 
from .model import Profiles
from .model import Manga
from .model import Chapter
from .model import ImageSet
from .model import Report
import os
import pathlib
import shutil


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

#Directory 
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '\\static\\upload\\'
TRASH_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '\\static\\trash\\'
MANGA_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '\\static\\upload\\manga\\'


#Our views
views = Blueprint("views", __name__, static_folder="static", template_folder="Templates")

#For flash pop and 2 form in auth page
flag = False
log = False


#Home page
@views.route('/', methods=['POST', 'GET'], defaults={'page' : 1})
@views.route('/<int:page>', methods=['POST', 'GET'])
def home(page):
    #20 manga per page
    per_page = 20

    #Do nothing
    if request.method == 'GET':
        manga = Manga.query.order_by(
            Manga.added_at.desc()).paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
    #Do search
    else:
        search = request.form.get('search')
        title = "%{}%".format(search)
        manga = Manga.query.filter(Manga.title.like(title)).paginate(per_page=per_page, error_out=False)

    #Active navbar
    active = 'Home'
    
    #If login
    if current_user.is_authenticated:
        user = Users.query.filter_by(id=current_user.id).first()
        profile = user.profile.first()

        user.Active(1)
        title = 'Manga Online - User'

        return render_template(
                'home/index.html', 
                title=title, 
                active=active, 
                manga=manga,
                user=user,
                profile=profile
            )
            
    #If not
    else:
        title = 'Manga Online - Read Manga Online For Free'
        return render_template("home/index.html", title=title, page=page, active=active, user=None, manga=manga)



#Sign in and sign up page
@views.route('/auth')
def auth():
    title = 'Manga Online - Sign In For Download Manga'
    active = 'Auth'
    user = None
    return render_template('auth/auth.html', title=title, active=active, user=user, log=log)

#Sign up method
@views.route('/Register', methods=['POST'])
def Register():
    global log
    if request.form:

        #Get form
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_repeat = request.form.get('password_repeat')

        #Default user condition
        level = 2
        active = 0

        #Form sign up flag
        log=False

        #Form validation
        email_validation = Users.query.filter_by(email=email).first()
        username_validation = Users.query.filter_by(username=username).first()
        if username_validation:
            flash('Username already used', category='error')
        elif len(username) < 3:
            flash('Username must be at least 4 characters long', category='error')
        elif email_validation:
            flash('Email already used', category='error')
        elif len(email) < 4:
            flash('Email must be at least 5 characters long', category='error')
        elif password != password_repeat:
            flash('Password does not match.', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', category='error')
        else:
            #Make our record
            profile = Profiles(name=username, picture='default.png')
            user = Users(username=username, email=email, password=generate_password_hash(password, method='sha256'), level=level, active=active)
            user.Create(profile)
            flash('Your account has been successfully created', category='success')

    return redirect(url_for('views.auth'))

#Sign in method
@views.route('/Login', methods=['POST'])
def Login():
    global log
    if request.form:
        #Form sign in flag
        log=True

        #Get our form
        username = request.form.get('username')
        password = request.form.get('password')

        #Form validation
        users = Users.query.filter_by(username=username).first()
        if request.form.get('remember-me') == 'on':
            remember=True
        else:
            remember=False
        if len(username) < 3:
            flash('Email must be at least 4 characters long', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', category='error')
        else:
            if users:
                if check_password_hash(users.password, password):
                    #Sign in
                    login_user(users, remember=remember)
                    return redirect(url_for('views.home'))
                else:
                    flash('Wrong password', category='error')
            else:
                flash('Wrong username', category='error')
        return redirect(url_for('views.auth'))

#Sign out method
@views.route('/Logout')
@login_required
def Logout():
    #Get current user
    user = Users.query.filter_by(id=current_user.id).first()

    #Set off condition
    #user.active = 0
    #Update DB and sign out
    user.Active(0)
    logout_user()

    return redirect(url_for('views.auth'))


#User Profile
@views.route('/Profile')
@login_required
def Profile():
    user = Users.query.filter_by(id=current_user.id).first()
    profile = user.profile.first()
    return render_template('profile/profile.html', user=user, flag=flag, profile=profile)

#User List
@views.route('/ManageUser', methods=['POST', 'GET'], defaults={'user_page' : 1})
@views.route('/ManageUser/<int:user_page>', methods=['POST', 'GET'])
@login_required
def ManageUser(user_page):
    users = Users.query.order_by(Users.last_active.desc()).paginate(page=user_page, per_page=10, error_out=False)
    
    user = Users.query.filter_by(id=current_user.id).first()
    if user.level == 1:
        profile = user.profile.first()
        return render_template(
            'admin/manageusers.html', 
            title="Manga Online - Admin", 
            active='Admin',
            user=user, 
            profile=profile, 
            users=users
            )
    else:
        return redirect('views.home')

#Delete User
@views.route('/DeleteUser', methods=['POST', 'GET']) 
@login_required
def DeleteUser():
    user = Users.query.filter_by(id=current_user.id).first()
    if user.level == 1:
        if request.method == 'POST':
            profile = user.profile.first()
            user_id = request.form.get('user_id')
            delete_user = db.session.query(Users).filter(Users.id==user_id).first()
            db.session.delete(delete_user)
            db.session.commit()
            flash('User deleted', category='error')
        return redirect(url_for('views.ManageUser'))
    else:
        return redirect(url_for('views.home'))

#Update User
@views.route('/UpdateUser', methods=['POST'])
@login_required
def UpdateUser():
    if request.form:
        print(request.form)
        id = request.form.get('id')
        level = request.form.get('level')
        user = Users.query.filter_by(id=id).first()
        user.level = level
        db.session.commit()
        flash('Data user berhasil diubah', category='success')
    return redirect(url_for('views.ManageUser'))

#User Report
@views.route('/UserReport', methods=['POST', 'GET'])
@login_required
def UserReport():
    #
    user = Users.query.filter_by(id=current_user.id).first()
    profile = user.profile.first()

    #Check request method
    if request.method == 'POST':
        #Create Report  
        text = request.form.get('text')
        report = Report(description=text)
        user.report.append(report) 
        db.session.add(report)
        db.session.commit()
        flash('Report has been send', category='success')
    return render_template('user/user.html', user=user, profile=profile)

#Admin Report
@views.route('/AdminReport', methods=['POST', 'GET'], defaults={'report_page' : 1})
@views.route('/AdminReport/<int:report_page>', methods=['POST', 'GET']) 
@login_required
def AdminReport(report_page):
    user = Users.query.filter_by(id=current_user.id).first()
    if user.level == 1:
        profile = user.profile.first()
        active = 'AdminReport'
        title = 'Manga Online - Admin Report'
        report = Report.query.order_by(Report.date.desc()).paginate(page=report_page, per_page=10, error_out=False)
        return render_template(
            'admin/report.html', 
            user=user, 
            profile=profile, 
            report=report, 
            active=active,
            title=title
            )
    else:
        abort(404)

@views.route('/DeleteReport', methods=['POST', 'GET'])
@login_required
def DeleteReport():
    user = Users.query.filter_by(id=current_user.id).first()
    id = request.form.get('id')
    report = Report.query.filter_by(id=id).first()
    db.session.delete(report)
    db.session.commit()
    return redirect(url_for('views.AdminReport'))


#Add Manga
@views.route('/AddManga', methods=['POST'])
@login_required
def AddManga():
    if current_user.level == 1:
        if request.form:
            #Get manga value
            title = request.form.get('title')
            author = request.form.get('author')
            genre = request.form.get('genre')
            status = request.form.get('status')
            description = request.form.get('description')
            thumbnail = request.files['thumbnail']
            #Check manga by title
            manga = Manga.query.filter_by(title=title).first()

            #If manga exist
            if manga:
                flash('Manga already added', category='error')
            else:
                #Make folder path for manga
                folder_path = 'upload/manga/' + title

                #Get real path for create folder
                real_path = MANGA_FOLDER + title

                #Get image name
                filename = secure_filename(thumbnail.filename)

                
                #Check format file
                if allowed_file(thumbnail.filename):
                    #Checking path
                    if not os.path.exists(real_path):
                        #Create folder
                        os.makedirs(real_path)

                    #Join folder path with image name
                    path = os.path.join(real_path, filename)

                    #Save image in manga path
                    thumbnail.save(path)
                    #Add manga to database

                    new_manga = Manga(title=title, folder_path = folder_path, author=author, genre=genre, status=status, description=description, thumbnail=filename)
                    new_manga.Create(new_manga)

                    flash('Manga added', category='success')
                else:
                    flash('Thumbnail only support JPEG JPG PNG', category='error')
                
    return redirect(url_for('views.home'))

#Delete Manga
@views.route('/DeleteManga', methods=['POST'])
@login_required
def DeleteManga():
    if request.form:
        #Get manga by id and delete
        id = request.form.get('id')
        manga = Manga.query.filter_by(id=id).first()
        if manga:
            manga.Delete(manga)

        #Get source path and destination path
        source_path = MANGA_FOLDER + manga.title
        destination_path = TRASH_FOLDER + manga.title

        #Check manga folder in trash and delete if exist
        if os.path.exists(destination_path):
            shutil.rmtree(destination_path, ignore_errors=True)

        #Change destination path to trash directory
        destination_path = TRASH_FOLDER 
        
        #Move manga if exist
        if os.path.exists(source_path):
            print(destination_path)
            shutil.move(source_path, destination_path)
        flash('Manga deleted', category='success')

    return redirect(url_for('views.home'))

#Edit Manga
@views.route('/EditManga', methods=['POST'])
@login_required
def EditManga():
    if request.form:
        print(request.form)
        #Get manga
        id = request.form.get('id')
        manga = Manga.query.filter_by(id=id).first()

        #Get old title for source path
        old_title = manga.title

        #Get new title for destination path
        new_title = request.form.get('title')
        
        check_manga = Manga.query.filter_by(title=new_title).first()
        if check_manga:
            if check_manga.title != old_title:
                flash('Manga already available', category='error')
                return redirect(url_for('views.home'))
            

        #Get other value
        manga.title = new_title
        manga.author = request.form.get('author')
        manga.genre = request.form.get('genre')
        manga.status = request.form.get('status')
        manga.description = request.form.get('description')
        manga.folder_path = 'upload/manga/' + new_title

        #Make source and destination path to rename folder
        source_path = MANGA_FOLDER + old_title
        destination_path = MANGA_FOLDER + new_title
         
        #Rename folder if exist
        if os.path.exists(source_path):
            os.rename(source_path, destination_path)
            thumbnail = request.files['thumbnail']
            #Change image name if request value not null
            filename = request.files['thumbnail'].filename
            if filename != '':
                path = os.path.join(destination_path, filename)
                #Check format
                if allowed_file(thumbnail.filename):
                    #Check path
                    if os.path.exists(path):
                        os.remove(path)
                    fix_name = secure_filename(thumbnail.filename)
                    thumbnail.save(path)
                    manga.thumbnail = filename
                else:
                    flash('Thumbnail only support JPEG JPG PNG', category='error')
        manga.Update()

        

        flash('Event telah diubah', category='success')
    return redirect(url_for('views.home'))

#Read Manga
@views.route('/Read/<int:manga_id>', methods=['POST', 'GET'])
def Read_Manga(manga_id):
    if current_user.is_authenticated:
        user = Users.query.filter_by(id=current_user.id).first()
        profile = Profiles.query.filter_by(id=user.id).first()
    else:
        user = None
        profile = None
    manga = Manga.query.filter_by(id=manga_id).first()
    chapter = manga.chapter.order_by(Chapter.chapter.desc())
    manga_title = manga.title
    web_title = 'Manga Online - Read ' + manga_title 
    active = 'Read Manga'
    
    return render_template(
        'read/read.html', 
        active=active, 
        user=user, 
        profile=profile, 
        manga=manga, 
        title=web_title,
        chapter=chapter
    )


#Read Chapter
@views.route('/Read/<int:manga_id>/<int:chapter_num>', methods=['POST', 'GET'])
def Read_Chapter(manga_id, chapter_num):

    #Navbar condition
    if current_user.is_authenticated:
        user = Users.query.filter_by(id=current_user.id).first()
        profile = Profiles.query.filter_by(id=user.id).first()
    else:
        user = None
        profile = None

    #For chapter navigation
    manga = Manga.query.filter_by(id=manga_id).first()
    #chapter_nav = Chapter.query.filter_by(manga_id=manga.id).order_by(Chapter.chapter.asc())\
        #.paginate(page=chapter_num, per_page=1, error_out=False)
    chapter_nav = manga.chapter.order_by(Chapter.chapter.asc()).paginate(page=chapter_num, per_page=1, error_out=False)

    #For images
    chapter = Chapter.query.filter_by(manga_id=manga_id).filter_by(chapter=chapter_num).first()
    #images = ImageSet.query.filter_by(chapter_id=chapter.id).order_by(ImageSet.image.asc()).all()
    images = chapter.ImageSet.order_by(ImageSet.image.asc())
    
    
    return render_template(
        'read/manga.html', 
        manga=manga, 
        chapter=chapter, 
        images=images,
        user=user,
        profile=profile,
        chapter_nav=chapter_nav
        )


#Delete Chapter
@views.route('/DeleteChapter', methods=['POST'])
def Delete_Chapter():
    if request.form:
        chapter_id = request.form.get('chapter_id')
        chapter = Chapter.query.filter_by(id=chapter_id).first()

        manga_id = request.form.get('manga_id')
        manga = Manga.query.filter_by(id=manga_id).first()
        manga_path = MANGA_FOLDER + manga.title
        chapter_folder = os.path.join(manga_path, str(chapter.chapter))
        images = ImageSet.query.filter_by(chapter_id=chapter.id).all()
        print(chapter_folder)

        if os.path.exists(chapter_folder):
            shutil.rmtree(chapter_folder)

        chapter.Delete(chapter)
    return redirect(url_for('views.Read_Manga', manga_id=manga.id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#Upload Chapter method
@views.route('/UploadChapter', methods=['POST'])
@login_required
def UploadChapter():
    if request.method == 'POST':
        #Get value
        chapter = request.form.get('chapter')
        manga_id = request.form.get('manga_id')
        manga = Manga.query.filter_by(id=manga_id).first()
        check_chapter = Chapter.query.filter_by(chapter=chapter).filter_by(manga_id=manga.id).first()

        #Check chapter
        if check_chapter:
            flash('Chapter already available', category='error')
            return redirect(url_for('views.Read_Manga', manga_id=manga.id))

        images = request.files.getlist('files[]')
        
        
        #Check images format
        if images:
            
            #Cek images format
            for image in images:
                if allowed_file(image.filename):
                    upload = True
                else:
                    upload = False
                    break
        

        if upload:
            new_chapter = Chapter(chapter=chapter)
            manga.chapter.append(new_chapter)
            db.session.add(new_chapter)

            #Create or remove folder
            manga_path = MANGA_FOLDER + manga.title
            chapter_path = os.path.join(manga_path, str(chapter))
            zip_path = chapter_path + '\\' + manga.title + chapter + '.zip'
            
            if os.path.exists(chapter_path):
                shutil.rmtree(chapter_path)
            if not os.path.exists(chapter_path):
                os.makedirs(chapter_path)

            #Create path for record
            manga_folder = 'upload/manga/' + manga.title
            
            chapter_folder = manga_folder + '/' + str(chapter) + '/'

            linkZip = chapter_folder + manga.title + chapter + '.zip'
            #create zip file
            zipf = zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED)
            new_chapter.linkDL = linkZip
            
            #Save images and write file to zip in chapter folder
            i = 0
            for img in images:
                i = i + 1
                image = secure_filename(img.filename)
                imgs = ImageSet(image=image, image_path=chapter_folder)
                new_chapter.ImageSet.append(imgs)
                path = os.path.join(chapter_path, image)
                if os.path.exists(path):
                    os.remove(path)
                if not os.path.exists(path):
                    imgs.Create(imgs)
                    img.save(path)
                    zipf.write(path, os.path.basename(path))
            
            zipf.close()
            manga.NewChapter()
            
        else:
            flash('Images only support JPEG JPG PNG', category='error')

    return redirect(url_for('views.Read_Manga', manga_id=manga_id))

#Update Link Downlaod
@views.route('/Uplink', methods=['POST'])
@login_required
def UpdateLinkDL():
    chapter_id = request.form.get('chapter_id')
    linkDL = request.form.get('linkDL')
    chapter = Chapter.query.filter_by(id=chapter_id).first()
    chapter.UpdateLink(linkDL)
    
    return redirect(url_for('views.Read_Manga', manga_id=chapter.manga_id))
