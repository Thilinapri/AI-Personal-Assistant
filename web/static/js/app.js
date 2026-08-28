function createDetailRow(label, value) {
    const paragraph =
        document.createElement("p");

    const labelElement =
        document.createElement("strong");

    labelElement.textContent =
        `${label}: `;

    paragraph.appendChild(
        labelElement
    );

    paragraph.appendChild(
        document.createTextNode(value)
    );

    return paragraph;
}


async function loadStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        const statusElement =
            document.getElementById("system-status");

        const toggleButton =
            document.getElementById(
                "listening-toggle-button"
            );

        statusElement.textContent =
            `Web: ${data.web} | Database: ${data.database} | Listening: ${data.listening}`;

        if (data.listening === "active") {
            toggleButton.textContent =
                "Pause Listening";

            toggleButton.dataset.enabled =
                "true";
        } else {
            toggleButton.textContent =
                "Resume Listening";

            toggleButton.dataset.enabled =
                "false";
        }

    } catch (error) {
        console.error("Status loading failed:", error);
    }
}


async function toggleListening() {

    const button =
        document.getElementById(
            "listening-toggle-button"
        );

    const currentlyEnabled =
        button.dataset.enabled === "true";

    const newState =
        !currentlyEnabled;

    button.disabled = true;

    try {
        const response = await fetch(
            "/api/listening",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body: JSON.stringify({
                    enabled: newState,
                }),
            }
        );

        if (!response.ok) {
            throw new Error(
                "Listening update failed"
            );
        }

        await loadStatus();

    } catch (error) {
        console.error(
            "Listening control failed:",
            error
        );

        alert(
            "Failed to change listening state."
        );

    } finally {
        button.disabled = false;
    }
}


async function loadMemories() {
    try {
        const response = await fetch("/api/memories");
        const memories = await response.json();

        const memoryList =
            document.getElementById("memory-list");

        memoryList.replaceChildren();

        if (memories.length === 0) {
            memoryList.textContent =
                "No memories stored yet.";

            return;
        }

        memories.forEach((memory) => {

            const card =
                document.createElement("div");

            card.className = "memory-card";

            const title =
                document.createElement("h3");

            title.textContent =
                memory.title;

            const content =
                document.createElement("p");

            content.textContent =
                memory.content;

            const deleteButton =
                document.createElement("button");

            deleteButton.className =
                "delete-memory-button";

            deleteButton.textContent =
                "Delete";

            deleteButton.addEventListener(
                "click",
                () => deleteMemory(memory.id)
            );

            card.appendChild(title);
            card.appendChild(content);

            card.appendChild(
                createDetailRow(
                    "Category",
                    memory.category
                )
            );

            card.appendChild(
                createDetailRow(
                    "Date",
                    memory.date || "Not specified"
                )
            );

            card.appendChild(
                createDetailRow(
                    "Time",
                    memory.time || "Not specified"
                )
            );

            card.appendChild(
                createDetailRow(
                    "Status",
                    memory.status
                )
            );

            card.appendChild(
                createDetailRow(
                    "Seen",
                    `${memory.seen_count} time(s)`
                )
            );

            card.appendChild(deleteButton);

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

        reminderList.replaceChildren();

        if (reminders.length === 0) {
            reminderList.textContent =
                "No reminders scheduled.";

            return;
        }

        reminders.forEach((reminder) => {

            const card =
                document.createElement("div");

            card.className = "memory-card";

            const title =
                document.createElement("h3");

            title.textContent =
                reminder.title;

            const content =
                document.createElement("p");

            content.textContent =
                reminder.content;

            card.appendChild(title);
            card.appendChild(content);

            card.appendChild(
                createDetailRow(
                    "Reminder time",
                    reminder.reminder_time
                )
            );

            card.appendChild(
                createDetailRow(
                    "Status",
                    reminder.status
                )
            );

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


async function deleteMemory(memoryId) {

    const confirmed = confirm(
        "Are you sure you want to delete this memory?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `/api/memories/${memoryId}`,
            {
                method: "DELETE",
            }
        );

        if (!response.ok) {
            throw new Error("Delete failed");
        }

        loadMemories();
        loadReminders();

    } catch (error) {
        console.error(
            "Memory deletion failed:",
            error
        );

        alert("Failed to delete memory.");
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

        resultsContainer.replaceChildren();

        if (results.length === 0) {
            resultsContainer.textContent =
                "No matching memories found.";

            return;
        }

        results.forEach((memory) => {

            const card =
                document.createElement("div");

            card.className = "memory-card";

            const title =
                document.createElement("h3");

            title.textContent =
                memory.title;

            const content =
                document.createElement("p");

            content.textContent =
                memory.content;

            card.appendChild(title);
            card.appendChild(content);

            card.appendChild(
                createDetailRow(
                    "Similarity",
                    memory.score.toFixed(3)
                )
            );

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

document
    .getElementById(
        "listening-toggle-button"
    )
    .addEventListener(
        "click",
        toggleListening
    );


loadStatus();
loadMemories();
loadReminders();