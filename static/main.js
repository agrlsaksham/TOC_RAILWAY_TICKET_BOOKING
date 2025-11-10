// client-side interactivity for DFA tester
document.addEventListener("DOMContentLoaded", () => {
  const tokens = document.querySelectorAll(".token");
  const seqInput = document.getElementById("seq");
  const btnRun = document.getElementById("btn-run");
  const btnReset = document.getElementById("btn-reset");
  const traceEl = document.getElementById("trace");
  const curStateEl = document.getElementById("cur-state");
  const acceptBadge = document.getElementById("accept-badge");

  // click a single token -> step
  tokens.forEach(btn => {
    btn.addEventListener("click", async () => {
      const sym = btn.dataset.sym;
      const res = await fetch("/api/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: sym })
      });
      const j = await res.json();
      if (res.ok) {
        curStateEl.textContent = j.current;
        traceEl.textContent = JSON.stringify(j.trace);
        updateAccept(j.accepted);
      } else {
        alert(j.error || "error");
      }
    });
  });

  // run sequence
  btnRun.addEventListener("click", async () => {
    const seq = seqInput.value.trim();
    if (!seq) { alert("Enter a sequence like: a s v c d o"); return; }
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sequence: seq })
    });
    const j = await res.json();
    curStateEl.textContent = j.current;
    traceEl.textContent = JSON.stringify(j.trace);
    updateAccept(j.accepted);
  });

  // reset
  btnReset.addEventListener("click", async () => {
    const res = await fetch("/api/reset", { method: "POST" });
    const j = await res.json();
    curStateEl.textContent = j.current;
    traceEl.textContent = JSON.stringify(j.trace);
    updateAccept(j.accepted);
    seqInput.value = "";
  });

  function updateAccept(flag) {
    if (flag) {
      acceptBadge.style.display = "inline-block";
      acceptBadge.textContent = "ACCEPTED";
      acceptBadge.className = "accepted";
    } else {
      acceptBadge.style.display = "inline-block";
      acceptBadge.textContent = "NOT ACCEPTED";
      acceptBadge.className = "rejected";
    }
  }

  // init: call reset to sync server-side DFA
  btnReset.click();
});

