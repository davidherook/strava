from app.main import example_function


class TestSomething:

    def test_dummy(self):
        assert 1 == 1

    def test_example_function(self):
        assert example_function() == 'a'
