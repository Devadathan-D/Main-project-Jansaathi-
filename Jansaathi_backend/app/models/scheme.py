from app.extensions import db

class Scheme(db.Model):
    __tablename__ = "schemes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    
    # Details
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(500), nullable=True) # The real DB column
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Target demographics
    state = db.Column(db.String(100), index=True, nullable=True)
    occupation = db.Column(db.String(100), index=True, nullable=True)
    category = db.Column(db.String(100), index=True, nullable=True)

    # Age eligibility
    min_age = db.Column(db.Integer, nullable=True)
    max_age = db.Column(db.Integer, nullable=True)

    # Income eligibility
    min_income = db.Column(db.Float, nullable=True)
    max_income = db.Column(db.Float, nullable=True)

    # Required documents
    required_documents = db.Column(db.JSON, default=list)

    @staticmethod
    def _format_title_from_link(link):
        if not link:
            return None
        slug = str(link).rstrip("/").split("/")[-1].strip()
        if not slug:
            return None
        return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-") if part)

    def _display_name(self):
        name = (self.name or "").strip()
        if name:
            return name
        fallback = self._format_title_from_link(self.link)
        return fallback or "Untitled Scheme"

    def to_dict(self):
        """
        Returns a dictionary compatible with the Flutter App.
        Includes ALIASES so the old UI works with the new DB.
        """
        display_name = self._display_name()
        content = {"Details": [self.description]} if self.description else {}
        is_open = bool(self.is_active)
        status_text = "Open" if is_open else "Closed"
        return {
            "id": self.id,
            "name": display_name,
            "description": self.description,
            "link": self.link,
            "is_active": self.is_active,
            "is_open": is_open,
            "scheme_status": status_text,
            "status_text": status_text,
            "category": self.category,
            "content": content,
            "eligibility": {
                "state": self.state,
                "occupation": self.occupation,
                "category": self.category,
                "min_age": self.min_age,
                "max_age": self.max_age,
                "min_income": self.min_income,
                "max_income": self.max_income,
                "required_documents": self.required_documents
            },
            # ================= COMPATIBILITY ALIASES =================
            # Your Flutter app expects these keys from the old JSON Scraper.
            # We map them here so you don't have to change Flutter code.
            "title": display_name,           # Alias for 'name'
            "scheme_url": self.link,      # Alias for 'link'
            "is_closed": not is_open # Inverse logic for compatibility
        }

    def __repr__(self):
        return f'<Scheme {self.name}>'
