import pandas as pd
from app import create_app, db
from app.models.scheme import Scheme

def import_csv():
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Load CSV
            df = pd.read_csv('schemes_data.csv')
            print(f"📂 Loaded {len(df)} rows from schemes_data.csv")
            
            # DEBUG: Print columns to check for typos
            print(f"🔍 CSV Columns found: {list(df.columns)}")
            
        except FileNotFoundError:
            print("❌ Error: 'schemes_data.csv' not found. Please place it in the project root.")
            return
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return

        # Optional: Clear old schemes to avoid duplicates
        # Scheme.query.delete()
        # db.session.commit()

        count = 0
        for _, row in df.iterrows():
            try:
                # Helper to handle NaN/None
                def get_val(key):
                    val = row.get(key)
                    return val if pd.notna(val) else None

                # Helper to clean list strings
                def get_list(key):
                    val = get_val(key)
                    if isinstance(val, str):
                        return [x.strip() for x in val.split(',')]
                    return []

                scheme = Scheme(
                    name=get_val('name'),
                    description=get_val('description'),
                    link=get_val('link'),
                    is_active=True,
                    state=get_val('state'),
                    occupation=get_val('occupation'),
                    category=get_val('category'),
                    min_age=int(get_val('min_age')) if get_val('min_age') else None,
                    max_age=int(get_val('max_age')) if get_val('max_age') else None,
                    # Ensure these are converted to Float
                    min_income=float(get_val('min_income')) if get_val('min_income') else None,
                    max_income=float(get_val('max_income')) if get_val('max_income') else None,
                    required_documents=get_list('required_documents')
                )
                
                db.session.add(scheme)
                count += 1
                
            except Exception as e:
                print(f"⚠️ Skipping row {count+1} due to error: {e}")
                continue

        try:
            db.session.commit()
            print(f"✅ Successfully imported {count} schemes into the database!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database commit failed: {e}")

if __name__ == "__main__":
    import_csv()