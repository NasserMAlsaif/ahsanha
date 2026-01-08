import os
import json

DATA_PATH = os.path.join(os.path.dirname(__file__), "product_data.json")

def _load_products():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _matches(item: dict, filters: dict) -> bool:
    # فلاتر بسيطة جدًا للـ MVP
    for k, v in (filters or {}).items():
        if k not in item:
            continue

        item_val = item.get(k)

        # multi-select: v قد تكون list
        if isinstance(v, list):
            if item_val not in v:
                return False
        else:
            # range للسعر: price_min, price_max
            if k == "price_min":
                try:
                    if float(item.get("price", 0)) < float(v):
                        return False
                except:
                    pass
            elif k == "price_max":
                try:
                    if float(item.get("price", 0)) > float(v):
                        return False
                except:
                    pass
            else:
                # نص مطابق بسيط
                if str(item_val).lower() != str(v).lower():
                    return False

    return True

def search_products(domain: str, filters: dict):
    # الآن ندعم فقط product.* من نفس ملف البيانات
    products = _load_products()

    # فلترة بحسب domain إن كان موجود بالحقل
    filtered = [p for p in products if p.get("domain") == domain]

    # طبق فلاتر إضافية
    out = []
    for item in filtered:
        if _matches(item, filters):
            out.append(item)

    # ترتيب افتراضي بسيط: الأرخص أولًا
    out.sort(key=lambda x: x.get("price", 10**18))
    return out
