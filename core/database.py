# -*- coding: utf-8 -*-
"""本地多用户数据库：用户表 + 历史记录表（增删查改）"""
import hashlib
import json
import os
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "tool.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash(pwd: str) -> str:
    return hashlib.sha256(("vft$" + pwd).encode("utf-8")).hexdigest()


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pwd_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT,
            last_login TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            video_name TEXT,
            video_path TEXT,
            preset_name TEXT,
            threshold REAL,
            frame_count INTEGER,
            out_ppt TEXT DEFAULT '',
            out_gif TEXT DEFAULT '',
            out_dir TEXT,
            cost_sec REAL,
            params_json TEXT,
            created_at TEXT)""")
        # 首次启动创建默认管理员 admin/admin123
        row = c.execute("SELECT COUNT(*) n FROM users").fetchone()
        if row["n"] == 0:
            c.execute("INSERT INTO users(username,pwd_hash,role,created_at) VALUES(?,?,?,?)",
                      ("admin", _hash("admin123"), "admin",
                       time.strftime("%Y-%m-%d %H:%M:%S")))


# ---------------- 用户管理（增删查改） ----------------

def verify_user(username: str, password: str):
    with _conn() as c:
        r = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if r and r["pwd_hash"] == _hash(password):
            c.execute("UPDATE users SET last_login=? WHERE id=?",
                      (time.strftime("%Y-%m-%d %H:%M:%S"), r["id"]))
            return dict(r)
    return None


def list_users():
    with _conn() as c:
        rows = c.execute("SELECT id,username,role,created_at,last_login FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def add_user(username: str, password: str, role: str = "user") -> str:
    if not username.strip() or not password:
        return "用户名或密码不能为空"
    with _conn() as c:
        exist = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if exist:
            return "用户名已存在"
        c.execute("INSERT INTO users(username,pwd_hash,role,created_at) VALUES(?,?,?,?)",
                  (username.strip(), _hash(password), role,
                   time.strftime("%Y-%m-%d %H:%M:%S")))
    return "ok"


def delete_user(user_id: int) -> str:
    with _conn() as c:
        r = c.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
        if not r:
            return "用户不存在"
        if r["role"] == "admin" and c.execute(
                "SELECT COUNT(*) n FROM users WHERE role='admin'").fetchone()["n"] <= 1:
            return "不能删除最后一个管理员"
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
    return "ok"


def reset_password(user_id: int, new_pwd: str) -> str:
    if not new_pwd:
        return "密码不能为空"
    with _conn() as c:
        c.execute("UPDATE users SET pwd_hash=? WHERE id=?", (_hash(new_pwd), user_id))
    return "ok"


def change_role(user_id: int, role: str) -> str:
    with _conn() as c:
        c.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    return "ok"


def change_own_password(user_id: int, old_pwd: str, new_pwd: str) -> str:
    with _conn() as c:
        r = c.execute("SELECT pwd_hash FROM users WHERE id=?", (user_id,)).fetchone()
        if not r or r["pwd_hash"] != _hash(old_pwd):
            return "原密码错误"
        c.execute("UPDATE users SET pwd_hash=? WHERE id=?", (_hash(new_pwd), user_id))
    return "ok"


# ---------------- 历史记录（增删查改） ----------------

def add_history(user_id, video_name, video_path, preset_name, threshold,
                frame_count, out_ppt, out_gif, out_dir, cost_sec, params: dict):
    with _conn() as c:
        c.execute("""INSERT INTO history(user_id,video_name,video_path,preset_name,threshold,
                     frame_count,out_ppt,out_gif,out_dir,cost_sec,params_json,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (user_id, video_name, video_path, preset_name, threshold,
                   frame_count, out_ppt, out_gif, out_dir, cost_sec,
                   json.dumps(params, ensure_ascii=False),
                   time.strftime("%Y-%m-%d %H:%M:%S")))


def list_history(user_id=None, limit=300):
    with _conn() as c:
        if user_id is None:  # 管理员看全部
            rows = c.execute("SELECT h.*,u.username FROM history h LEFT JOIN users u "
                             "ON u.id=h.user_id ORDER BY h.id DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = c.execute("SELECT h.*,u.username FROM history h LEFT JOIN users u "
                             "ON u.id=h.user_id WHERE h.user_id=? ORDER BY h.id DESC LIMIT ?",
                             (user_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_history(hid: int):
    with _conn() as c:
        r = c.execute("SELECT * FROM history WHERE id=?", (hid,)).fetchone()
        return dict(r) if r else None


def delete_history(hid: int):
    with _conn() as c:
        c.execute("DELETE FROM history WHERE id=?", (hid,))


def update_history(hid: int, **fields):
    """允许修改备注性字段（如输出路径），供记录管理使用"""
    allow = {"out_ppt", "out_gif", "out_dir"}
    keys = [k for k in fields if k in allow]
    if not keys:
        return
    with _conn() as c:
        for k in keys:
            c.execute(f"UPDATE history SET {k}=? WHERE id=?", (fields[k], hid))


# 模块导入即确保库表就绪
init_db()
