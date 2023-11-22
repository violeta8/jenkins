import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question

def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    
    Función auxiliar que permite crear una pregunta.
    Recibe el texto de la pregunta y los días que han pasado o faltan
    desde o para publicarla. (Un valor negativo significa que ya se publico,
    un valor positivo significa que se tenfrá que publicar en el futuro.)
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


"""Test para la clase DetailView

La clase DetailView muestra los detalles, pregunta y respuesta de una pregunta. 
Se accede con la url /polls/<id de la pregunta>.

Requisitos
==========
1. Si intentamos ver el detalle de una pregunta con fecha de publicación futura
 nos debe devolver un 404.

¿Dónde conseguimos esto?

En la función get_queryset de la Class DetailView, la cosulta que se hace es:

    Question.objects.filter(pub_date__lte=timezone.now())

Al no seleccionar ninguna pregunta nos da un 404.
===============================================================================
2. Al ver el detalle de una pregunta publicada con un fecha pasada se debe mostrar 
el texto de la pregunta. Esto se consigue en el template detail.html en la primera línea:

    <h1>{{ question.question_text }}</h1>
"""


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.

        En este test se comprueba que si accedemos a detalle de una pregunta 
        con fecha de publicación en el futuro (todavía no se ha publicado),
        nos devuelve un 404. 
        """
        future_question = create_question(
            question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.

        Cuando intentamos ver el detalle de una pregunta publicada 
        en el pasado se debe ver el texto de la pregunta.
        """
        past_question = create_question(
            question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

"""Test para la clase IndexView
La clase IndexView es la encargada de mostrar las preguntas publicadas.
Cada objeto "Question" tiene una fecha de publicación. 

Solo se publican las preguntas cuya fecha de publicación sea menor que 
el día actual (publicadas en el pasado). 

En la página principal se ven las 5 últimas preguntas publicadas.

Requisitos
==========
1. Si no hay preguntas en la base de datos, en la página principal aparece el mensaje "No polls are available.". 
Lo puedes ver en el template index.html.

===============================================================================
2. Si hay preguntas con fecha de publicación en el pasado, debe aparecer en la página principal.
Eso lo puedes ver en el fichero views.py en la función get_queryset de la Class IndexView, la consulta es:

     Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

===============================================================================
3. Si tenemos preguntas con fecha de publicación en el futuro, no deben aparecer en la página principal.
En la página principal aparece el mensaje "No polls are available.". 

"""

class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.

        Si no hay preguntas en la base de datos debe aparecer el mensaje 
        "No polls are available."
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.

        Las preguntas con fecha de publicación en el pasado debe aparecer en 
        la página principal.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.

        Las preguntas con fecha de publicación en el futuro, no deben 
        aparecer en la página principal.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.

        Si tenemos una pregunta publicada en el pasado y otra en el futuro.
        Sólo debe aparecer la publicada en el pasado.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.

        Si tenemos varias preguntas en el pasado deben aparecer en la página principal.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )

""" Test sobre el modele de datos

Podemos ver en el modelo de datos (models.py) que la clase Question tiene 
una función booleana (was_published_recently) que devuelve True si la pregunta ha sido
publicada en el último día.

Requisitos
==========

1. En las preguntas publicadas en una fecha futura, la función was_published_recently() 
debe devolver False

===============================================================================

2. En las preguntas publicadas hace más de 1 día, la función was_published_recently() 
debe devolver False.

===============================================================================

3. En las preguntas publicadas hace un 1 día, la función was_published_recently() 
debe devolver True.

"""
class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.

        Las preguntas publicadas en una fecha futura, la función 
        was_published_recently() debe devolver False
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        
        En las preguntas publicadas hace más de 1 día, la función 
        was_published_recently() debe devolver False.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        
        En las preguntas publicadas hace un 1 día, la función 
        was_published_recently() debe devolver True.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)
