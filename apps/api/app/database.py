"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from contextlib import contextmanager

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/analyst_awards"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_migrations():
    """배포 시 자동으로 마이그레이션 실행"""
    try:
        import os
        from pathlib import Path
        from alembic import command
        from alembic.config import Config
        
        # alembic.ini 파일 경로 찾기
        current_dir = Path(__file__).parent.parent
        alembic_ini_path = current_dir / "alembic.ini"
        
        if not alembic_ini_path.exists():
            print(f"alembic.ini 파일을 찾을 수 없습니다: {alembic_ini_path}")
            return
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", "alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        
        # 최신 마이그레이션으로 업그레이드
        command.upgrade(alembic_cfg, "head")
        print("데이터베이스 마이그레이션이 완료되었습니다.")
    except Exception as e:
        print(f"마이그레이션 실행 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        # 마이그레이션 실패해도 애플리케이션은 계속 실행
        pass


# 애플리케이션 시작 시 마이그레이션 실행 (환경 변수로 제어)
if os.getenv("AUTO_MIGRATE", "false").lower() == "true":
    run_migrations()
