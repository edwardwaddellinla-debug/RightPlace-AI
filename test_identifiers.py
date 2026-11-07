import sqlite3, unittest
from identifiers import setup_identifiers, lookup_identifier
class IdentifierTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row;setup_identifiers(self.db)
 def tearDown(self):self.db.close()
 def add(self,number='ABC-123',maker='Acme',status='verified'):
  self.db.execute('INSERT INTO identifier_evidence(identifier,kind,maker,item_name,source_url,source_label,status) VALUES (?,?,?,?,?,?,?)',(number,'model',maker,'Test appliance','https://example.org','Catalog',status))
 def test_empty_does_not_guess(self):self.assertEqual(lookup_identifier(self.db,'ABC-123')['results'],[])
 def test_exact_match(self):
  self.add();self.assertEqual(len(lookup_identifier(self.db,'abc-123')['results']),1)
  self.assertEqual(lookup_identifier(self.db,'ABC-12')['results'],[])
 def test_maker_disambiguation(self):
  self.add();self.add(maker='Other');self.assertEqual(len(lookup_identifier(self.db,'ABC-123')['results']),2)
  self.assertEqual(len(lookup_identifier(self.db,'ABC-123','Acme')['results']),1)
 def test_rejected_hidden(self):
  self.add(status='rejected');self.assertEqual(lookup_identifier(self.db,'ABC-123')['results'],[])
 def test_invalid(self):
  for value in ('','x','a'*101,'bad\nnumber'):
   with self.assertRaises(ValueError):lookup_identifier(self.db,value)
if __name__=='__main__':unittest.main()

class AmbiguityTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row;setup_identifiers(self.db)
 def insert(self,maker,item,source='https://example.org/1',status='verified',notes=''):
  self.db.execute('INSERT INTO identifier_evidence(identifier,kind,maker,item_name,source_url,source_label,status,notes) VALUES (?,?,?,?,?,?,?,?)',('XYZ123','model',maker,item,source,'Catalog',status,notes))
 def test_same_product_multiple_sources_no_question(self):
  self.insert('Maker','Truck');self.insert('Maker','Truck','https://example.org/2')
  result=lookup_identifier(self.db,'XYZ123')
  self.assertFalse(result['ambiguous']);self.assertEqual(result['distinct_products'],1)
 def test_two_products_one_short_question(self):
  self.insert('Maker','Truck');self.insert('Other','Washing machine')
  result=lookup_identifier(self.db,'XYZ123')
  self.assertEqual(result['clarifying_question'],'What is it for?')
 def test_category_resolves_ambiguity(self):
  self.insert('Maker','Truck');self.insert('Other','Washing machine')
  result=lookup_identifier(self.db,'XYZ123',category='washing')
  self.assertFalse(result['ambiguous']);self.assertEqual(len(result['results']),1)
 def test_candidate_not_misrepresented_as_verified(self):
  self.insert('Maker','Truck',status='candidate')
  self.assertIn('not verified',lookup_identifier(self.db,'XYZ123')['note'])
