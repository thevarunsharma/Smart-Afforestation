from flask import Flask, render_template, request, redirect, url_for
from smart_afforestation import TreePlanterGA

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        return redirect(url_for('show_result'), code=307)
    return render_template('home.html')

@app.route("/Result", methods=['POST'])
def show_result():
    data = request.form
    AQI = int(data.get('AQI'))
    area_lt = int(data.get('area'))
    cost_lt = int(data.get('cost'))
    population = int(data.get('population'))
    runtime = int(data.get('runtime'))
    # smart planter agent
    agent = TreePlanterGA(AQI, area_lt, cost_lt, population)
    print("processing request...")
    agent.run_search(runtime=runtime, verbose=0)
    result = agent.get_results()
    return render_template('result.html', trees=result['trees'], score=result['score'],
                            area_used=result['area'], cost_used=result['cost'], population=population,
                            AQI=AQI, area_limit=area_lt, cost_limit=cost_lt)

app.run(debug=True)
