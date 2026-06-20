// ================= API =================
const API = {
    updateStatus: '/update_status',
    getComplaints: '/get_complaints/',
    adminData: '/admin_data',
    submitComplaint: '/submit_complaint'
};

// ================= TOAST =================
function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerText = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ================= STATUS =================
function getStatusClass(status) {
    status = status.toLowerCase();
    return "status " + status;
}

// ================= ADMIN =================
function updateStatus(id, status) {
    fetch(API.updateStatus, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status })
    })
    .then(res => res.json())
    .then(() => {
        showToast("Status updated ✅");

        // reload admin data
        if (typeof loadAdminComplaints === "function") {
            loadAdminComplaints();
        }
    })
    .catch(() => showToast("Error ❌", "error"));
}

function loadAdminComplaints() {
    fetch(API.adminData)
    .then(res => res.json())
    .then(data => {
        let html = "";

        data.forEach(c => {
            html += `
            <div class="card">
                <div class="card-header">
                    <span><i class="fa fa-user"></i> ${c.name}</span>
                    <span class="${getStatusClass(c.status)}">
                        ${c.status}
                    </span>
                </div>

                <p class="complaint-text">
                    <i class="fa fa-comment"></i> ${c.complaint}
                </p>

                <p class="category">
                    PRN: ${c.prn || "N/A"}
                </p>

                <div class="btn-group">
                    <button class="btn accept" onclick="updateStatus(${c.id}, 'Accepted')">
                        Accept
                    </button>

                    <button class="btn reject" onclick="updateStatus(${c.id}, 'Rejected')">
                        Reject
                    </button>

                    <button class="btn resolve" onclick="updateStatus(${c.id}, 'Resolved')">
                        Resolve
                    </button>
                </div>
            </div>`;
        });

        document.getElementById("complaints").innerHTML = html;
    });
}

// ================= STUDENT =================
function submitComplaint() {
    const complaint = document.getElementById("complaint").value;
    const prn = document.getElementById("prn").value;
    const name = localStorage.getItem("user");

    if (!complaint) {
        showToast("Enter complaint ❌", "error");
        return;
    }

    fetch(API.submitComplaint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, prn, complaint })
    })
    .then(res => res.json())
    .then(() => {
        showToast("Complaint submitted 🚀");
        document.getElementById("complaint").value = "";
        loadUserComplaints();
    });
}

function loadUserComplaints() {
    const name = localStorage.getItem("user");

    fetch(API.getComplaints + name)
    .then(res => res.json())
    .then(data => {
        let html = "";

        data.forEach(c => {
            html += `
            <div class="card">
                <p class="complaint-text">${c.complaint}</p>
                <p class="${getStatusClass(c.status)}">${c.status}</p>
            </div>`;
        });

        document.getElementById("complaints").innerHTML = html;
    });
}

// ================= AUTO REFRESH =================
setInterval(() => {
    if (document.getElementById("complaints")) {

        // detect page type
        if (window.location.pathname.includes("admin")) {
            loadAdminComplaints();
        } else {
            loadUserComplaints();
        }

    }
}, 4000);
async function translateText(text, id){

    let resultDiv = document.getElementById("trans_" + id);
    resultDiv.innerHTML = "Translating...";

    try {
        const res = await fetch("https://libretranslate.de/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                q: text,
                source: "auto",
                target: "en",
                format: "text"
            })
        });
        const en = await res.json();

        const res2 = await fetch("https://libretranslate.de/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                q: text,
                source: "auto",
                target: "hi",
                format: "text"
            })
        });
        const hi = await res2.json();

        const res3 = await fetch("https://libretranslate.de/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                q: text,
                source: "auto",
                target: "mr",
                format: "text"
            })
        });
        const mr = await res3.json();

        resultDiv.innerHTML = `
            <b>🇬🇧 English:</b> ${en.translatedText}<br>
            <b>🇮🇳 Hindi:</b> ${hi.translatedText}<br>
            <b>🇲🇷 Marathi:</b> ${mr.translatedText}
        `;

    } catch(err){
        resultDiv.innerHTML = "❌ Translation failed";
        console.error(err);
    }
}