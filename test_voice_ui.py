import unittest
from pathlib import Path
class VoiceUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(Path(__file__).parent/'index.html').read_text()
    def test_voice_button_is_primary_and_accessible(self):
        self.assertIn('id="mic" aria-label="Ask by voice" aria-pressed="false"',self.html)
        self.assertIn('#mic{height:116px;width:116px',self.html)
    def test_voice_failure_resets_button_and_allows_typing(self):
        self.assertIn('r.onerror=e=>{if(activeSpeech!==r)return;failed=true;',self.html)
        self.assertIn('setVoiceStatus(failed?errorMessage:',self.html)
        self.assertIn("$('mic').classList.toggle('listening',listening)",self.html)
    def test_successful_speech_submits_question(self):
        self.assertIn("if(captured&&!failed&&!submitted)",self.html)
if __name__=='__main__':unittest.main()
