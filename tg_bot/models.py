from sqlalchemy import Column, Integer, String, Boolean, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    product_type = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    price = Column(String, nullable=False)
    hallmark = Column(String)
    additional_info = Column(Text)
    contacts = Column(Text, nullable=False)
    media_ids = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    channel_message_ids = Column(Text)  # Сохраняем все message_id медиагруппы в канале
    admin_message_ids = Column(Text)  # Сохраняем все message_id медиагруппы в чате с администратором
    admin_buttons_message_id = Column(BigInteger)  # Сохраняем message_id сообщения с кнопками

class BannedUser(Base):
    __tablename__ = 'banned_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)