import sqlite3,unittest
from parts_registry import setup_parts,lookup
class PartsTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row;setup_parts(self.db)
 def tearDown(self):self.db.close()
 def test_empty_is_honest(self):
  r=lookup(self.db,'Western Star','4900','air tank elbow');self.assertEqual(r['results'],[]);self.assertIn('Do not invent',r['note'])
 def test_verified_source_not_verified_fit(self):
  self.db.execute("INSERT INTO part_evidence(maker,model,component,part_number,number_kind,source_url,source_label,verification) VALUES (?,?,?,?,?,?,?,?)",('Western Star','4900','air tank elbow','EXAMPLE-ONLY','OEM','https://example.org/catalog','Test catalog','verified'))
  r=lookup(self.db,'western star','4900','air tank elbow');self.assertTrue(r['results'][0]['source_verified']);self.assertEqual(r['results'][0]['fitment'],'needs_fitment_verification')
 def test_serial_range_needs_manual_check(self):
  self.db.execute("INSERT INTO part_evidence(maker,model,serial_range,component,part_number,number_kind,source_url,source_label,verification) VALUES (?,?,?,?,?,?,?,?,?)",('Western Star','4900','VIN subset','air tank elbow','EXAMPLE-ONLY','OEM','https://example.org/catalog','Test catalog','candidate'))
  self.assertEqual(lookup(self.db,'Western Star','4900','air tank elbow','ABC')['results'][0]['fitment'],'needs_serial_verification')
 def test_rejected_not_returned(self):
  self.db.execute("INSERT INTO part_evidence(maker,model,component,part_number,number_kind,source_url,source_label,verification) VALUES (?,?,?,?,?,?,?,?)",('Western Star','4900','air tank elbow','BAD','OEM','https://example.org','Test','rejected'))
  self.assertEqual(lookup(self.db,'Western Star','4900','air tank elbow')['results'],[])
 def test_invalid_input(self):
  with self.assertRaises(ValueError):lookup(self.db,'','4900','elbow')
if __name__=='__main__':unittest.main()
