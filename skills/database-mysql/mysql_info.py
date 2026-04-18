#!/usr/bin/env python3
"""
MySQL 数据库信息查询工具
用法:
  python3 mysql_info.py --host HOST --user USER --password PASS [选项]

选项:
  --host HOST          数据库主机地址
  --port PORT          端口号 (默认 3306)
  --user USER          用户名
  --password PASS      密码
  --database DB        指定数据库 (不填则列出所有数据库)
  --sql "SELECT ..."   执行自定义 SQL (需同时指定 --database)
  --no-rows            跳过行数统计 (大表时加快速度)
"""

import argparse
import sys

def ensure_pymysql():
    try:
        import pymysql
        return pymysql
    except ImportError:
        print("正在安装 PyMySQL...", flush=True)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMySQL", "-q"])
        import pymysql
        return pymysql

def connect(pymysql, host, port, user, password, database=None):
    return pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )

def get_basic_info(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION() as version")
        version = cur.fetchone()['version']
        cur.execute("SELECT USER() as user")
        current_user = cur.fetchone()['user']
        cur.execute("SELECT @@hostname as hostname, @@port as port, @@character_set_server as charset")
        server_info = cur.fetchone()
        cur.execute("SHOW DATABASES")
        databases = [list(row.values())[0] for row in cur.fetchall()]
    return {
        "version": version,
        "user": current_user,
        "server": server_info,
        "databases": databases,
    }

def get_table_info(conn, database, count_rows=True):
    tables_info = []
    with conn.cursor() as cur:
        cur.execute(f"USE `{database}`")

        # 通过 information_schema 获取表基本信息（更快）
        cur.execute("""
            SELECT
                TABLE_NAME as name,
                TABLE_ROWS as approx_rows,
                DATA_LENGTH as data_bytes,
                TABLE_COMMENT as comment,
                ENGINE as engine,
                CREATE_TIME as created
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """, (database,))
        tables = cur.fetchall()

        for table in tables:
            tname = table['name']

            # 获取列信息
            cur.execute(f"DESCRIBE `{tname}`")
            columns = cur.fetchall()

            row_count = None
            if count_rows:
                try:
                    cur.execute(f"SELECT COUNT(*) as cnt FROM `{tname}`")
                    row_count = cur.fetchone()['cnt']
                except Exception:
                    row_count = table.get('approx_rows', '?')

            tables_info.append({
                "name": tname,
                "rows": row_count if row_count is not None else table.get('approx_rows', '?'),
                "engine": table.get('engine', ''),
                "comment": table.get('comment', ''),
                "columns": columns,
            })

    return tables_info

def fmt_num(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)

def print_basic_info(info):
    print(f"\n{'='*60}")
    print(f"  MySQL 连接成功")
    print(f"{'='*60}")
    print(f"  版本      : {info['version']}")
    print(f"  当前用户  : {info['user']}")
    host = info['server'].get('hostname', '')
    port = info['server'].get('port', '')
    charset = info['server'].get('charset', '')
    print(f"  服务器    : {host}:{port}  字符集: {charset}")
    dbs = info['databases']
    sys_dbs = {'information_schema', 'performance_schema', 'mysql', 'sys'}
    user_dbs = [d for d in dbs if d not in sys_dbs]
    print(f"\n  数据库列表 ({len(dbs)} 个, 其中用户库 {len(user_dbs)} 个):")
    for db in dbs:
        tag = "  [系统]" if db in sys_dbs else ""
        print(f"    - {db}{tag}")

def print_table_info(database, tables):
    print(f"\n{'='*60}")
    print(f"  数据库 [{database}]  共 {len(tables)} 张表")
    print(f"{'='*60}")
    if not tables:
        print("  (无表)")
        return

    name_w = max(len(t['name']) for t in tables)
    for t in tables:
        cols = [c['Field'] for c in t['columns']]
        col_types = {c['Field']: c['Type'] for c in t['columns']}
        print(f"\n  {t['name']:<{name_w}}  |  {fmt_num(t['rows'])} 行  |  引擎: {t.get('engine','')}")
        if t.get('comment'):
            print(f"    备注: {t['comment']}")
        for col in t['columns']:
            key_mark = " [PK]" if col.get('Key') == 'PRI' else ""
            null_mark = "" if col.get('Null') == 'NO' else " nullable"
            default = f"  default={col['Default']}" if col.get('Default') is not None else ""
            print(f"    {col['Field']:<20} {col['Type']:<25}{key_mark}{null_mark}{default}")

def run_custom_sql(conn, sql, database=None):
    with conn.cursor() as cur:
        if database:
            cur.execute(f"USE `{database}`")
        cur.execute(sql)
        rows = cur.fetchall()
    if not rows:
        print("(无结果)")
        return
    headers = list(rows[0].keys())
    widths = [max(len(str(h)), max(len(str(r.get(h, ''))) for r in rows)) for h in headers]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_row = "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |"
    print(sep)
    print(header_row)
    print(sep)
    for row in rows:
        print("| " + " | ".join(str(row.get(h, '')).ljust(w) for h, w in zip(headers, widths)) + " |")
    print(sep)
    print(f"共 {len(rows)} 行")

def main():
    parser = argparse.ArgumentParser(description="MySQL 数据库信息查询工具")
    parser.add_argument("--host", required=True, help="数据库主机")
    parser.add_argument("--port", default=3306, type=int, help="端口 (默认 3306)")
    parser.add_argument("--user", required=True, help="用户名")
    parser.add_argument("--password", required=True, help="密码")
    parser.add_argument("--database", default=None, help="指定数据库名")
    parser.add_argument("--sql", default=None, help="执行自定义 SQL")
    parser.add_argument("--no-rows", action="store_true", help="跳过行数统计")
    args = parser.parse_args()

    pymysql = ensure_pymysql()

    try:
        conn = connect(pymysql, args.host, args.port, args.user, args.password, args.database)
    except Exception as e:
        print(f"\n连接失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.sql:
            run_custom_sql(conn, args.sql, args.database)
        else:
            info = get_basic_info(conn)
            print_basic_info(info)

            if args.database:
                tables = get_table_info(conn, args.database, count_rows=not args.no_rows)
                print_table_info(args.database, tables)
            else:
                print("\n提示: 使用 --database 库名 查看表详情")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
