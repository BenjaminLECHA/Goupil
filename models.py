from typing import Optional
import datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, \
    String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from constants import DB_DEFAULT_EMPTY_VARYING, DB_APP_ID_FK, DB_USERS_USER_ID_FK, \
    DB_DEMANDES_DEMANDE_ID_FK, DB_ISSUES_ISSUE_ID_FK


class Base(DeclarativeBase):
    pass


class App(Base):
    __tablename__ = 'app'
    __table_args__ = (
        PrimaryKeyConstraint('app_id', name='app_pkey'),
        UniqueConstraint('acronyme', name='app_acronyme_key')
    )

    app_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    acronyme: Mapped[str] = mapped_column(String(20), nullable=False)
    git_id: Mapped[int] = mapped_column(Integer, nullable=False)
    git_url: Mapped[str] = mapped_column(String(100), nullable=False)
    private_token: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self):
        return self.acronyme

    demandes: Mapped[list['Demandes']] = relationship('Demandes', back_populates='app')
    issues: Mapped[list['Issues']] = relationship('Issues', back_populates='app')
    labels: Mapped[list['Labels']] = relationship('Labels', back_populates='app')
    milestones: Mapped[list['Milestones']] = relationship('Milestones', back_populates='app')
    user_app: Mapped[list['UserApp']] = relationship('UserApp', back_populates='app')


class Statuts(Base):
    __tablename__ = 'statuts'
    __table_args__ = (
        PrimaryKeyConstraint('statut_id', name='statuts_pkey'),
    )

    statut_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[Optional[str]] = mapped_column(String(100))

    def __repr__(self):
        return self.nom if self.nom else f"Statut {self.statut_id}"

    demandes: Mapped[list['Demandes']] = relationship('Demandes', back_populates='statut')


class Users(Base, UserMixin):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("email::text ~* '^[A-Za-z0-9._%%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'::text", name='valid_email'),
        PrimaryKeyConstraint('user_id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        UniqueConstraint('username', name='users_username_key')
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text(DB_DEFAULT_EMPTY_VARYING))
    email: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text(DB_DEFAULT_EMPTY_VARYING))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False,
                                               server_default=text(DB_DEFAULT_EMPTY_VARYING))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    is_admin: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return self.username

    demandes: Mapped[list['Demandes']] = relationship('Demandes', back_populates='user')
    user_app: Mapped[list['UserApp']] = relationship('UserApp', back_populates='user')
    messages: Mapped[list['Messages']] = relationship('Messages', back_populates='user')

    def set_password(self, password: str):
        """Hache le mot de passe avec Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Vérifie si le mot de passe est correct."""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Retourne l'identifiant unique de l'utilisateur (requis par Flask-Login)."""
        return str(self.user_id)

    def get_accessible_apps(self):
        """Retourne la liste des applications auxquelles l'utilisateur a accès."""
        from setup import db
        from models import App, UserApp
        if self.is_admin:
            return db.session.query(App).all()
        return [ua.app for ua in self.user_app]

    def get_app_list(self):
        """Retourne la liste des IDs des applications auxquelles l'utilisateur a accès."""
        if self.is_admin:
            from setup import db
            from models import App
            return [app.app_id for app in db.session.query(App).all()]
        return [ua.app_id for ua in self.user_app]


class CategorieDemande(Base):
    __tablename__ = 'categorie_demande'
    __table_args__ = (
        PrimaryKeyConstraint('categorie_id', name='categorie_demande_pkey'),
    )

    categorie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7))

    def __repr__(self):
        return self.nom

    demandes: Mapped[list['Demandes']] = relationship('Demandes', back_populates='categorie')


class Demandes(Base):
    __tablename__ = 'demandes'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], [DB_APP_ID_FK], ondelete='CASCADE', name='demandes_app_id_fkey'),
        ForeignKeyConstraint(['statut_id'], ['statuts.statut_id'], name='demandes_statut_id_fkey'),
        ForeignKeyConstraint(['user_id'], [DB_USERS_USER_ID_FK], ondelete='SET NULL', name='demandes_user_id_fkey'),
        ForeignKeyConstraint(['categorie_id'], ['categorie_demande.categorie_id'], name='demandes_categorie_id_fkey'),
        PrimaryKeyConstraint('demande_id', name='demandes_pkey')
    )

    demande_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    statut_id: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    app_id: Mapped[Optional[int]] = mapped_column(Integer)
    categorie_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return self.title if self.title else f"Demande {self.demande_id}"

    app: Mapped[Optional['App']] = relationship('App', back_populates='demandes')
    statut: Mapped[Optional['Statuts']] = relationship('Statuts', back_populates='demandes')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='demandes')
    categorie: Mapped[Optional['CategorieDemande']] = relationship('CategorieDemande', back_populates='demandes')
    demande_issue: Mapped[list['DemandeIssue']] = relationship('DemandeIssue', back_populates='demande')
    messages: Mapped[list['Messages']] = relationship('Messages', back_populates='demande')
    pieces_jointes: Mapped[list['PiecesJointes']] = relationship('PiecesJointes', back_populates='demande')

    def count_message(self):
        i = 0
        for _ in self.messages:
            i += 1
        return i


class Issues(Base):
    __tablename__ = 'issues'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], [DB_APP_ID_FK], ondelete='CASCADE', name='issues_app_id_fkey'),
        PrimaryKeyConstraint('issue_id', name='issues_pkey')
    )

    issue_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    git_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_closed: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    app_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    web_url: Mapped[Optional[str]] = mapped_column(String(255))

    def __repr__(self):
        return self.title if self.title else f"Issue {self.issue_id}"

    app: Mapped[Optional['App']] = relationship('App', back_populates='issues')
    demande_issue: Mapped[list['DemandeIssue']] = relationship('DemandeIssue', back_populates='issue')
    label_issue: Mapped[list['LabelIssue']] = relationship('LabelIssue', back_populates='issue')
    millestone_issue: Mapped[list['MillestoneIssue']] = relationship('MillestoneIssue', back_populates='issue')


class Labels(Base):
    __tablename__ = 'labels'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], [DB_APP_ID_FK], ondelete='CASCADE', name='labels_app_id_fkey'),
        PrimaryKeyConstraint('label_id', name='labels_pkey')
    )

    label_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    git_id: Mapped[Optional[int]] = mapped_column(Integer)
    color: Mapped[Optional[str]] = mapped_column(String(7))
    app_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    def __repr__(self):
        return self.title if self.title else f"Label {self.label_id}"

    app: Mapped[Optional['App']] = relationship('App', back_populates='labels')
    label_issue: Mapped[list['LabelIssue']] = relationship('LabelIssue', back_populates='label')


class Milestones(Base):
    __tablename__ = 'milestones'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], [DB_APP_ID_FK], ondelete='CASCADE', name='milestones_app_id_fkey'),
        PrimaryKeyConstraint('milestone_id', name='milestones_pkey')
    )

    milestone_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    is_closed: Mapped[Optional[bool]] = mapped_column(Boolean)
    git_id: Mapped[Optional[int]] = mapped_column(Integer)
    app_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    def __repr__(self):
        return self.title if self.title else f"Milestone {self.milestone_id}"

    app: Mapped[Optional['App']] = relationship('App', back_populates='milestones')
    millestone_issue: Mapped[list['MillestoneIssue']] = relationship('MillestoneIssue', back_populates='milestone')


class UserApp(Base):
    __tablename__ = 'user_app'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], [DB_APP_ID_FK], ondelete='CASCADE', name='user_app_app_id_fkey'),
        ForeignKeyConstraint(['user_id'], [DB_USERS_USER_ID_FK], ondelete='CASCADE', name='user_app_user_id_fkey'),
        PrimaryKeyConstraint('user_app_id', name='user_app_pkey')
    )

    user_app_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_dev: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    app_id: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self):
        try:
            return f"{self.user.username} - {self.app.acronyme}"
        except Exception:
            return f"UserApp {self.user_app_id}"

    app: Mapped[Optional['App']] = relationship('App', back_populates='user_app')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='user_app')


class DemandeIssue(Base):
    __tablename__ = 'demande_issue'
    __table_args__ = (
        ForeignKeyConstraint(['demande_id'], [DB_DEMANDES_DEMANDE_ID_FK], ondelete='CASCADE',
                             name='demande_issue_demande_id_fkey'),
        ForeignKeyConstraint(['issue_id'], [DB_ISSUES_ISSUE_ID_FK], ondelete='CASCADE',
                             name='demande_issue_issue_id_fkey'),
        PrimaryKeyConstraint('demande_issue_id', name='demande_issue_pkey')
    )

    demande_issue_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    demande_id: Mapped[Optional[int]] = mapped_column(Integer)
    issue_id: Mapped[Optional[int]] = mapped_column(Integer)

    demande: Mapped[Optional['Demandes']] = relationship('Demandes', back_populates='demande_issue')
    issue: Mapped[Optional['Issues']] = relationship('Issues', back_populates='demande_issue')


class LabelIssue(Base):
    __tablename__ = 'label_issue'
    __table_args__ = (
        ForeignKeyConstraint(['issue_id'], [DB_ISSUES_ISSUE_ID_FK], ondelete='CASCADE',
                             name='label_issue_issue_id_fkey'),
        ForeignKeyConstraint(['label_id'], ['labels.label_id'], ondelete='CASCADE', name='label_issue_label_id_fkey'),
        PrimaryKeyConstraint('label_issue_id', name='label_issue_pkey')
    )

    label_issue_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label_id: Mapped[Optional[int]] = mapped_column(Integer)
    issue_id: Mapped[Optional[int]] = mapped_column(Integer)

    issue: Mapped[Optional['Issues']] = relationship('Issues', back_populates='label_issue')
    label: Mapped[Optional['Labels']] = relationship('Labels', back_populates='label_issue')


class Messages(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        ForeignKeyConstraint(['demande_id'], [DB_DEMANDES_DEMANDE_ID_FK], ondelete='CASCADE',
                             name='messages_demande_id_fkey'),
        ForeignKeyConstraint(['user_id'], [DB_USERS_USER_ID_FK], ondelete='SET NULL', name='messages_user_id_fkey'),
        PrimaryKeyConstraint('message_id', name='messages_pkey')
    )

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    demande_id: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return self.content[:30] + '...' if len(self.content) > 30 else self.content

    demande: Mapped[Optional['Demandes']] = relationship('Demandes', back_populates='messages')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='messages')
    pieces_jointes: Mapped[list['PiecesJointes']] = relationship('PiecesJointes', back_populates='message')


class MillestoneIssue(Base):
    __tablename__ = 'millestone_issue'
    __table_args__ = (
        ForeignKeyConstraint(['issue_id'], [DB_ISSUES_ISSUE_ID_FK], ondelete='CASCADE',
                             name='millestone_issue_issue_id_fkey'),
        ForeignKeyConstraint(['milestone_id'], ['milestones.milestone_id'], ondelete='CASCADE',
                             name='millestone_issue_milestone_id_fkey'),
        PrimaryKeyConstraint('millestone_issue_id', name='millestone_issue_pkey')
    )

    millestone_issue_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    milestone_id: Mapped[Optional[int]] = mapped_column(Integer)
    issue_id: Mapped[Optional[int]] = mapped_column(Integer)

    issue: Mapped[Optional['Issues']] = relationship('Issues', back_populates='millestone_issue')
    milestone: Mapped[Optional['Milestones']] = relationship('Milestones', back_populates='millestone_issue')


class PiecesJointes(Base):
    __tablename__ = 'pieces_jointes'
    __table_args__ = (
        ForeignKeyConstraint(['demande_id'], [DB_DEMANDES_DEMANDE_ID_FK], ondelete='CASCADE',
                             name='pieces_jointes_demande_id_fkey'),
        ForeignKeyConstraint(['message_id'], ['messages.message_id'], ondelete='CASCADE',
                             name='pieces_jointes_message_id_fkey'),
        PrimaryKeyConstraint('piece_jointe_id', name='pieces_jointes_pkey')
    )

    piece_jointe_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(255), nullable=False)
    demande_id: Mapped[Optional[int]] = mapped_column(Integer)
    message_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    demande: Mapped[Optional['Demandes']] = relationship('Demandes', back_populates='pieces_jointes')
    message: Mapped[Optional['Messages']] = relationship('Messages', back_populates='pieces_jointes')
