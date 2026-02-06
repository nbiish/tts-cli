
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from tts_cli.models.pocket_tts_model import PocketTTSModel

class TestPocketTTSModel(unittest.TestCase):
    def setUp(self):
        self.model = PocketTTSModel()
        # Mock environment executable
        self.model.python_executable = Path("/mock/python")
        self.model.is_available = True

    def test_initialization(self):
        self.assertEqual(self.model.model_name, "pocket-tts")
        self.assertTrue("alba" in self.model._default_voices)

    def test_voice_validation(self):
        self.assertTrue(self.model.validate_voice("alba"))
        self.assertFalse(self.model.validate_voice("invalid_voice"))
        
        # Test path validation (mocking Path.exists)
        with patch("pathlib.Path.exists", return_value=True):
            self.assertTrue(self.model.validate_voice("/path/to/voice.wav"))

    @patch("subprocess.Popen")
    def test_generate_speech(self, mock_popen):
        # Setup mock process
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Success", "")
        process_mock.returncode = 0
        mock_popen.return_value.__enter__.return_value = process_mock

        # Mock Path.exists to return True for output file
        with patch("pathlib.Path.exists", return_value=True):
            # Test generation
            success = self.model.generate_speech("Hello world", "alba", "output.wav")
        
        self.assertTrue(success)
        
        # Verify script content
        args, _ = mock_popen.call_args
        cmd_args = args[0]
        script_content = cmd_args[2]
        
        self.assertIn("from pocket_tts import TTSModel", script_content)
        self.assertIn('voice_input = "alba"', script_content)
        self.assertIn('text = "Hello world"', script_content)
        self.assertIn('output_path = "output.wav"', script_content)

    @patch("subprocess.Popen")
    def test_generate_speech_voice_cloning(self, mock_popen):
        # Setup mock process
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Success", "")
        process_mock.returncode = 0
        mock_popen.return_value.__enter__.return_value = process_mock

        # Test generation with file path
        # We need exists to be true for both voice file and output file
        with patch("pathlib.Path.exists", return_value=True):
            success = self.model.generate_speech("Hello world", "/path/to/voice.wav", "output.wav")
        
        self.assertTrue(success)
        
        # Verify script content
        args, _ = mock_popen.call_args
        cmd_args = args[0]
        script_content = cmd_args[2]
        
        self.assertIn('voice_input = "/path/to/voice.wav"', script_content)
        self.assertIn('voice_is_path = True', script_content)

if __name__ == "__main__":
    unittest.main()
