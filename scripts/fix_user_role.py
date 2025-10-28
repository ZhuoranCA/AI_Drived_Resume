from pymongo import MongoClient

# 连接本地 MongoDB
client = MongoClient("mongodb://localhost:27017")

# 连接你项目使用的 user 数据库
db = client["user_db"]       # ✅ 按你当前代码来，这里用 user_db
users = db["users"]          # 集合名为 users

# 查找并补齐缺失 role 字段的用户
result = users.update_many(
    {"role": {"$exists": False}},
    {"$set": {"role": "user"}}
)

print(f"✅ Updated {result.modified_count} user documents in 'user_db.users'")
