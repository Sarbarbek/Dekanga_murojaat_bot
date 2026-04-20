import asyncpg
from typing import Optional, Tuple, List, Any, Dict
from datetime import datetime, timezone, timedelta
from app.time_sync import now_utc5, get_now_utc5_str

def get_now_utc5() -> str:
    """Hozirgi vaqtni UTC+5 formatida qaytaradi."""
    return get_now_utc5_str()

class Database:
    def __init__(self, host: str, user: str, password: str, db: str, port: int = 5432, dsn: Optional[str] = None) -> None:
        self._host = host
        self._user = user
        self._password = password
        self._db = db
        self._port = port
        self._dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        if self._dsn:
            self.pool = await asyncpg.create_pool(dsn=self._dsn)
        else:
            self.pool = await asyncpg.create_pool(
                host=self._host,
                user=self._user,
                password=self._password,
                database=self._db,
                port=self._port
            )
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS murojaatlar (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    passport VARCHAR(50),
                    phone VARCHAR(50),
                    group_name VARCHAR(255) NOT NULL,
                    department_key VARCHAR(50),  -- 'kun', 'kech', 'mag', 'sirt'
                    body_text TEXT,
                    file_id VARCHAR(255),
                    file_type VARCHAR(50) NOT NULL DEFAULT 'text',
                    status VARCHAR(50) NOT NULL DEFAULT 'new',
                    answer_text TEXT,
                    answered_by BIGINT,
                    created_at TIMESTAMP NOT NULL,
                    answered_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    full_name VARCHAR(255),
                    username VARCHAR(255),
                    created_at TIMESTAMP NOT NULL
                );
                """
            )
            
            # Column checks
            for col, col_type in [("passport", "VARCHAR(50)"), ("phone", "VARCHAR(50)"), ("department_key", "VARCHAR(50)")]:
                col_exists = await conn.fetchval(
                    f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='murojaatlar' AND column_name='{col}')"
                )
                if not col_exists:
                    await conn.execute(f"ALTER TABLE murojaatlar ADD COLUMN {col} {col_type}")

            username_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='username')"
            )
            if not username_exists:
                await conn.execute("ALTER TABLE users ADD COLUMN username VARCHAR(255)")

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    def _get_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database pool is not initialized. Call init() first.")
        return self.pool

    async def create_murojaat(
        self,
        *,
        user_id: int,
        full_name: str,
        passport: str,
        phone: str,
        group_name: str,
        department_key: str,
        body_text: Optional[str],
        file_id: Optional[str],
        file_type: str,
    ) -> int:
        now = now_utc5().replace(tzinfo=None)
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO murojaatlar (user_id, full_name, passport, phone, group_name, department_key, body_text, file_id, file_type, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                user_id, full_name, passport, phone, group_name, department_key, body_text, file_id, file_type, now,
            )
            return row['id']

    async def get_murojaat_owner(self, appeal_id: int) -> Optional[int]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            user_id = await conn.fetchval(
                "SELECT user_id FROM murojaatlar WHERE id = $1",
                appeal_id,
            )
            return user_id

    async def get_murojaat_info(self, appeal_id: int) -> Optional[dict]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, department_key FROM murojaatlar WHERE id = $1",
                appeal_id,
            )
            return dict(row) if row else None

    async def set_answer(self, *, appeal_id: int, answer_text: str, answered_by: int) -> bool:
        now = now_utc5().replace(tzinfo=None)
        pool = self._get_pool()
        async with pool.acquire() as conn:
            status = await conn.execute(
                """
                UPDATE murojaatlar
                SET status = 'answered', answer_text = $1, answered_by = $2, answered_at = $3
                WHERE id = $4 AND status = 'new'
                """,
                answer_text, answered_by, now, appeal_id,
            )
            return status == "UPDATE 1"

    async def list_user_murojaatlar(self, user_id: int, limit: int = 5) -> List[Tuple[int, str, str]]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, status, created_at
                FROM murojaatlar
                WHERE user_id = $1
                ORDER BY id DESC
                LIMIT $2
                """,
                user_id, limit,
            )
            return [(r['id'], r['status'], r['created_at'].strftime("%Y-%m-%d %H:%M:%S")) for r in rows]

    async def list_murojaatlar_by_status(
        self,
        *,
        status: str,
        department_key: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Tuple[int, int, str, str, str, str, str]]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            query = "SELECT m.id, m.user_id, m.full_name, m.group_name, m.created_at, COALESCE(m.body_text, '') AS body_text, u.username FROM murojaatlar m LEFT JOIN users u ON m.user_id = u.user_id WHERE m.status = $1"
            args: List[Any] = [status]
            
            if department_key and department_key not in ("total", "all"):
                query += " AND m.department_key = $2"
                args.append(department_key)
                limit_idx = 3
                offset_idx = 4
            else:
                limit_idx = 2
                offset_idx = 3
            
            query += f" ORDER BY m.id DESC LIMIT ${limit_idx} OFFSET ${offset_idx}"
            args.extend([limit, offset])

            rows = await conn.fetch(query, *args)
            return [
                (r['id'], r['user_id'], r['full_name'], r['group_name'], r['created_at'].strftime("%Y-%m-%d %H:%M:%S"), r['body_text'], r['username'] or "")
                for r in rows
            ]

    async def export_murojaatlar(
        self,
        *,
        status: str,
        department_key: Optional[str] = None,
        limit: int = 5000,
    ) -> List[Tuple]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT m.id, m.user_id, m.full_name, m.passport, m.phone, m.group_name, m.department_key, m.created_at, m.answered_at, m.status, 
                       COALESCE(m.body_text, '') AS body_text, COALESCE(m.answer_text, '') AS answer_text,
                       u.username
                FROM murojaatlar m
                LEFT JOIN users u ON m.user_id = u.user_id
            """
            args: List[Any] = []
            conditions = []
            
            if status != "all":
                args.append(status)
                conditions.append(f"m.status = ${len(args)}")
            if department_key and department_key not in ("total", "all"):
                args.append(department_key)
                conditions.append(f"m.department_key = ${len(args)}")
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            args.append(limit)
            query += f" ORDER BY m.id ASC LIMIT ${len(args)}"

            rows = await conn.fetch(query, *args)
            
            return [
                (
                    r['id'],
                    r['user_id'],
                    r['username'] or "",
                    r['full_name'],
                    r['passport'] or "",
                    r['phone'] or "",
                    r['group_name'],
                    r['department_key'] or "",
                    r['created_at'].strftime("%Y-%m-%d %H:%M:%S") if r['created_at'] else "",
                    r['answered_at'].strftime("%Y-%m-%d %H:%M:%S") if r['answered_at'] else "",
                    r['status'],
                    r['body_text'],
                    r['answer_text']
                )
                for r in rows
            ]

    async def get_murojaat_brief(
        self, appeal_id: int
    ) -> Optional[Tuple[int, str, str, str, str, Optional[str], str, str, str]]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, full_name, group_name, COALESCE(body_text, '') AS body_text, file_type, file_id, status, created_at, department_key
                FROM murojaatlar
                WHERE id = $1
                """,
                appeal_id,
            )
            if not row:
                return None
            return (
                row['user_id'],
                row['full_name'],
                row['group_name'],
                row['body_text'],
                row['file_type'],
                row['file_id'],
                row['status'],
                row['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
                row['department_key'] or ""
            )

    async def get_statistics(self, department_key: Optional[str] = None) -> dict:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            filter_sql = ""
            args = []
            if department_key and department_key not in ("total", "all"):
                filter_sql = " WHERE department_key = $1"
                args.append(department_key)
            
            row = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*),
                    SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'answered' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN created_at::DATE = CURRENT_DATE THEN 1 ELSE 0 END),
                    SUM(CASE WHEN created_at::DATE = CURRENT_DATE AND status = 'new' THEN 1 ELSE 0 END)
                FROM murojaatlar {filter_sql}
            """, *args)
            
            if not row:
                return {"total": 0, "new_count": 0, "answered_count": 0, "today_total": 0, "today_new": 0}
            
            return {
                "total": row[0] or 0,
                "new_count": int(row[1] or 0),
                "answered_count": int(row[2] or 0),
                "today_total": int(row[3] or 0),
                "today_new": int(row[4] or 0)
            }

    async def search_murojaatlar(
        self,
        *,
        query: str,
        department_key: Optional[str] = None,
        limit: int = 20,
    ) -> List[Tuple[int, int, str, str, str, str, str]]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            search_query = f"%{query}%"
            sql = """
                SELECT id, user_id, full_name, group_name, created_at, status, COALESCE(body_text, '') AS body_text
                FROM murojaatlar
                WHERE (full_name ILIKE $1 OR group_name ILIKE $1 OR body_text ILIKE $1)
            """
            args: List[Any] = [search_query]
            if department_key and department_key not in ("total", "all"):
                sql += " AND department_key = $2"
                args.append(department_key)
                limit_idx = 3
            else:
                limit_idx = 2
            
            sql += f" ORDER BY id DESC LIMIT ${limit_idx}"
            args.append(limit)

            rows = await conn.fetch(sql, *args)
            return [
                (r['id'], r['user_id'], r['full_name'], r['group_name'], r['created_at'].strftime("%Y-%m-%d %H:%M:%S"), r['status'], r['body_text'])
                for r in rows
            ]

    async def update_user(self, user_id: int, full_name: Optional[str] = None, username: Optional[str] = None) -> None:
        now = now_utc5().replace(tzinfo=None)
        pool = self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, full_name, created_at, username)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET full_name = EXCLUDED.full_name, username = EXCLUDED.username
                """,
                user_id, full_name, now, username
            )

    async def get_users_list(self, department_key: str, offset: int = 0, limit: int = 30) -> Tuple[List[dict], int, int]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            if department_key in ("total", "all"):
                total_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                phone_count = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM murojaatlar WHERE phone IS NOT NULL AND phone != ''")
                
                rows = await conn.fetch(
                    """
                    SELECT u.user_id, u.full_name, u.username, u.created_at,
                           (SELECT m.phone FROM murojaatlar m WHERE m.user_id = u.user_id AND m.phone IS NOT NULL AND m.phone != '' ORDER BY m.id DESC LIMIT 1) as phone
                    FROM users u
                    ORDER BY u.created_at DESC
                    LIMIT $1 OFFSET $2
                    """, limit, offset
                )
            else:
                total_count = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM murojaatlar WHERE department_key = $1", department_key)
                phone_count = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM murojaatlar WHERE department_key = $1 AND phone IS NOT NULL AND phone != ''", department_key)
                
                rows = await conn.fetch(
                    """
                    SELECT u.user_id, u.full_name, u.username, u.created_at,
                           (SELECT m.phone FROM murojaatlar m WHERE m.user_id = u.user_id AND m.department_key = $1 AND m.phone IS NOT NULL AND m.phone != '' ORDER BY m.id DESC LIMIT 1) as phone
                    FROM users u
                    INNER JOIN (SELECT DISTINCT user_id FROM murojaatlar WHERE department_key = $1) as deps ON u.user_id = deps.user_id
                    ORDER BY u.created_at DESC
                    LIMIT $2 OFFSET $3
                    """, department_key, limit, offset
                )
            
            result = []
            for r in rows:
                result.append({
                    "user_id": r["user_id"],
                    "full_name": r["full_name"],
                    "username": r["username"],
                    "phone": r["phone"],
                    "created_at": r["created_at"]
                })
            return result, total_count, phone_count

    async def get_all_users_count(self) -> int:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")

    async def get_all_user_ids(self) -> List[int]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users")
            return [r['user_id'] for r in rows]

    async def get_full_backup(self) -> Dict[str, List[Dict[str, Any]]]:
        """Barcha ma'lumotlarni JSON formatda eksport qilish uchun qaytaradi."""
        pool = self._get_pool()
        async with pool.acquire() as conn:
            users_rows = await conn.fetch("SELECT * FROM users")
            murojaatlar_rows = await conn.fetch("SELECT * FROM murojaatlar")
            
            users = []
            for r in users_rows:
                d = dict(r)
                if d.get('created_at'): d['created_at'] = d['created_at'].isoformat()
                users.append(d)
                
            murojaatlar = []
            for r in murojaatlar_rows:
                d = dict(r)
                if d.get('created_at'): d['created_at'] = d['created_at'].isoformat()
                if d.get('answered_at'): d['answered_at'] = d['answered_at'].isoformat()
                murojaatlar.append(d)
                
            return {
                "users": users,
                "murojaatlar": murojaatlar
            }

    async def restore_full_backup(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """JSON backupdan ma'lumotlarni tiklash."""
        pool = self._get_pool()
        users_count = 0
        murojaatlar_count = 0
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Users restoration
                for u in data.get("users", []):
                    created_at = datetime.fromisoformat(u['created_at']) if u.get('created_at') else now_utc5().replace(tzinfo=None)
                    await conn.execute(
                        """
                        INSERT INTO users (user_id, full_name, username, created_at)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (user_id) DO UPDATE SET 
                            full_name = EXCLUDED.full_name, 
                            username = EXCLUDED.username,
                            created_at = EXCLUDED.created_at
                        """,
                        u['user_id'], u['full_name'], u['username'], created_at
                    )
                    users_count += 1
                
                # Murojaatlar restoration
                for m in data.get("murojaatlar", []):
                    created_at = datetime.fromisoformat(m['created_at']) if m.get('created_at') else now_utc5().replace(tzinfo=None)
                    answered_at = datetime.fromisoformat(m['answered_at']) if m.get('answered_at') else None
                    
                    await conn.execute(
                        """
                        INSERT INTO murojaatlar (
                            id, user_id, full_name, passport, phone, group_name, department_key, 
                            body_text, file_id, file_type, status, answer_text, answered_by, 
                            created_at, answered_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                        ON CONFLICT (id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            full_name = EXCLUDED.full_name,
                            passport = EXCLUDED.passport,
                            phone = EXCLUDED.phone,
                            group_name = EXCLUDED.group_name,
                            department_key = EXCLUDED.department_key,
                            body_text = EXCLUDED.body_text,
                            file_id = EXCLUDED.file_id,
                            file_type = EXCLUDED.file_type,
                            status = EXCLUDED.status,
                            answer_text = EXCLUDED.answer_text,
                            answered_by = EXCLUDED.answered_by,
                            created_at = EXCLUDED.created_at,
                            answered_at = EXCLUDED.answered_at
                        """,
                        m['id'], m['user_id'], m['full_name'], m.get('passport'), m.get('phone'), m['group_name'], 
                        m.get('department_key'), m['body_text'], m['file_id'], m['file_type'], m['status'], 
                        m['answer_text'], m['answered_by'], created_at, answered_at
                    )
                    murojaatlar_count += 1
                    
        return {"users": users_count, "murojaatlar": murojaatlar_count}
