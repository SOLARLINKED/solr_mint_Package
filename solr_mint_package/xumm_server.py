#!/usr/bin/env python3
"""
Flask skeleton server to create Xumm payloads securely using server-side API keys.

Endpoints:
 - POST /payload/payment  -> create a payment payload (destination,drops,memo) -> returns sign URL/json
 - POST /payload/offer    -> create a payload to accept a sell-offer (offer_index) -> returns sign URL/json

Security:
 - In production, authenticate callers and use HTTPS. Keep XUMM keys in env.
"""
from flask import Flask, request, jsonify, abort
import os
from dotenv import load_dotenv

load_dotenv()
from xumm_client import create_payload, payload_sign_url_from_response, XummError

app = Flask(__name__)

@app.route("/payload/payment", methods=["POST"])
def create_payment_payload():
    body = request.get_json() or {}
    destination = body.get("destination")
    drops = body.get("drops")
    memo = body.get("memo", "SOLRAI-REC Testnet Purchase")
    if not destination or not drops:
        return abort(400, description="destination and drops are required")
    # Build minimal tx
    tx = {
        "TransactionType": "Payment",
        "Destination": destination,
        "Amount": str(drops),
    }
    try:
        resp = create_payload(tx)
    except XummError as e:
        return abort(500, description=str(e))
    return jsonify(resp)

@app.route("/payload/offer", methods=["POST"])
def create_offer_accept_payload():
    body = request.get_json() or {}
    offer_index = body.get("offer_index")
    if not offer_index:
        return abort(400, description="offer_index is required")
    # Build an NFTokenAcceptOffer tx
    tx = {
        "TransactionType": "NFTokenAcceptOffer",
        "NFTokenSellOffer": offer_index,
    }
    try:
        resp = create_payload(tx)
    except XummError as e:
        return abort(500, description=str(e))
    return jsonify(resp)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)))
