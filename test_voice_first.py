import pathlib, unittest
class VoiceFirstLayout(unittest.TestCase):
 def test_primary_voice_before_text(self):
  html=pathlib.Path(__file__).with_name('index.html').read_text()
  self.assertLess(html.index('id="mic"'),html.index('id="question"'))
  self.assertIn('Tap the purple button to ask',html)
  self.assertIn('Or type your question',html)
  self.assertIn('id="askBtn"',html)
if __name__=='__main__':unittest.main()
