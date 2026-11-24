import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


@contextmanager
def cursor():
    conn = psycopg2.connect(os.environ['DATABASE_URL'], cursor_factory=RealDictCursor)
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def save_concern(text, category, confidence, flagged, village):
    with cursor() as cur:
        cur.execute('SELECT category_id FROM categories WHERE category_name = %s', (category,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f'Category not in database: {category}')
        cur.execute(
            '''INSERT INTO concerns
                   (transcribed_text, predicted_category, confidence_score, is_flagged, settlement_village)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING concern_id, submission_timestamp''',
            (text, row['category_id'], confidence, flagged, village))
        saved = cur.fetchone()
        if flagged:
            cur.execute('INSERT INTO review_queue (concern_id) VALUES (%s)', (saved['concern_id'],))
    return saved


def list_concerns(category=None, village=None, flagged_only=False, limit=50):
    sql = '''SELECT c.concern_id AS id, c.transcribed_text AS text, k.category_name AS category,
                    c.confidence_score AS confidence, c.is_flagged AS flagged,
                    c.settlement_village AS village, c.submission_timestamp AS submitted_at
             FROM concerns c JOIN categories k ON k.category_id = c.predicted_category
             WHERE (%s::text IS NULL OR k.category_name = %s)
               AND (%s::text IS NULL OR c.settlement_village = %s)
               AND (NOT %s OR c.is_flagged)
             ORDER BY c.submission_timestamp DESC
             LIMIT %s'''
    with cursor() as cur:
        cur.execute(sql, (category, category, village, village, flagged_only, limit))
        rows = cur.fetchall()
    for row in rows:
        row['submitted_at'] = row['submitted_at'].isoformat()
    return rows


def stats():
    with cursor() as cur:
        cur.execute('SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_flagged) AS flagged FROM concerns')
        totals = cur.fetchone()
        cur.execute('''SELECT k.category_name AS name, COUNT(c.concern_id) AS count
                       FROM categories k LEFT JOIN concerns c ON c.predicted_category = k.category_id
                       GROUP BY k.category_name ORDER BY k.category_name''')
        by_category = cur.fetchall()
        cur.execute('''SELECT COALESCE(settlement_village, 'Unspecified') AS name, COUNT(*) AS count
                       FROM concerns GROUP BY 1 ORDER BY count DESC''')
        by_village = cur.fetchall()
        cur.execute('''SELECT submission_timestamp::date AS day, COUNT(*) AS count
                       FROM concerns WHERE submission_timestamp >= NOW() - INTERVAL '7 days'
                       GROUP BY 1 ORDER BY 1''')
        by_day = cur.fetchall()
    for row in by_day:
        row['day'] = row['day'].isoformat()
    return {'total': totals['total'], 'flagged': totals['flagged'],
            'by_category': by_category, 'by_village': by_village, 'by_day': by_day}
