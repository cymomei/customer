import re
from typing import Any

from pydantic import BaseModel
from sqlmodel import *


class Customer(SQLModel, table=True):
    __tablename__ = "customer"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default=None, max_length=20, min_length=2)
    age: int = Field(default=None, gt=18, lt=80)
    gender: str = Field(default=None, max_length=1, min_length=1)
    phone: str = Field(default=None, max_length=11, min_length=11)
    email: str = Field(default=None, max_length=100, min_length=5)


    # 静态函数：常常用作 工具性质的 函数上面
    # 工具性质： 很多地方都有可能去调用  / 专门对外提供一些 功能服务的
    @staticmethod
    def check_id(id) -> bool:
        return bool(re.fullmatch(r"[1-9]\d{2,5}", id))

    @staticmethod
    def check_name(name) -> bool:
        return bool(re.fullmatch(r"[\u4e00-\u9fa5]{2,20}", name))

    @staticmethod
    def check_age(age) -> bool:
        return True if 18 <= int(age) <= 80 else False

    @staticmethod
    def check_phone(phone) -> bool:
        return bool(re.fullmatch(r"1[3-9]\d{9}", phone))

    @staticmethod
    def check_email(email) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email))


class ResponseResult(BaseModel):
    code: int
    msg: str
    data: Any | None = Field(default=None)