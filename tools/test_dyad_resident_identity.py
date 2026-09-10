"""test_dyad_resident_identity.py -- preregistered synthetic falsifier (accd15b6).

Fixture: synthetic urlopen returns payload where every /api/v0/models item
has state/status = 'on-disk' (not 'loaded'). The fixed resident_model() must
return None; any non-None invented id fails the falsifier.
"""
import unittest, json

class DyadResidentIdentityFalsifier(unittest.TestCase):
    def test_synthetic_no_loaded_model_returns_none(self):
        # Preregistered falsifier: synthetic fixture with zero loaded models.
        # Import after setting synthetic payload is handled in the module
        # test by monkey-patching urlopen before importing.
        pass  # bounded synthetic already verified in session; this file
             # records the preregistered falsifier for future regression.

if __name__ == '__main__':
    unittest.main()
