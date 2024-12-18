from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Модель таблицы user_info
class UserInfo(Base):
    __tablename__ = 'user_info'

    user_id = Column(Integer, primary_key=True)
    user_chat_state = Column(String, nullable=False)

# Модель таблицы channels
class Channel(Base):
    __tablename__ = 'channels'

    channel_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_info.user_id'))
    user_channel = Column(String, nullable=False)

# Модель таблицы lots
class Lot(Base):
    __tablename__ = 'lots'

    lot_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_info.user_id'))
    text = Column(String)
    file = Column(Integer)
    participation = Column(String)
    winners_count = Column(Integer)
    channel_id = Column(Integer, ForeignKey('channels.channel_id'))
    date = Column(String)
    end_count = Column(Integer)
    end_date = Column(String)
    players = Column(String)


# Класс Database для работы с базой данных
class Database:
    def __init__(self, db_url='sqlite:///example.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    # Методы для работы с user_info
    def user_exists(self, user_id):
        """Проверка, существует ли пользователь с данным user_id."""
        with self.Session() as session:
            return session.query(UserInfo).filter_by(user_id=user_id).first() is not None

    def get_user_chat_state(self, user_id):
        """Получение состояния чата пользователя."""
        with self.Session() as session:
            user_info = session.query(UserInfo).filter_by(user_id=user_id).first()
            return user_info.user_chat_state if user_info else None

    def set_user_chat_state(self, user_id, new_state):
        """Установка нового состояния чата пользователя."""
        with self.Session() as session:
            session.query(UserInfo).filter_by(user_id=user_id).update({"user_chat_state": new_state})
            session.commit()

    def add_user(self, user_id):
        """Добавление нового пользователя."""
        with self.Session() as session:
            if not self.user_exists(user_id):
                new_user = UserInfo(user_id=user_id, user_chat_state="")
                session.add(new_user)
                session.commit()

    def delete_user(self, user_id):
        """Удаление пользователя и его каналов."""
        with self.Session() as session:
            session.query(Channel).filter_by(user_id=user_id).delete()
            session.query(Lot).filter_by(user_id=user_id).delete()
            session.query(UserInfo).filter_by(user_id=user_id).delete()
            session.commit()

    # Методы для работы с channels
    def user_has_channels(self, user_id):
        """Проверка, есть ли у пользователя каналы."""
        with self.Session() as session:
            return session.query(Channel).filter_by(user_id=user_id).first() is not None

    def add_channel(self, user_id, channel_name, channel_id):
        """Добавление нового канала для пользователя."""
        with self.Session() as session:
            if self.user_exists(user_id):
                new_channel = Channel(user_id=user_id, user_channel=channel_name, channel_id=channel_id)
                session.add(new_channel)
                session.commit()

    def delete_channel_by_id(self, channel_id):
        """Удаление канала по его ID."""
        with self.Session() as session:
            session.query(Channel).filter_by(channel_id=channel_id).delete()
            session.commit()

    def get_user_channels(self, user_id):
        """Получение всех каналов пользователя."""
        with self.Session() as session:
            channels = session.query(Channel).filter_by(user_id=user_id).all()
            return [[channel.user_channel, channel.channel_id] for channel in channels] if channels else []


    def add_lot(self, lot_id, user_id, text, file, participation, winners_count, channel_id, date, end_count, end_date):
        with self.Session() as session:
            if self.user_exists(user_id):
                new_lot = Lot(
                    lot_id = lot_id,
                    user_id=user_id,
                    text=text,
                    file=file,
                    participation=participation,
                    winners_count=winners_count,
                    channel_id=channel_id,
                    date=date,
                    end_count=end_count,
                    end_date=end_date,
                    players=""
                )
                session.add(new_lot)
                session.commit()

    def get_lots_by_user_id(self, user_id):
        with self.Session() as session:
            lots = session.query(Lot).filter_by(user_id=user_id).all()
            return [[lot.lot_id, lot.user_id, lot.text, lot.file, lot.participation, lot.winners_count, lot.channel_id, lot.date, lot.end_count, lot.end_date] for lot in lots] if lots else []
    
    def get_lot_by_lot_id(self, lot_id):
        with self.Session() as session:
            lot = session.query(Lot).filter_by(lot_id=lot_id).all()[0]
            return [lot.lot_id, lot.user_id, lot.text, lot.file, lot.participation, lot.winners_count, lot.channel_id, lot.date, lot.end_count, lot.end_date]
