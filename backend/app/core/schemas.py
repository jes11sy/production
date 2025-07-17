from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# Base schemas
class CityBase(BaseModel):
    name: str = Field(..., max_length=100)


class RequestTypeBase(BaseModel):
    name: str = Field(..., max_length=50)


class DirectionBase(BaseModel):
    name: str = Field(..., max_length=50)


class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)


class TransactionTypeBase(BaseModel):
    name: str = Field(..., max_length=50)


class AdvertisingCampaignBase(BaseModel):
    city_id: int
    name: str = Field(..., max_length=200)
    phone_number: str = Field(..., max_length=20)


class MasterBase(BaseModel):
    city_id: int
    full_name: str = Field(..., max_length=200)
    phone_number: str = Field(..., max_length=20)
    birth_date: Optional[date] = None
    passport: Optional[str] = Field(None, max_length=20)
    status: str = Field(default="active", max_length=50)
    chat_id: Optional[str] = Field(None, max_length=100)
    login: str = Field(..., max_length=100)
    notes: Optional[str] = None


class EmployeeBase(BaseModel):
    name: str = Field(..., max_length=200)
    role_id: int
    status: str = Field(default="active", max_length=50)
    city_id: Optional[int] = None
    login: str = Field(..., max_length=100)
    notes: Optional[str] = None


class AdministratorBase(BaseModel):
    name: str = Field(..., max_length=200)
    role_id: int
    status: str = Field(default="active", max_length=50)
    login: str = Field(..., max_length=100)
    notes: Optional[str] = None


class RequestBase(BaseModel):
    advertising_campaign_id: Optional[int] = None
    city_id: int
    request_type_id: Optional[int] = None
    client_phone: str = Field(..., max_length=20)
    client_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    meeting_date: Optional[datetime] = None
    direction_id: Optional[int] = None
    problem: Optional[str] = None
    status: str = Field(default="new", max_length=50)
    master_id: Optional[int] = None
    master_notes: Optional[str] = None
    result: Optional[Decimal] = Field(None, decimal_places=2)
    expenses: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    net_amount: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    master_handover: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    ats_number: Optional[str] = Field(None, max_length=50)
    call_center_name: Optional[str] = Field(None, max_length=200)
    call_center_notes: Optional[str] = None
    avito_chat_id: Optional[str] = Field(None, max_length=100)
    
    @validator('meeting_date', pre=True)
    @classmethod
    def validate_meeting_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class TransactionBase(BaseModel):
    city_id: int
    transaction_type_id: int
    amount: Decimal = Field(..., decimal_places=2)
    notes: Optional[str] = None
    specified_date: date
    payment_reason: Optional[str] = None
    expense_receipt_path: Optional[str] = None


class FileBase(BaseModel):
    request_id: Optional[int] = None
    transaction_id: Optional[int] = None
    file_type: str = Field(..., max_length=50)
    file_path: str = Field(..., max_length=500)


# Create schemas
class CityCreate(CityBase):
    pass


class RequestTypeCreate(RequestTypeBase):
    pass


class DirectionCreate(DirectionBase):
    pass


class RoleCreate(RoleBase):
    pass


class TransactionTypeCreate(TransactionTypeBase):
    pass


class AdvertisingCampaignCreate(AdvertisingCampaignBase):
    pass


class MasterCreate(MasterBase):
    password: str = Field(..., min_length=6)


class EmployeeCreate(EmployeeBase):
    password: str = Field(..., min_length=6)


class AdministratorCreate(AdministratorBase):
    password: str = Field(..., min_length=6)


class RequestCreate(BaseModel):
    advertising_campaign_id: Optional[int] = None
    city_id: int
    request_type_id: Optional[int] = None
    client_phone: str = Field(..., max_length=20)
    client_name: Optional[str] = None
    address: Optional[str] = None
    meeting_date: Optional[datetime] = None
    direction_id: Optional[int] = None
    problem: Optional[str] = None
    status: str = Field(default="new", max_length=50)
    master_id: Optional[int] = None
    master_notes: Optional[str] = None
    result: Optional[Decimal] = Field(None, decimal_places=2)
    expenses: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    net_amount: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    master_handover: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    ats_number: Optional[str] = Field(None, max_length=50)
    call_center_name: Optional[str] = Field(None, max_length=200)
    call_center_notes: Optional[str] = None
    avito_chat_id: Optional[str] = Field(None, max_length=100)
    
    @validator('meeting_date', pre=True)
    @classmethod
    def validate_meeting_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class TransactionCreate(TransactionBase):
    pass


class FileCreate(FileBase):
    pass


# Update schemas
class CityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)


class RequestTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class DirectionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class TransactionTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class AdvertisingCampaignUpdate(BaseModel):
    city_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    phone_number: Optional[str] = Field(None, max_length=20)


class MasterUpdate(BaseModel):
    city_id: Optional[int] = None
    full_name: Optional[str] = Field(None, max_length=200)
    phone_number: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    passport: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=50)
    chat_id: Optional[str] = Field(None, max_length=100)
    login: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    role_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)
    city_id: Optional[int] = None
    login: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class AdministratorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    role_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)
    login: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class RequestUpdate(BaseModel):
    advertising_campaign_id: Optional[int] = None
    city_id: Optional[int] = None
    request_type_id: Optional[int] = None
    client_phone: Optional[str] = Field(None, max_length=20)
    client_name: Optional[str] = None
    address: Optional[str] = None
    meeting_date: Optional[datetime] = None
    direction_id: Optional[int] = None
    problem: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    master_id: Optional[int] = None
    master_notes: Optional[str] = None
    result: Optional[Decimal] = Field(None, decimal_places=2)
    expenses: Optional[Decimal] = Field(None, decimal_places=2)
    net_amount: Optional[Decimal] = Field(None, decimal_places=2)
    master_handover: Optional[Decimal] = Field(None, decimal_places=2)
    ats_number: Optional[str] = Field(None, max_length=50)
    call_center_name: Optional[str] = Field(None, max_length=200)
    call_center_notes: Optional[str] = None
    avito_chat_id: Optional[str] = Field(None, max_length=100)
    bso_file_path: Optional[str] = None
    expense_file_path: Optional[str] = None
    recording_file_path: Optional[str] = None
    
    @validator('meeting_date', pre=True)
    @classmethod
    def validate_meeting_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class TransactionUpdate(BaseModel):
    city_id: Optional[int] = None
    transaction_type_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, decimal_places=2)
    notes: Optional[str] = None
    specified_date: Optional[date] = None
    payment_reason: Optional[str] = None
    expense_receipt_path: Optional[str] = None
    
    @validator('specified_date', pre=True)
    @classmethod
    def validate_specified_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class FileUpdate(BaseModel):
    file_type: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=500)


# Response schemas
class CityResponse(CityBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RequestTypeResponse(RequestTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DirectionResponse(DirectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TransactionTypeResponse(TransactionTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AdvertisingCampaignResponse(AdvertisingCampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    city: CityResponse


class MasterResponse(MasterBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    city: CityResponse


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    role: RoleResponse
    city: Optional[CityResponse] = None


class AdministratorResponse(AdministratorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    role: RoleResponse


class FileResponse(FileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uploaded_at: datetime


class RequestResponse(RequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    advertising_campaign: Optional[AdvertisingCampaignResponse] = None
    city: CityResponse
    request_type: RequestTypeResponse
    direction: Optional[DirectionResponse] = None
    master: Optional[MasterResponse] = None
    files: List[FileResponse] = []
    bso_file_path: Optional[str] = None
    expense_file_path: Optional[str] = None
    recording_file_path: Optional[str] = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    city: CityResponse
    transaction_type: TransactionTypeResponse
    files: List[FileResponse] = []


# Authentication schemas
class UserLogin(BaseModel):
    login: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None 