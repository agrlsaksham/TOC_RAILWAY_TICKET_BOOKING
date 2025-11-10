from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__, static_folder="static", template_folder="templates")

# --- DFA Definition (full-word symbols) -------------------------------

STATES = [
    "start", "logged_in", "journey_sel", "availability", "class_sel",
    "passenger_info", "payment_try", "ticket_issued", "error", "no_availability"
]

ALPHABET = {
    "auth", "select", "avail_ok", "avail_no", "choose",
    "details", "pay_ok", "pay_fail", "cancel", "timeout", "search"
}

START = "start"
ACCEPT = {"ticket_issued"}

# Total transition table (only non-error flow shown in diagram initially).
DELTA = {
    "start": {
        "auth": "logged_in", "select": "error", "avail_ok": "error", "avail_no":"error",
        "choose":"error","details":"error","pay_ok":"error","pay_fail":"error",
        "cancel":"error","timeout":"error","search":"start"
    },
    "logged_in": {
        "auth":"error","select":"journey_sel","avail_ok":"error","avail_no":"error",
        "choose":"error","details":"error","pay_ok":"error","pay_fail":"error",
        "cancel":"error","timeout":"error","search":"logged_in"
    },
    "journey_sel": {
        "auth":"error","select":"error","avail_ok":"availability","avail_no":"no_availability",
        "choose":"error","details":"error","pay_ok":"error","pay_fail":"error",
        "cancel":"error","timeout":"error","search":"journey_sel"
    },
    "availability": {
        "auth":"error","select":"error","avail_ok":"error","avail_no":"error",
        "choose":"class_sel","details":"error","pay_ok":"error","pay_fail":"error",
        "cancel":"error","timeout":"error","search":"availability"
    },
    "class_sel": {
        "auth":"error","select":"error","avail_ok":"error","avail_no":"error",
        "choose":"error","details":"passenger_info","pay_ok":"error","pay_fail":"error",
        "cancel":"error","timeout":"error","search":"class_sel"
    },
    "passenger_info": {
        "auth":"error","select":"error","avail_ok":"error","avail_no":"error",
        "choose":"error","details":"error","pay_ok":"ticket_issued","pay_fail":"payment_try",
        "cancel":"error","timeout":"error","search":"passenger_info"
    },
    "payment_try": {
        "auth":"error","select":"error","avail_ok":"error","avail_no":"error",
        "choose":"error","details":"error","pay_ok":"ticket_issued","pay_fail":"error",
        "cancel":"error","timeout":"error","search":"error"   # search during payment -> error
    },
    "ticket_issued": { sym: "error" for sym in ALPHABET },
    "error": { sym: "error" for sym in ALPHABET },
    "no_availability": { sym: "no_availability" for sym in ALPHABET }
}

# --- DFA simulator class -----------------------------------------------

class DFA:
    def __init__(self, states, alphabet, delta, start, accept):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.delta = delta
        self.start = start
        self.accept = set(accept)
        self.reset()

    def reset(self):
        self.cur = self.start
        self.trace = [self.cur]

    def step(self, symbol):
        prev = self.cur
        if symbol not in self.alphabet:
            self.cur = "error"
        else:
            # transition defined (DELTA is total)
            self.cur = self.delta.get(self.cur, {}).get(symbol, "error")
        self.trace.append(self.cur)
        return prev, self.cur

    def run(self, sequence):
        self.reset()
        for s in sequence:
            self.step(s)
        return self.cur, (self.cur in self.accept), self.trace

dfa = DFA(STATES, ALPHABET, DELTA, START, ACCEPT)

# --- Random trails (readable words) ------------------------------------

random_trails = [
    {"seq":"auth select avail_ok choose details pay_ok", "expected":"accept"},
    {"seq":"search auth select search avail_ok choose search details pay_ok", "expected":"accept"},
    {"seq":"auth select avail_ok search choose details pay_fail pay_ok", "expected":"accept"},
    {"seq":"auth search select search avail_ok choose details pay_ok", "expected":"accept"},
    {"seq":"search search auth select avail_ok choose details search pay_ok", "expected":"accept"},
    {"seq":"select avail_ok choose details pay_ok", "expected":"reject"},
    {"seq":"auth avail_ok choose details pay_ok", "expected":"reject"},
    {"seq":"auth select avail_no", "expected":"reject"},
    {"seq":"auth select avail_ok details pay_ok", "expected":"reject"},
    {"seq":"auth select avail_ok choose details pay_fail", "expected":"reject"},
    {"seq":"auth select avail_ok choose details pay_fail search", "expected":"reject"},
    {"seq":"auth select avail_ok choose cancel", "expected":"reject"},
    {"seq":"auth select avail_ok choose details pay_ok select", "expected":"reject"},
    {"seq":"auth select avail_no search select avail_ok choose details pay_ok", "expected":"reject"}
]

# --- Flask routes -------------------------------------------------------

@app.route("/")
def index():
    # legend for UI display
    legend = {
        "auth":"login/auth", "select":"select journey", "avail_ok":"availability OK", "avail_no":"availability NO",
        "choose":"choose class/seat", "details":"enter passenger details", "pay_ok":"payment OK", "pay_fail":"payment FAIL",
        "cancel":"cancel", "timeout":"timeout", "search":"search trains"
    }
    return render_template("index.html", alphabet=sorted(ALPHABET), legend=legend, states=STATES, start=START)

@app.route("/api/step", methods=["POST"])
def api_step():
    symbol = request.json.get("symbol", "").strip()
    if not symbol:
        return jsonify(error="no symbol provided"), 400
    prev, cur = dfa.step(symbol)
    return jsonify(previous=prev, current=cur, accepted=(cur in dfa.accept), trace=dfa.trace, used_symbol=symbol)

@app.route("/api/run", methods=["POST"])
def api_run():
    seq = request.json.get("sequence", "")
    tokens = [t for t in seq.strip().split() if t]
    final, accepted, trace = dfa.run(tokens)
    return jsonify(current=final, accepted=accepted, trace=trace)

@app.route("/api/reset", methods=["POST"])
def api_reset():
    dfa.reset()
    return jsonify(current=dfa.cur, trace=dfa.trace, accepted=(dfa.cur in dfa.accept))

@app.route("/api/random", methods=["GET"])
def api_random():
    return jsonify(random.choice(random_trails))

if __name__ == "__main__":
    app.run(debug=True)
