
from app.db import get_connection


def create_source_document(
    title,
    source_type,
    raw_text=None,
    file_path=None,
    organization=None,
):
    """정책자료 한 건을 MySQL에 저장하고 생성된 ID를 반환한다."""

    if not title or not title.strip():
        raise ValueError("자료 제목을 입력해야 합니다.")

    if source_type not in ("PDF", "TEXT"):
        raise ValueError("자료 유형은 PDF 또는 TEXT여야 합니다.")

    if not raw_text and not file_path:
        raise ValueError("원문 텍스트나 PDF 경로가 필요합니다.")

    conn = get_connection()
    cursor = None

    try:
        cursor = conn.cursor()

        sql = """
            INSERT INTO source_documents
                (title, source_type, raw_text, file_path, organization)
            VALUES
                (%s, %s, %s, %s, %s)
        """

        values = (
            title,
            source_type,
            raw_text,
            file_path,
            organization,
        )

        cursor.execute(sql, values)
        document_id = cursor.lastrowid
        conn.commit()

        return document_id

    except Exception:
        conn.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def get_source_document(document_id):
    """ID로 정책자료 한 건을 조회한다."""

    conn = get_connection()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                title,
                source_type,
                organization,
                raw_text,
                file_path,
                created_at
            FROM source_documents
            WHERE id = %s
        """

        cursor.execute(sql, (document_id,))
        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()
