from django_tasks import task
from icecream import ic


@task()
def calculate_meaning_of_life() -> int:
    ic("running task")
    return 42
