import json
from flask import Flask, request, Response
from proactive.config import Configuration
from proactive.priority.priorityservice import PriorityService
from proactive.dbs import BusinessDB, OrderDB


app = Flask(__name__)
config = Configuration()
mongo = config.read([config.DATABASES])[0][0]
# Setup connection to orders database.
orderDBConn = OrderDB(
  mongo["uri"],
  mongo["port"],
  mongo["database"],
  mongo["username"],
  mongo["password"]
)
orderDBConn.connect()
priorityService = PriorityService(orderDBConn)



@app.route("/beginWorker", methods=["POST"])
def beginWorker():
  """
    Runs a new worker to monitor orders for a business.
    {
      "business": {
        id: "test1234"
      },
      refresh: 5000
    }
  """
  json_ = request.get_json()

  if json_:
    business = json_.get("business")
    businessID = business["businessID"]
    refresh = json_["refresh"]

    # Setup connection to orders database.
    businessDBConn = BusinessDB(
      mongo["uri"],
      mongo["port"],
      mongo["database"],
      mongo["username"],
      mongo["password"]
    )
    businessDBConn.connect()
    business = businessDBConn.read(businessID)
    priorityService.newWorker(business=business, workerID=businessID, refresh=refresh)
    return Response(response="Success!")
  return Response(response="Failed!")


@app.route("/stopWorker", methods=["GET"])
def stopWorker():
  workerID = request.args["id"]
  try:
    priorityService.stopWorker(workerID)
    return Response(response="Success!")
  except KeyError:
    return Response(response="Failed!")


@app.route("/priority")
def priority():
  workerID = request.args["id"]
  try:
    queueState = json.dumps(priorityService.workerQueueState(workerID=workerID))
    return Response(response=queueState)
  except KeyError:
    return Response(response="Failed!")


if __name__ == "__main__":
  app.run(host='0.0.0.0', port=6566)


