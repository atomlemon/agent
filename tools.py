import csv
import random
from langchain_core.tools import tool
import datetime
from pathlib import Path
import pandas as pd


@tool
def search_products(query:str):
    """
    模糊搜索商品信息
    :param query: 搜索关键词（类别或款式名称）
    :return: 匹配的商品列表（最多10条）
    """
    csv_path = Path(__file__).parent / 'source' / 'products.csv'
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)  # DictReader 自动用第一行做表头，不需要 next()
        try:
            products_list = []
            for row in reader:
                if query in row["类别"] or query in row["款式名称"] or query in row["货号"]:
                    reserve = int(row["库存数量"])
                    price = int(row["单价"])
                    days = int(row["补货天数"])
                    goods_type = row["类别"]
                    product = {
                        "product_id": row["货号"],
                        "name": row["款式名称"],
                        "color": row["颜色"],
                        "size": row["尺码"],
                        "picture": row["图片文件"],
                        "stock": reserve,
                        "price": price,
                        "restock_days": days,
                        "goods_type": goods_type
                         }
                    products_list.append(product)
                    if len(products_list) >= 10:
                        break
            if products_list:
                return {"status": "ok", "products": products_list}
            else:
                # 循环跑完没找到匹配 → 才返回无此商品
                return {"status": "not_found", "message": "无此商品"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@tool
def get_goods_info(product_id:str, color:str, size:str)  -> dict:
    """
    从 csv 文件中读取商品信息
    :param product_id: 商品货号
    :param color: 商品颜色
    :param size: 商品尺码
    :return: 商品信息
    """
    csv_path = Path(__file__).parent / 'source' / 'products.csv'
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)  # DictReader 自动用第一行做表头，不需要 next()
        try:
            for row in reader:
                if (row["货号"] == product_id
                        and row["颜色"] == color
                        and row["尺码"] == size):
                    reserve = int(row["库存数量"])
                    price = int(row["单价"])
                    days = int(row["补货天数"])
                    goods_type = row["类别"]
                    return {"status": "ok",
                            "product_id": row["货号"],
                            "name": row["款式名称"],
                            "color": row["颜色"],
                            "size": row["尺码"],
                            "picture": row["图片文件"],
                            "stock": reserve,
                            "price": price,
                            "restock_days": days,
                            "goods_type": goods_type
                            }
            # 循环跑完没找到匹配 → 才返回无此商品
            return {"status": "not_found", "message": "无此商品"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@tool
def get_shipping_info(
    recipient: str,
    phone: str,
    address: str,
    products: list  # [{"product_id": "A009", "color": "驼色", "size": "均码"}, ...]
) -> dict:
    """
    收集收货信息，创建订单（支持多件商品）
    :param recipient: 收货人姓名
    :param phone: 收货人电话
    :param address: 收货人地址
    :param products: 商品列表，每件商品包含 product_id, color, size
    :return: 订单信息
    """

    # 生成订单号（微秒级时间戳 + 随机数，避免同一秒多商品碰撞）
    order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + str(random.randint(100, 999))
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建多行订单数据（每件商品一行）
    rows = []
    for product in products:
        rows.append({
            "订单号": order_id,
            "下单时间": now_time,
            "收货人": recipient,
            "收货电话": phone,
            "收货地址": address,
            "商品货号": product["product_id"],
            "商品颜色": product["color"],
            "商品尺码": product["size"],
            "状态": "待发货"  # 新增
        })

    new_orders = pd.DataFrame(rows)
    csv_path = Path(__file__).parent / 'source' / 'order.csv'

    if csv_path.exists():
        existing_df = pd.read_csv(csv_path)
        combined = pd.concat([existing_df, new_orders], ignore_index=True)
        combined.to_csv(csv_path, index=False, encoding='utf-8')
    else:
        new_orders.to_csv(csv_path, index=False, encoding='utf-8')

    # 生成商品摘要
    product_summary = "、".join([f"{p['product_id']}({p['color']}/{p['size']})" for p in products])

    return {
        "status": "ok",
        "message": f"订单创建成功！订单号：{order_id}\n商品：{product_summary}\n共{len(products)}件，合计请自行计算"
    }

@tool
def control_stock(
    items: list,
    operation: str = "reduce"
) -> dict:
    """
    批量更新商品库存（下单减库存，退货加库存）
    :param items: 商品列表，每件商品包含 product_id, color, size, quantity
                  例如：[{"product_id": "A002", "color": "米白", "size": "M", "quantity": 1}, ...]
    :param operation: 操作类型，"reduce"减库存，"increase"加库存
    :return: 最终库存结果
    """
    csv_path = Path(__file__).parent / 'source' / 'products.csv'
    if not csv_path.exists():
        return {"status": "error", "message": "库存文件不存在"}

    products_df = pd.read_csv(csv_path)
    results = []
    all_success = True

    for item in items:
        product_id = item["product_id"]
        color = item["color"]
        size = item["size"]
        quantity = item.get("quantity", 1)

        # 找到匹配行
        mask = (products_df["货号"] == product_id) & \
               (products_df["颜色"] == color) & \
               (products_df["尺码"] == size)

        if not mask.any():
            results.append(f"❌ 未找到商品：{product_id} {color} {size}")
            all_success = False
            continue

        current_stock = products_df.loc[mask, "库存数量"].values[0]

        if operation == "reduce":
            if current_stock < quantity:
                results.append(f"❌ {product_id} {color} {size} 库存不足（当前 {current_stock}，需要 {quantity}）")
                all_success = False
                continue
            products_df.loc[mask, "库存数量"] = current_stock - quantity
            results.append(f"✅ {product_id} {color} {size} 减 {quantity}，剩余 {current_stock - quantity}")

        elif operation == "increase":
            products_df.loc[mask, "库存数量"] = current_stock + quantity
            results.append(f"✅ {product_id} {color} {size} 加 {quantity}，现有 {current_stock + quantity}")

        else:
            results.append(f"❌ 未知操作：{operation}")
            all_success = False

    # 保存（只要有一件成功就保存，避免重复读取）
    if results:
        products_df.to_csv(csv_path, index=False, encoding='utf-8')

    return {
        "status": "ok" if all_success else "partial",
        "message": "\n".join(results)
    }


@tool
def query_order(identifier: str) -> dict:
    """
    根据订单号或手机号查询订单状态
    :param identifier: 订单号 或 收货人手机号
    :return: 订单信息，包含状态、商品列表等
    """
    csv_path = Path(__file__).parent / 'source' / 'order.csv'
    if not csv_path.exists():
        return {"status": "error", "message": "订单文件不存在"}

    df = pd.read_csv(csv_path)

    df["订单号"] = df["订单号"].astype(str)
    df["收货电话"] = df["收货电话"].astype(str)
    identifier = str(identifier)

    # 筛选匹配的行
    mask = (df["订单号"] == identifier) | (df["收货电话"] == identifier)
    result_df = df[mask]

    if result_df.empty:
        return {"status": "error", "message": f"未找到订单：{identifier}"}

    # 按订单号分组，合并多件商品
    orders = []
    for order_id, group in result_df.groupby("订单号"):
        # 取第一行作为订单基础信息（收货人、地址等）
        first = group.iloc[0]
        items = []
        for _, row in group.iterrows():
            items.append({
                "product_id": row["商品货号"],
                "color": row["商品颜色"],
                "size": row["商品尺码"]
            })

        orders.append({
            "order_id": order_id,
            "status": first.get("状态", "未知"),  # 如果没有状态列，默认“未知”
            "order_time": first["下单时间"],
            "recipient": first["收货人"],
            "phone": first["收货电话"],
            "address": first["收货地址"],
            "items": items,
            "total_items": len(items)
        })

    return {
        "status": "ok",
        "orders": orders
    }


















