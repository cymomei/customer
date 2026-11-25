# 封装所有AI的功能函数
# 1、AI 智能的从 用户输入的文本中 提取有效信息
import json
import os
from http import client

from dotenv import load_dotenv
from openai import OpenAI

# 0、加载项目根目录下的 .env 配置文件（密钥不写死在代码里，也不进仓库）
load_dotenv()

# 1、定义 AI所需的基础配置  base url  / api key / model
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def get_client():
    """统一构建 AI 客户端，顺便检查密钥是否已配置"""
    if not API_KEY:
        raise RuntimeError("未读取到 DEEPSEEK_API_KEY，请在项目根目录的 .env 文件中配置后重启服务")
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


# AI智能添加客户数据
def ai_extract_customer_data(text):
    # 2、构建 client 客户端对象
    client = get_client()
    # 3、订制 AI 的人设（限制AI的联想，输出信息必须都关联我们自己的数据，限制AI返回的格式要求）
    system_prompt = """你是一个智能信息分离小助手。你的任务是从用户输入的自然语言文本中，分离出有效信息，并按指定 JSON 格式输出。

    ## 需要分离的字段
    1. id：客户编号，通常为3-6位的数字。
    2. name：姓名，中文姓名或英文姓名。
    3. age：年龄，必须是整数（如 28）。若文本中写的是中文数字（如"二十岁"），请转换为整数 20。
    4. gender：性别，只能是 "男" 或 "女"。
    5. phone：电话号码，保留数字串，去掉空格、横线等分隔符（如 "138-0013-8000" 输出 "13800138000"）。
    6. email：电子邮箱地址，保持原样。

    ## 处理规则
    1. 只提取文本中明确出现的信息，不要推测、不要补全、不要编造虚假信息。
    2. 文本中没有出现的字段，一律用 null 填充（JSON 中的 null 对应 Python 的 None），不要用空字符串代替。
    3. 如果某字段信息模糊、无法确定，也用 null 填充，不要猜测。
    4. 如果文本中包含多个人的信息，只提取第一个人的信息。
    5. 如果文本与上述字段完全无关，输出所有字段为 null 的 JSON。

    ## 输出格式（严格遵守）
    - 只输出一个 JSON 对象，不要输出任何解释、前后缀或 markdown 代码块标记。
    - JSON 必须且只能包含以下 6 个键，顺序为：id, name, age, gender, phone, email。
    - age 必须是 JSON 整数或 null；其余字段为字符串或 null。
    - 使用标准 JSON 双引号，不要使用中文引号。

    ## 示例

    输入：我叫张三丰，今年33岁，男，电话13800138000，邮箱zhangsanfeng@example.com，编号C001。
    输出：{"id": "C001", "name": "张三丰", "age": 33, "gender": "男", "phone": "13800138000", "email": "zhangsanfeng@example.com"}

    输入：客户李四，女，手机 139-1234-5678。
    输出：{"id": null, "name": "李四", "age": null, "gender": "女", "phone": "13912345678", "email": null}

    输入：今天天气不错。
    输出：{"id": null, "name": null, "age": null, "gender": null, "phone": null, "email": null}
    """
    # 4、构建请求对象
    messages: list = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(
        model=MODEL,  # 模型名称（在 .env 中配置）
        messages=messages,  # 提示词列表
        response_format = {"type": "json_object"}, # 如果要求AI必须输出JSON格式的结果，必须添加这个配置
        max_tokens=500  # 限制AI消费token的最大量
    )
    # 5、获取结果  这里result 是一段分离并且封装好的 json字符串
    result = response.choices[0].message.content

    # 5.1 处理一下这段json字符串   将JSON转换为字典对象
    customer_dict = json.loads(result)

    # 6、返回结果
    return customer_dict

# AI智能校验字段数据
def ai_check_customer_data(customer_dict):
    # 1、构建client对象
    client = get_client()

    # 2、构建system_prompt
    system_prompt = """你是一个智能字段校验助手。你的任务是检查用户提供的字段数据是否符合以下规则，并严格按照指定 JSON 格式返回校验结果。

    ## 待校验字段与规则
    用户会以 JSON 形式提供数据，包含字段：id, name, age, gender, phone, email。请逐字段校验：

    1. id：必须存在且不能为 null 或空字符串；必须是 3 到 6 位数字；首位不能为 0。
    2. name：必须存在且不能为 null 或空字符串；必须是 2 到 20 位中文或英文字符（可含汉字、英文字母，不含数字、空格及特殊符号）。
    3. age：必须存在且不能为 null 或空字符串；必须是 18 到 80 之间的整数（含 18 和 80）。
    4. gender：必须存在且不能为 null 或空字符串；只能是 "男" 或 "女"。
    5. phone：必须存在且不能为 null 或空字符串；必须是中国大陆 11 位手机号：以 1 开头，第二位为 3 到 9，共 11 位数字。
    6. email：必须存在且不能为 null 或空字符串；必须符合标准邮箱格式（形如 local@domain.tld，local 可含字母数字及 . _ % + -，domain 含字母数字及 -，顶级域名至少 2 个字母）。

    ## 校验原则
    - 每个字段都必须存在，缺失、null、空字符串均视为错误。
    - 对所有字段逐一检查，不要因为某个字段出错就跳过其他字段。
    - 严格按照上述规则判断，不要放宽或加严。
    - 不修改、不补全、不猜测用户数据。
    - 如果字段类型明显不对（如 age 是字符串 "abc"、phone 是数字而非字符串），按"格式不正确"处理。

    ## 错误文案规范
    每条错误使用固定格式："字段名：错误描述"。字段名用 id / name / age / gender / phone / email。参考文案：
    - "id：客户编号不能为空"
    - "id：客户编号必须是3到6位数字"
    - "id：客户编号首位不能为0"
    - "name：姓名不能为空"
    - "name：姓名必须是2到20位中文或英文"
    - "age：年龄不能为空"
    - "age：年龄必须是18到80之间的整数"
    - "gender：性别不能为空"
    - "gender：性别只能是男或女"
    - "phone：手机号不能为空"
    - "phone：手机号格式不正确"
    - "email：邮箱不能为空"
    - "email：邮箱格式不正确"

    ## 返回格式（严格遵守）
    - 只输出一个 JSON 对象，不要输出任何解释、前后缀或 markdown 代码块标记。
    - 必须且只能包含两个键：valid（布尔值）和 errors（字符串数组）。
    - 全部字段通过校验时：valid 为 true，errors 为空数组 []。
    - 存在任一错误时：valid 为 false，errors 列出所有错误文案（每个出错字段可有多条）。
    - errors 中不要出现重复文案。
    - 使用标准 JSON 双引号，不要使用中文引号。

    ## 示例

    输入：{"id": "1001", "name": "张三", "age": 28, "gender": "男", "phone": "13800138000", "email": "zhangsan@example.com"}
    输出：{"valid": true, "errors": []}

    输入：{"id": "", "name": "张三", "age": 28, "gender": "男", "phone": "12345678901", "email": "zhangsan@example.com"}
    输出：{"valid": false, "errors": ["id：客户编号不能为空", "phone：手机号格式不正确"]}

    输入：{"id": "0123", "name": "张", "age": 17, "gender": "", "phone": "13800138000", "email": "bad-email"}
    输出：{"valid": false, "errors": ["id：客户编号首位不能为0", "name：姓名必须是2到20位中文或英文", "age：年龄必须是18到80之间的整数", "gender：性别不能为空", "email：邮箱格式不正确"]}
    """

    # 3、构建messages 提示词列表
    messages:list = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(customer_dict)}
    ]
    # 4、构建请求对象
    response = client.chat.completions.create(
        model=MODEL,  # 模型名称（在 .env 中配置）
        messages=messages,  # 提示词列表
        response_format = {"type": "json_object"}, # 如果要求AI必须输出JSON格式的结果，必须添加这个配置
        max_tokens=500  # 限制AI消费token的最大量
    )
    # 5、获取响应结果
    result = response.choices[0].message.content
    # 6、将结果 JSON字符串 转换为 字典数据
    result_dict = json.loads(result)
    # 7、返回结果
    return result_dict

# question: 问题  customer_data：AI回答所调用 "知识库" 数据
def ai_chat(question,customer_data):
    # 1、构建client对象
    client = get_client()
    # 2、系统提示词
    system_prompt = """你是一个客户管理系统的智能助手。你的职责是回答用户关于客户的问题，并且所有回答必须严格基于系统提供的 customer_data（客户数据）。

    ## 回答规则
    1. 只回答与客户相关的问题。与客户无关的问题，直接回复：无法回答该问题，请联系人工客服...
    2. 回答内容必须完全来自 customer_data 中的数据，不得引入任何外部知识或假设。
    3. 严禁编造、推测、臆想客户数据中不存在的信息。数据中没有的内容，一律视为"不知道"。
    4. 如果用户的问题无法从 customer_data 中的信息得到回答（包括：问题涉及的数据字段不存在、数据为空/null、问题超出客户数据范围），直接回复：无法回答该问题，请联系人工客服...
    5. 不对客户数据做主观评价、推断或延伸（如根据年龄推测职业、根据电话推测地区等）。
    6. 如果问题涉及多个客户，只依据 customer_data 中对应客户的数据回答；若 customer_data 中不存在该客户，回复：无法回答该问题，请联系人工客服...
    7. 回答简洁直接，只陈述 customer_data 中的事实，不要添加解释性、推测性的内容。

    ## 数据说明
    - customer_data 会随用户消息一同提供，格式为 JSON，可能包含单个或多个客户的信息。
    - 字段可能包括：id、name、age、gender、phone、email 等。
    - 字段值为 null 或缺失，表示该信息不存在，不能当作已知信息使用。

    ## 回复格式
    - 正常回答：直接用自然语言陈述 customer_data 中的事实，简洁明了。
    - 无法回答时，固定回复：无法回答该问题，请联系人工客服...（不要添加其他内容）

    ## 示例

    customer_data：{"id": "1001", "name": "张三", "age": 28, "gender": "男", "phone": "13800138000", "email": "zhangsan@example.com"}

    用户：张三的电话是多少？
    回答：张三的电话是 13800138000。

    用户：张三的邮箱是什么？
    回答：张三的邮箱是 zhangsan@example.com。

    用户：张三的家庭住址是什么？
    回答：无法回答该问题，请联系人工客服...

    用户：张三的年龄是多少？他大概做什么工作？
    回答：张三的年龄是 28 岁。无法回答该问题，请联系人工客服...

    用户：帮我推荐一款手机。
    回答：无法回答该问题，请联系人工客服...
    """
    # 3、messages 提示词列表
    messages: list = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"question={question},customer_data={json.dumps(customer_data, ensure_ascii=False)}"}
    ]
    # 4、构建请求对象
    response = client.chat.completions.create(
        model=MODEL,  # 模型名称（在 .env 中配置）
        messages=messages,  # 提示词列表
        max_tokens=500  # 限制AI消费token的最大量
    )
    # 5、获取结果
    return response.choices[0].message.content


if __name__ == "__main__":
    # 只打印掩码，避免密钥出现在日志或截图里
    if API_KEY:
        print("API_KEY:", API_KEY[:6] + "****" + API_KEY[-4:])
    else:
        print("API_KEY: 未配置，请在 .env 中填写 DEEPSEEK_API_KEY")
    print("BASE_URL:", BASE_URL)
    print("MODEL:", MODEL)
    # text = input("请输入一段文本：")
    # ans = ai_extract_customer_data(text)
    #
    # # 直接将 第一步的结果给第二步 做智能校验
    # result = ai_check_customer_data(ans)
    # print(result)