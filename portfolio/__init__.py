from datetime import datetime
from database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class PortfolioUser(Base):
    
    __tablename__ = 'portfolio_users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    risk_profile = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    watchlist_items = relationship('WatchlistItem', backref='user', lazy=True, cascade='all, delete-orphan')
    positions = relationship('Position', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'risk_profile': self.risk_profile,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PortfolioUser {self.name} ({self.risk_profile})>'

class WatchlistItem(Base):
    
    __tablename__ = 'portfolio_watchlist'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('portfolio_users.id'), nullable=False)
    symbol = Column(String(10), nullable=False)
    added_on = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'symbol', name='unique_portfolio_user_symbol'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'added_on': self.added_on.isoformat() if self.added_on else None
        }
    
    def __repr__(self):
        return f'<WatchlistItem {self.symbol} for User {self.user_id}>'

class Position(Base):
    
    __tablename__ = 'portfolio_positions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('portfolio_users.id'), nullable=False)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'symbol', name='unique_portfolio_user_position'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_cost': self.avg_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Position {self.symbol}: {self.quantity} @ ${self.avg_cost}>'

__all__ = ['PortfolioUser', 'WatchlistItem', 'Position']
