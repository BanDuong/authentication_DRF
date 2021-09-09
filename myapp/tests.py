from django.test import TestCase
from myapp.models import *
# Create your tests here.

class AnythingTest(TestCase):
    # def setUp(self) -> None:
    #     Questions.objects.create(question="What grade are you in?")

    def test_questions(self):   # Each testing time, A DB virtual will be created
        users = User.objects.all()  # -->NULL
        self.assertContains(users[0].username, 'admin')    # --> False

