import dataclasses
import unittest
from unittest.mock import patch

from ruby.core.compat import compat_dataclass


class CompatDataclassTests(unittest.TestCase):
    def test_falls_back_when_slots_not_supported(self) -> None:
        call_kwargs: list[dict[str, object]] = []

        def fake_dataclass(*args, **kwargs):
            call_kwargs.append(dict(kwargs))
            if kwargs.get("slots") is True:
                raise TypeError("dataclass() got an unexpected keyword argument 'slots'")
            return dataclasses.dataclass(*args, **kwargs)

        with patch("ruby.core.compat._stdlib_dataclass", side_effect=fake_dataclass):
            decorator = compat_dataclass(slots=True)

            @decorator
            class Sample:
                value: int

        self.assertEqual(call_kwargs[0].get("slots"), True)
        self.assertNotIn("slots", call_kwargs[1])
        self.assertEqual(Sample(value=1).value, 1)


if __name__ == "__main__":
    unittest.main()
