from sqlalchemy import Column, Integer, String, Text, DateTime, Date, DECIMAL, Boolean, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class City(Base):
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Relationships
    advertising_campaigns = relationship("AdvertisingCampaign", back_populates="city")
    masters = relationship("Master", back_populates="city")
    employees = relationship("Employee", back_populates="city")
    requests = relationship("Request", back_populates="city")
    transactions = relationship("Transaction", back_populates="city")


class RequestType(Base):
    __tablename__ = "request_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    requests = relationship("Request", back_populates="request_type")


class Direction(Base):
    __tablename__ = "directions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    requests = relationship("Request", back_populates="direction")


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    employees = relationship("Employee", back_populates="role")
    administrators = relationship("Administrator", back_populates="role")


class TransactionType(Base):
    __tablename__ = "transaction_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="transaction_type")


class AdvertisingCampaign(Base):
    __tablename__ = "advertising_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    name = Column(String(200), nullable=False)
    phone_number = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    city = relationship("City", back_populates="advertising_campaigns")
    requests = relationship("Request", back_populates="advertising_campaign")


class Master(Base):
    __tablename__ = "masters"
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    full_name = Column(String(200), nullable=False)
    phone_number = Column(String(20), nullable=False)
    birth_date = Column(Date)
    passport = Column(String(20))
    status = Column(String(50), default="active")
    chat_id = Column(String(100))
    login = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    city = relationship("City", back_populates="masters")
    requests = relationship("Request", back_populates="master")


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(String(50), default="active")
    city_id = Column(Integer, ForeignKey("cities.id"))
    login = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="employees", lazy="joined")
    city = relationship("City", back_populates="employees", lazy="joined")


class Administrator(Base):
    __tablename__ = "administrators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(String(50), default="active")
    login = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="administrators")


class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    advertising_campaign_id = Column(Integer, ForeignKey("advertising_campaigns.id"))
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    request_type_id = Column(Integer, ForeignKey("request_types.id"), nullable=False)
    client_phone = Column(String(20), nullable=False)
    client_name = Column(String(200), nullable=True)
    address = Column(Text)
    meeting_date = Column(DateTime(timezone=True))
    direction_id = Column(Integer, ForeignKey("directions.id"))
    problem = Column(Text)
    status = Column(String(50), default="Новая")
    master_id = Column(Integer, ForeignKey("masters.id"))
    master_notes = Column(Text)
    result = Column(Numeric(10, 2), nullable=True)
    expenses = Column(DECIMAL(10, 2), default=0)
    net_amount = Column(DECIMAL(10, 2), default=0)
    master_handover = Column(DECIMAL(10, 2), default=0)
    ats_number = Column(String(50))
    call_center_name = Column(String(200))
    call_center_notes = Column(Text)
    bso_file_path = Column(String(500))
    expense_file_path = Column(String(500))
    recording_file_path = Column(String(500))
    avito_chat_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships с оптимизацией загрузки
    advertising_campaign = relationship("AdvertisingCampaign", back_populates="requests", lazy="select")
    city = relationship("City", back_populates="requests", lazy="select")
    request_type = relationship("RequestType", back_populates="requests", lazy="select")
    direction = relationship("Direction", back_populates="requests", lazy="select")
    master = relationship("Master", back_populates="requests", lazy="select")
    files = relationship("File", back_populates="request", lazy="select")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    transaction_type_id = Column(Integer, ForeignKey("transaction_types.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    notes = Column(Text)
    file_path = Column(String(500))
    specified_date = Column(Date, nullable=False)
    payment_reason = Column(Text, nullable=True)
    expense_receipt_path = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships с оптимизацией загрузки
    city = relationship("City", back_populates="transactions", lazy="select")
    transaction_type = relationship("TransactionType", back_populates="transactions", lazy="select")
    files = relationship("File", back_populates="transaction", lazy="select")


class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"))
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"))
    file_type = Column(String(50), nullable=False)  # bso, expense, recording, transaction
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Check constraint to ensure only one reference is set
    __table_args__ = (
        CheckConstraint(
            "(request_id IS NOT NULL AND transaction_id IS NULL) OR (request_id IS NULL AND transaction_id IS NOT NULL)",
            name="check_reference"
        ),
    )
    
    # Relationships
    request = relationship("Request", back_populates="files")
    transaction = relationship("Transaction", back_populates="files") 