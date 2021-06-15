from App import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Users(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True)
	email = db.Column(db.String(150), unique=True)
	password = db.Column(db.String(150), nullable=False)
	level = db.Column(db.Integer, nullable=False)
	created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
	active = db.Column(db.Integer, default=0, nullable=False)
	last_active = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)

	def Create(self, profile):
		self.profile.append(profile)
		db.session.add(self)
		db.session.add(profile)
		self.Update()
	
	def Update(self):
		db.session.commit()

	def Active(self, active):
		if (active == 1):
			self.last_active = func.now()
		self.active = active
		self.Update()

	def Delete(self):
		db.session.delete(self)
		self.Update()
		
	#Relation
	profile = db.relationship("Profiles", cascade="all,delete", backref="user", lazy='dynamic')
	report = db.relationship('Report', cascade="all,delete", backref="user", lazy='dynamic')

class Report(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(db.Text(2000), nullable=False)
	date = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

class Profiles(db.Model):
	id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
	name = db.Column(db.String(150), nullable=True)
	picture = db.Column(db.String(150), nullable=True)

#One Manga to Many Chapter
class Manga(db.Model, UserMixin):
	#Column on table
	id = db.Column(db.Integer, primary_key=True)
	thumbnail = db.Column(db.String(150), nullable=False)
	folder_path = db.Column(db.String(150), nullable=False)
	title = db.Column(db.String(150), nullable=False)
	author = db.Column(db.String(150), nullable=False)
	genre = db.Column(db.String(150), nullable=False)
	status = db.Column(db.String(150), nullable=False)
	description = db.Column(db.Text(2000), nullable=False)
	added_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
	updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)

	#Create manga
	def Create(self, manga):
		db.session.add(manga)
		self.Update()

	def Update(self):
		db.session.commit()

	#Update manga if chapter added
	def NewChapter(self):
		self.updated_at = func.now()
		db.session.commit()
	
	#Delete manga
	def Delete(self, manga):
		db.session.delete(manga)
		self.Update()


	#Relation
	#Delete chapter will delete all images 
	chapter = db.relationship("Chapter", cascade="all,delete", backref="manga", lazy='dynamic')


#One Chapter to Many ImageSet
class Chapter(db.Model):
	#Column on table
	id = db.Column(db.Integer, primary_key=True)
	chapter = db.Column(db.Integer, nullable=False)
	linkDL = db.Column(db.String(150), nullable=True)
	added_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)

	#Update Chapter
	def Update(self):
		db.session.commit()

	def UpdateLink(self, linkDL):
		self.linkDL = linkDL
		self.Update()

	#Delete Chapter
	def Delete(self, chapter):
		db.session.delete(chapter)
		self.Update()

	#Relation
	ImageSet = db.relationship("ImageSet", cascade="all,delete", backref="chapter", lazy='dynamic')
	manga_id = db.Column(db.Integer, db.ForeignKey('manga.id', ondelete='CASCADE'))

class ImageSet(db.Model):
	#Column on table
	id = db.Column(db.Integer, primary_key=True)
	image = db.Column(db.Integer, nullable=False)
	image_path = db.Column(db.String(150), nullable=False)
	chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete='CASCADE'))

	#Update Image
	def Update(self):
		db.session.commit()

	def Create(self, imgs):
		db.session.add(imgs)
	
	#Manual delete if passive delete from chapter not work
	def DeleteAll(self, image, images):
		for image in images:
			db.session.delete(image)
		self.Update()


	
	


