from celery_config import celery, flask_app
from adult_report_generator import generate_full_report

# Ensure the task is registered with Celery
celery.task(name='adult_report_generator.generate_full_report')(generate_full_report)

if __name__ == '__main__':
    with flask_app.app_context():
        celery.start()
