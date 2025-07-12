from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from dateutil.parser import isoparse
from .extensions import mongo
import json

webhook = Blueprint('webhook', __name__, url_prefix ='/webhook')

@webhook.route('/events', methods = ['GET'])
def api_root():
    since_param = request.args.get("since")
    query = {}
    if since_param:
        try:
            since_dt = isoparse(since_param)
            query = {"timestamp": {"$gt": since_dt}}
        except ValueError:
            return jsonify({"error": "Invalid timestamp format"}), 400
        
    print("Querying for events after:", query.get("timestamp", {}).get("$gt"))
    events = list(mongo.db.events.find(query).sort("timestamp", -1))
    print(since_param)
    # print(since_dt)
    for e in events:
        e["_id"] = str(e["_id"])
    return jsonify(events)

@webhook.route('/receiver', methods = ['POST'])
def receiver():
    allowed_actions = {"PUSH", "PULL REQUEST", "MERGE"}
    if request.headers.get('Content-Type') == 'application/json':
        event_type = request.headers.get("X-GitHub-Event")
        payload = request.get_json()
        delivery_id = request.headers.get("X-GitHub-Delivery")
        print(payload)
        data = {
            "_id" : None, # to prevent duplication
            "request_id": None,
            "author" : None,
            "action" : None,
            "from_branch" : None,
            "to_branch" : None,
            "timestamp" : None,
        }
        # Handle push event
        if event_type == "push":
            commit_hash = payload.get("after")
            data.update({
                "_id": commit_hash,
                "request_id": commit_hash,
                "author": payload.get("pusher", {}).get("name"),
                "action": "PUSH",
                "from_branch": None,
                "to_branch": payload.get("ref", "").split("/")[-1],
                "timestamp": isoparse(payload.get("head_commit", {}).get("timestamp") or datetime.now(timezone.utc).isoformat())
            })

        
        # Handle pull request event
        elif event_type == "pull_request":
            pr = payload.get("pull_request", {})
            pr_action = payload.get("action")

            action_type = "MERGE" if pr_action == "closed" and pr.get("merged") else "PULL REQUEST"

            data.update({
                "_id": str(pr.get("id")),
                "request_id": str(pr.get("id")),
                "author": pr.get("user", {}).get("login"),
                "action": action_type,
                "from_branch": pr.get("head", {}).get("ref"),
                "to_branch": pr.get("base", {}).get("ref"),
                "timestamp": isoparse(
                    pr.get("merged_at") if action_type == "MERGE" else
                    pr.get("updated_at") or pr.get("created_at") or
                    datetime.now(timezone.utc).isoformat()
                )
            })
        else:
            return jsonify({"message": f"Ignored unsupported event: {event_type}"}), 200
        
        if data["action"] not in allowed_actions:
            return jsonify({"error": "Invalid action type"}), 400
        
        print(f"Time stamp  {data['timestamp']}")
        mongo.db.events.replace_one({"_id":data["_id"]}, data, upsert = True)
        return jsonify({"status": "received"}), 200
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    