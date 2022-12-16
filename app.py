from flask import Flask
from celery import Celery
import time

app = Flask(__name__)

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0'
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def add(x, y):
    time.sleep(5)  # simulate some long-running work
    return x + y

@app.route('/add/<int:x>/<int:y>')
def add(x, y):
    result = add.delay(x, y)
    return str(result.get())

if __name__ == '__main__':
    app.run()
