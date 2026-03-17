from app import create_app, db
from app.models.scheme import Scheme
from scheme_utils import load_schemes_data


def _title_from_link(link):
    if not link:
        return None
    slug = str(link).rstrip('/').split('/')[-1].strip()
    if not slug:
        return None
    return ' '.join(part.capitalize() for part in slug.replace('_', '-').split('-') if part)


def _clean_title(raw_title, scheme_url):
    title = (raw_title or '').strip()
    if title:
        return title
    fallback = _title_from_link(scheme_url)
    return fallback or 'Untitled Scheme'


def _extract_description(content):
    if not isinstance(content, dict):
        return ''

    chunks = []
    for value in content.values():
        if isinstance(value, list):
            chunks.extend(str(item) for item in value if isinstance(item, (str, int, float)))
        elif isinstance(value, (str, int, float)):
            chunks.append(str(value))

    return ' '.join(chunks)


def import_json_to_sql():
    """
    Reads schemes.json and saves them into the SQL Database.
    This allows the recommendation engine to work with scraped data.
    """
    app = create_app()

    with app.app_context():
        print('Starting migration: JSON -> SQL Database...')

        json_data = load_schemes_data()
        if not json_data:
            print('No data found in JSON. Aborting.')
            return

        # Optional: clear existing rows first to avoid duplicates.
        # Scheme.query.delete()
        # db.session.commit()

        count = 0
        for block in json_data:
            category = block.get('category', 'General')
            schemes_list = block.get('schemes', [])

            for scheme in schemes_list:
                scheme_url = scheme.get('scheme_url')
                title = _clean_title(scheme.get('title'), scheme_url)
                content = scheme.get('content', {})
                description = _extract_description(content)

                db_scheme = Scheme(
                    name=title,
                    description=description[:500],
                    link=scheme_url,
                    is_active=not scheme.get('is_closed', False),
                    state='ALL',
                    occupation=None,
                    category=category,
                    min_age=None,
                    max_age=None,
                    min_income=None,
                    max_income=None,
                    required_documents=[]
                )

                db.session.add(db_scheme)
                count += 1

        try:
            db.session.commit()
            print(f'SUCCESS: Imported {count} schemes into the database.')
            print('Your recommendation engine can now use this data.')
        except Exception as e:
            db.session.rollback()
            print(f'Error importing to DB: {e}')


if __name__ == '__main__':
    import_json_to_sql()
