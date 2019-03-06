import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        # Return data in serialized form
        return {
            'name': self.name,
            'id': self.id
        }


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    price = Column(String(8))
    creator = Column(String(80))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
        # Return data in serialized form
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'price': self.price
        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
Base.metadata.create_all(engine)

if __name__ == '__main__':
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    category1 = Category(name="Baseball")
    session.add(category1)

    category2 = Category(name="Football")
    session.add(category2)

    category3 = Category(name="Soccer")
    session.add(category3)

    category4 = Category(name="Basketball")
    session.add(category4)

    item1 = Item(name="Bat",
                 description="A smooth club used to hit a baseball",
                 price="$9.99", category=category1,
                 creator="admin")
    session.add(item1)

    item2 = Item(name="Football",
                 description="A leather ball used for throwing",
                 price="$5.99", category=category2,
                 creator="admin")
    session.add(item2)

    item3 = Item(name="Soccerball",
                 description="A black and white ball used for kicking",
                 price="$5.99", category=category3,
                 creator="admin")
    session.add(item3)

    item4 = Item(name="Basketball",
                 description="A big ball used for shooting hoops",
                 price="$9.99", category=category4,
                 creator="admin")
    session.add(item4)

    session.commit()
