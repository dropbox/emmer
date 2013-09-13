from emmer import Emmer
import response_router
import unittest


class TestEmmer(unittest.TestCase):
    def test_constructor(self):
        emmer = Emmer()
        self.assertEqual(emmer.response_router.__class__,
                         response_router.ResponseRouter)
