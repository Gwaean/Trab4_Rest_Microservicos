from flask import Flask,jsonify
from flask import render_template
from flask import sse
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import uuid
import random
from faker import Faker
from flask_cors import CORS
from Cruzeiro_Itinerarios import carregar_itinerarios

fake = Faker()

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

sse.publish({"message": datetime.datetime.now()}, type='publish')
def get_data():
    data = list()
    for _ in range(10):
        data.append({'userId': uuid.uuid4(), 'id': random.randrange(1, 100), 'name': fake.name(), 'address': fake.address()})
    return data


def get_schd_time():
    return random.randrange(5,20)

def server_side_event():
    """ Function to publish server side event """
    with app.app_context():
        sse.publish(get_data(), type='dataUpdate')
        print("Event Scheduled at ",datetime.datetime.now())


sched = BackgroundScheduler(daemon=True)
sched.add_job(server_side_event,'interval',seconds=get_schd_time())
sched.start()


@app.route('/')
def index():
    return jsonify(get_data())

@app.route('/api/destinations')
def get_destinations():
    """Return list of unique destinations from itinerarios.csv"""
    itinerarios = carregar_itinerarios()

    destinos = list(set(item['destino'] for item in itinerarios))
    
    return jsonify([
        {"id": idx + 1, "name": destino}
        for idx, destino in enumerate(destinos)
    ])
if __name__ == '__main__':
   app.run(debug=True,host='0.0.0.0',port=5000)