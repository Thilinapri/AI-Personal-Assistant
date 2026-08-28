async function loadStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        const statusElement =
            document.getElementById("system-status");

        statusElement.textContent =
            `Web: ${data.web} | Database: ${data.database}`;

    } catch (error) {
        console.error("Status loading failed:", error);
    }
}


async function loadMemories() {
    try {
        const response = await fetch("/api/memories");
        const memories = await response.json();

        const memoryList =
            document.getElementById("memory-list");

        memoryList.innerHTML = "";

        if (memories.length === 0) {
            memoryList.textContent =
                "No memories stored yet.";

            return;
        }

        memories.forEach((memory) => {

            const card =
                document.createElement("div");

            card.className = "memory-card";

            card.innerHTML = `
                <h3>${memory.title}</h3>

                <p>
                    ${memory.content}
                </p>

                <p>
                    <strong>Category:</strong>
                    ${memory.category}
                </p>

                <p>
                    <strong>Date:</strong>
                    ${memory.date || "Not specified"}
                </p>

                <p>
                    <strong>Time:</strong>
                    ${memory.time || "Not specified"}
                </p>

                <p>
                    <strong>Status:</strong>
                    ${memory.status}
                </p>

                <p>
                    <strong>Seen:</strong>
                    ${memory.seen_count} time(s)
                </p>
            `;

            memoryList.appendChild(card);
        });

    } catch (error) {
        console.error(
            "Memory loading failed:",
            error
        );
    }
}


async function loadReminders() {
    try {
        const response = await fetch("/api/reminders");
        const reminders = await response.json();

        const reminderList =
            document.getElementById("reminder-list");

        reminderList.innerHTML = "";

        if (reminders.length === 0) {
            reminderList.textContent =
                "No reminders scheduled.";

            return;
        }

        reminders.forEach((reminder) => {

            const card =
                document.createElement("div");

            card.className = "memory-card";

            card.innerHTML = `
                <h3>${reminder.title}</h3>

                <p>${reminder.content}</p>

                <p>
                    <strong>Reminder time:</strong>
                    ${reminder.reminder_time}
                </p>

                <p>
                    <strong>Status:</strong>
                    ${reminder.status}
                </p>
            `;

            reminderList.appendChild(card);
        });

    } catch (error) {
        console.error(
            "Reminder loading failed:",
            error
        );

        document.getElementById(
            "reminder-list"
        ).textContent =
            "Failed to load reminders.";
    }
}


async function searchMemories() {
    const input =
        document.getElementById("memory-search-input");

    const resultsContainer =
        document.getElementById("search-results");

    const query = input.value.trim();

    if (!query) {
        resultsContainer.textContent =
            "Enter a question first.";

        return;
    }

    resultsContainer.textContent =
        "Searching...";

    try {
        const response = await fetch(
            `/api/memories/search?q=${encodeURIComponent(query)}`
        );

        const results = await response.json();

        resultsContainer.innerHTML = "";

        if (results.length === 0) {
            resultsContainer.textContent =
                "No matching memories found.";

            return;
        }

        results.forEach((memory) => {

            const card =
                document.createElement("div");

            card.className = "memory-card";

            card.innerHTML = `
                <h3>${memory.title}</h3>

                <p>${memory.content}</p>

                <p>
                    <strong>Similarity:</strong>
                    ${memory.score.toFixed(3)}
                </p>
            `;

            resultsContainer.appendChild(card);
        });

    } catch (error) {
        console.error(
            "Memory search failed:",
            error
        );

        resultsContainer.textContent =
            "Search failed.";
    }
}


document
    .getElementById("memory-search-button")
    .addEventListener(
        "click",
        searchMemories
    );

document
    .getElementById("memory-search-input")
    .addEventListener(
        "keydown",
        function (event) {
            if (event.key === "Enter") {
                searchMemories();
            }
        }
    );


loadStatus();
loadMemories();
loadReminders();