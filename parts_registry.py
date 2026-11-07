"""Evidence-first parts registry. No guessed OEM or interchange numbers."""
import json, sqlite3

def setup_parts(connection):
    connection.execute('''CREATE TABLE IF NOT EXISTS part_evidence (
      id INTEGER PRIMARY KEY, maker TEXT NOT NULL, model TEXT NOT NULL,
      serial_range TEXT NOT NULL DEFAULT '', component TEXT NOT NULL,
      part_number TEXT NOT NULL, number_kind TEXT NOT NULL,
      source_url TEXT NOT NULL, source_label TEXT NOT NULL,
      verification TEXT NOT NULL CHECK(verification IN ('candidate','verified','rejected')),
      notes TEXT NOT NULL DEFAULT '',
      UNIQUE(maker,model,serial_range,component,part_number,number_kind,source_url))''')

def lookup(connection,maker,model,component,serial=''):
    """Conservative: unknown serial fitment never becomes confirmed fitment."""
    if not all(isinstance(x,str) for x in (maker,model,component,serial)):
        raise ValueError('Text fields required')
    if not all(0<len(x.strip())<=100 for x in (maker,model,component)) or len(serial)>100:
        raise ValueError('Maker, model, and component required (max 100 characters)')
    rows=connection.execute('''SELECT maker,model,serial_range,component,part_number,
      number_kind,source_url,source_label,verification,notes FROM part_evidence
      WHERE lower(maker)=lower(?) AND lower(model)=lower(?) AND lower(component)=lower(?)
      AND verification!='rejected' ORDER BY verification DESC,part_number LIMIT 50''',
      (maker.strip(),model.strip(),component.strip())).fetchall()
    matches=[]
    for row in rows:
        d=dict(row)
        # Serial ranges require a manufacturer-specific decoder; never compare them lexically.
        d['fitment']='needs_serial_verification' if d['serial_range'] else 'needs_fitment_verification'
        d['source_verified']=d['verification']=='verified'
        matches.append(d)
    return {'results':matches,'note':('No catalog records loaded. Do not invent part numbers.' if not matches
        else 'Catalog evidence is not proof of fit. Verify VIN/serial, thread, seat and rating before ordering.')}
