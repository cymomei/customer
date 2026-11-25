# 接口层
import os
from pathlib import Path
from fastapi import FastAPI
from sqlalchemy import create_engine
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.CustomerModels import ResponseResult
from app.CustomerDb import *
import uvicorn
app = FastAPI(title="客户管理系统")

# 前端页面直接双击打开（file://）时需要跳域访问，同源访问下这个配置不会有副作用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# static 与 app 是项目根下的同级目录，上溯两级取到根目录
BASE_DIR = Path(__file__).resolve().parent.parent
FRONT_PATH = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=FRONT_PATH), name="static")

load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "customer_test")

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    echo=True,
)
# 提供session对象
def create_session():
    with Session(engine) as session:
        print("session创建成功")
        yield session
        print("session成功关闭")


# pip install sqlmodel pymysql fastapi uvicorn openai
# 将实体搬运过来，并且用pydantic修正一下（将数据库表的主键修正int类型）
# 创建接口层，将基础的一些 （createSession函数 连接字符串）拷贝过来
@app.get("/", include_in_schema=False)
def index():
    """前端管理页：http://127.0.0.1:8806/"""
    return FileResponse(FRONT_PATH / "index.html")


@app.post("/add_customer")
def add_customer(customer: Customer, session: Session = Depends(create_session)):
    code = add_customer_db(customer, session)
    if code != 200:
        return ResponseResult(code=code, msg="添加失败，编号可能已存在")
    return ResponseResult(code=0, msg="添加成功", data=customer)

@app.get("/query_customers")
def query_customers(session: Session = Depends(create_session)):
    customers = query_customers_db(session)
    return ResponseResult(code=0, msg="查询成功", data=customers)

@app.get("/query_customer/{id}")
def query_customer(id: int, session: Session = Depends(create_session)):
    customer = query_customer_byid_db(id, session)
    return ResponseResult(code=0, msg="查询成功", data=customer)
@app.get("/query_customer_byname")
def query_customer_byname(name: str, session: Session = Depends(create_session)):
    customers = query_customer_byname_db(name, session)
    return ResponseResult(code=0, msg="查询成功", data=customers)

@app.delete("/delete_customer/{id}")
def delete_customer(id: int, session: Session = Depends(create_session)):
    code = del_customer_db(id, session)
    return ResponseResult(code=code, msg="删除成功" if code == 200 else "删除失败，客户不存在")

@app.put("/update_customer")
def update_customer(customer: Customer, session: Session = Depends(create_session)):
    code = update_customer_db(customer, session)
    return ResponseResult(code=code, msg="修改成功" if code == 200 else "修改失败，客户不存在")

@app.post("/add_customer_ai")
def add_customer_ai(text: str, session: Session = Depends(create_session)):
    code, data = add_customer_ai_db(text, session)
    if code != 200:
        # 失败时 data 是错误文案
        return ResponseResult(code=code, msg=data)
    return ResponseResult(code=0, msg="AI添加成功", data=data)

@app.post("/ai_chat")
def ai_chat_api(question: str, session: Session = Depends(create_session)):
    code, answer = ai_chat_db(question, session)
    if code != 200:
        return ResponseResult(code=code, msg=answer)
    return ResponseResult(code=0, msg="回答成功", data=answer)
if __name__ == "__main__":

    uvicorn.run(app, host=os.getenv("APP_HOST", "127.0.0.1"), port=int(os.getenv("APP_PORT", "8806")))



