"""Evidence-based identifier lookup with one-question ambiguity resolution."""
KINDS={'serial','model','vin','sku','barcode','part','imei','other'}

def setup_identifiers(db):
    db.execute('''CREATE TABLE IF NOT EXISTS identifier_evidence (
      id INTEGER PRIMARY KEY, identifier TEXT NOT NULL, kind TEXT NOT NULL,
      maker TEXT NOT NULL DEFAULT '', item_name TEXT NOT NULL,
      source_url TEXT NOT NULL, source_label TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('candidate','verified','rejected')),
      notes TEXT NOT NULL DEFAULT '',
      UNIQUE(identifier,kind,maker,item_name,source_url))''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_identifier_exact ON identifier_evidence(identifier)')

def lookup_identifier(db, value, maker='', category=''):
    if not all(isinstance(x,str) for x in (value,maker,category)) or not (2<=len(value.strip())<=100) or len(maker)>100 or len(category)>100:
        raise ValueError('Identifier must be 2–100 characters; maker/category max 100 characters')
    value=value.strip();maker=maker.strip();category=category.strip()
    if any(ord(ch)<32 for ch in value+maker+category):
        raise ValueError('Control characters not allowed')
    rows=db.execute('''SELECT identifier,kind,maker,item_name,source_url,source_label,status,notes
       FROM identifier_evidence WHERE identifier=? COLLATE NOCASE
       AND (?='' OR maker=? COLLATE NOCASE) AND status!='rejected'
       ORDER BY CASE status WHEN 'verified' THEN 0 ELSE 1 END, maker LIMIT 200''',(value,maker,maker)).fetchall()
    matches=[dict(row) for row in rows]
    # Category is an optional conversational hint; don't pretend it's a verified taxonomy.
    if category:
        matches=[r for r in matches if category.casefold() in (r['item_name']+' '+r['notes']).casefold()]
    # Distinct products, not source citations: two catalogs documenting one item are one match.
    identities={(r['kind'].casefold(),r['maker'].casefold(),r['item_name'].casefold()) for r in matches}
    ambiguous=len(identities)>1
    if ambiguous:
        question='What is it for?'
        note='This number matches more than one product. Ask one short clarification before choosing.'
    elif not matches:
        question=None
        note='No catalog match found. Ask for manufacturer or product type if needed; do not guess.'
    else:
        question=None
        note=('One documented product match found; verify the model/serial range before ordering or repairing.'
              if any(r['status']=='verified' for r in matches) else
              'One candidate found, but its identity is not verified.')
    return {'identifier':value,'results':matches[:50], 'ambiguous':ambiguous,
            'clarifying_question':question,'distinct_products':len(identities),'note':note,
            'privacy':'Avoid sharing personal account numbers, access codes, or device identifiers publicly.'}
