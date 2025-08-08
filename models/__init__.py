from .user import User
from .itinerary import Itinerary
from .transportation import Transportation

# Importar todos los modelos del traveler test
from .traveler_test.question import Question
from .traveler_test.question_option import QuestionOption
from .traveler_test.traveler_type import TravelerType
from .traveler_test.question_option_score import QuestionOptionScore
from .traveler_test.user_traveler_test import UserTravelerTest
from .traveler_test.user_answers import UserAnswer

from database import Base