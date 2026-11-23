# -*- coding: utf-8 -*-
"""data/ 의 parquet 에서 표 설명(schema.json)을 만든다.

    python tools/make_schema.py

- 열 이름·자료형은 parquet 에서 읽는다
- 종류가 12가지 이하인 글자 열은 값 목록을 함께 적는다 (AI가 SQL을 쓸 때 쓴다)
- **한 줄이 무엇인지(그레인)는 사람이 정한 것**이다
"""
import io
import json
import os

import duckdb

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

GRAIN = {
    "employees": "직원 1명", "trips": "출장 1건", "expenses": "출장 1건의 비용 항목 1개",
}
SKIP_VALUES = set()


def main():
    con = duckdb.connect()
    out = {"note": "한 줄이 무엇인지(grain)는 사람이 정한 것입니다. 조인하기 전에 반드시 봅니다.", "tables": {}}
    for f in sorted(os.listdir(DATA)):
        if not f.endswith(".parquet"):
            continue
        t = f[:-8]
        path = os.path.join(DATA, f).replace("\\", "/")
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{path}')").fetchone()[0]
        cols = []
        for name, typ, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchall():
            c = {"name": name, "type": typ}
            if typ == "VARCHAR" and name not in SKIP_VALUES:
                vals = con.execute(f"SELECT DISTINCT {name} FROM read_parquet('{path}') "
                                   f"WHERE {name} IS NOT NULL ORDER BY 1 LIMIT 13").fetchall()
                if len(vals) <= 12:
                    c["values"] = [v[0] for v in vals]
            cols.append(c)
        out["tables"][t] = {"grain": GRAIN[t], "rows": n, "columns": cols}
    io.open(os.path.join(HERE, "schema.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"표 {len(out['tables'])}개 · 전체 {sum(v['rows'] for v in out['tables'].values()):,}행")


if __name__ == "__main__":
    main()
