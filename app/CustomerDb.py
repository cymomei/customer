from sqlmodel import Session, select
from app.CustomerModels import Customer
from ai_tools import *

def add_customer_db(customer:Customer,session:Session):
    try:
        session.add(customer)
        session.commit()
        session.refresh(customer)   # 刷新后才能拿到数据库自增的 id
    except Exception:
        session.rollback()          # 主键冲突等异常必须回滚，否则 session 会处于脏状态
        return 500
    return 200


def del_customer_db(id:int,session:Session):
    try:
        tmp = session.get(Customer,id)
        if tmp is None:          # 客户不存在，直接告诉调用方
            return 404
        session.delete(tmp)
        session.commit()
    except:
        session.rollback()       # 删除失败要把事务回滚掉，否则 session 会处于脏状态
        return 500
    return 200


def update_customer_db(customer:Customer,session:Session):
    try:
        tmp = session.get(Customer,customer.id)
        if tmp is None:             # 编号不存在，返回 404 而不是 500
            return 404
        tmp.name = customer.name
        tmp.age = customer.age
        tmp.gender = customer.gender
        tmp.phone = customer.phone
        tmp.email = customer.email
        session.commit()
    except Exception:
        session.rollback()
        return 500
    return 200


def query_customers_db(session:Session):
    stmt = select(Customer)
    result = session.exec(stmt).all()
    return result

# 5、根据ID查询客户
def query_customer_byid_db(id:int,session:Session):
    return session.get(Customer,id)

def query_customer_byname_db(name:str,session:Session):
    stmt = select(Customer).where(Customer.name.contains(name))
    result = session.exec(stmt).all()
    return result


def add_customer_ai_db(text,session:Session):
    # 1、AI 从自然语言里抽取字段
    customer_dict = ai_extract_customer_data(text)
    if not customer_dict or not customer_dict.get("name"):
        return 400, "未从文本中识别到有效客户信息"

    # 2、AI 逐字段校验（比 Pydantic 严格：手机号/邮箱格式、性别取值）
    check_result = ai_check_customer_data(customer_dict)
    if not check_result.get("valid"):
        return 400, "；".join(check_result.get("errors", []))

    # 3、丢掉 null 字段（如文本没提编号），再交给 Pydantic 兜底校验
    payload = {k: v for k, v in customer_dict.items() if v is not None and k in Customer.model_fields}
    try:
        customer = Customer(**payload)
    except Exception as e:
        return 400, f"数据校验失败：{e}"

    # 4、入库（返回 状态码 + 实体，方便接口层把新编号回传给前端）
    code = add_customer_db(customer, session)
    if code != 200:
        return code, "数据库写入失败，客户编号可能已存在"
    return 200, customer

def ai_check_customer_data_db(customer_dict):
    return ai_check_customer_data(customer_dict)

def ai_chat_db(question:str,session:Session):
    customers = query_customers_db(session)
    matched = [c for c in customers if c.name and c.name in question]
    customer_data = [c.model_dump() for c in (matched or customers)]
    try:
        answer = ai_chat(question, customer_data)
    except Exception:
        return 500, "AI 服务异常，请稍后重试..."
    return 200, answer