from unittest import TestCase

from pydantic import ValidationError

from neon_users_service.models import *


class TestSqlite(TestCase):
    def test_neon_user_config(self):
        default = NeonUserConfig()
        valid_with_extras = NeonUserConfig(
            user={"first_name": "Daniel",
                  "middle_name": "James",
                  "last_name": "McKnight",
                  "preferred_name": "tester",
                  "dob": "01/01/2001",
                  "email": "developers@neon.ai",
                  "extra_key": "This should be removed by validation"
                  },
            language={"input": ["en-us", "uk-ua"],
                      "output": ["en-us", "es-es"]},
            units={"time": 24, "date": "YMD", "measure": "metric"},
            location={"lat": 47.6765382, "lon": -122.2070775,
                      "name": "Kirkland, WA",
                      "timezone": "America/Los_Angeles"},
            extra_section={"test": True}
        )

        # Ensure invalid keys are removed and defaults are added
        self.assertEqual(default.model_dump().keys(),
                         valid_with_extras.model_dump().keys())
        for section in default.model_dump().keys():
            if section == "skills":
                # `skills` is not a model, the contents are arbitrary
                continue
            default_keys = getattr(default, section).model_dump().keys()
            extras_keys = getattr(valid_with_extras, section).model_dump().keys()
            self.assertEqual(default_keys, extras_keys)

        # Validation errors
        with self.assertRaises(ValidationError):
            NeonUserConfig(units={"time": 13})
        with self.assertRaises(AssertionError):
            # TODO: This should fail validation
            config = NeonUserConfig(location={"lat": "47.6765382",
                                     "lon": "-122.2070775"})
            assert config.location.latitude == 47.6765382
