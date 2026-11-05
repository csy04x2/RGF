import hashlib
from app.database import get_connection, is_postgres


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

        if is_postgres(conn):
            cursor.execute(sql + " RETURNING id", values)
            document_id = cursor.fetchone()["id"]
        else:
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
        cursor = conn.cursor()

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




def save_source_evidence(
    source_document_id: int,
    page_number: int,
    content: str,
) -> int:
    """Save evidence or reuse the ID of an identical record."""

    if source_document_id <= 0:
        raise ValueError("Invalid source document ID")

    if page_number <= 0:
        raise ValueError("Invalid PDF page number")

    if not content.strip():
        raise ValueError("Evidence content cannot be empty")

    content_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    location_label = f"PDF {page_number}"

    sql = """
        INSERT INTO source_evidence (
            source_document_id,
            evidence_type,
            location_label,
            content,
            content_hash
        )
        VALUES (%s, 'PARAGRAPH', %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            id = LAST_INSERT_ID(id)
    """

    connection = get_connection()
    postgres = is_postgres(connection)
    if postgres:
        sql = """
            INSERT INTO source_evidence (
                source_document_id, evidence_type, location_label, content, content_hash
            ) VALUES (%s, 'PARAGRAPH', %s, %s, %s)
            ON CONFLICT (source_document_id, location_label, content_hash)
            DO UPDATE SET id = source_evidence.id
            RETURNING id
        """

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    source_document_id,
                    location_label,
                    content,
                    content_hash,
                ),
            )

            evidence_id = cursor.fetchone()["id"] if postgres else cursor.lastrowid

        connection.commit()
        return evidence_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
