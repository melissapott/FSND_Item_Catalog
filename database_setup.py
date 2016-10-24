from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# define database tables - User, Category, and Item
class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	email = Column(String(250))

	@property
	def serialize(self):
	#this will be used for returning a JSON object
		return {
			'id': self.id,
			'name' : self.name,
			'email' : self.email
		}

class Category(Base):
	__tablename__ = 'category'
	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	description = Column(String(250))
	icon = Column(String(250))
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
	#this will be used for returing a JSON object
		return {
			'id' : self.id,
			'name' : self.name,
			'description' : self.description,
			'icon' : self.icon,
			'user_id' : self.user_id
		}

class Item(Base):
	__tablename__ = 'item'
	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	description = Column(String(250))
	price = Column(String(10))
	image = Column(String(250))
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
	#this will be used for returning a JSON object
		return {
			'id' : self.id,
			'name' : self.name,
			'description' : self.description,
			'price' : self.price,
			'image' : self.image,
			'category' : self.category.name,
			'user_id' : self.user_id
		}

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)