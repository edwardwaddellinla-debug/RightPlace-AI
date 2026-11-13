import unittest
from pathlib import Path
class TroubleshootingContextTests(unittest.TestCase):
    def test_endpoint_validates_context(self):
        s=Path(__file__).with_name('server.py').read_text()
        self.assertIn("if not isinstance(tried,list)",s)
        self.assertIn('tried[:8]',s)
        self.assertIn("model_batch(prompt,compare=",s)
    def test_ui_passes_context_without_persistence(self):
        s=Path(__file__).with_name('index.html').read_text()
        self.assertIn('already_tried:followupLog',s)
        self.assertIn("item.tried=q",s)
