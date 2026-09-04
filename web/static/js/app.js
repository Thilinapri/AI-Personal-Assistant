let knownTriggeredReminderIds = new Set();
let reminderStateInitialized = false;

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


async function clearAllMemories() {

    const confirmation = prompt(
        "This will permanently delete ALL memories and reminders.\n\nType CLEAR to continue."
    );

    if (confirmation !== "CLEAR") {
        return;
    }

    try {
        const response = await fetch(
            "/api/memories",
            {
                method: "DELETE",
            }
        );

        if (!response.ok) {
            throw new Error(
                "Clear memories failed"
            );
        }

        await loadMemories();
        await loadReminders();

        const resultsContainer =
            document.getElementById(
                "search-results"
            );

        resultsContainer.replaceChildren();

        alert(
            "All memories and reminders were deleted."
        );

    } catch (error) {
        console.error(
            "Clearing memories failed:",
            error
        );

        alert(
            "Failed to clear memories."
        );
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

            const editButton =
                document.createElement("button");

            editButton.className =
                "edit-memory-button";

            editButton.textContent =
                "Edit";

            editButton.addEventListener(
                "click",
                () => showEditForm(memory, card)
            );

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

            const actions =
                document.createElement("div");

            actions.className =
                "memory-actions";

            actions.appendChild(editButton);
            actions.appendChild(deleteButton);

            card.appendChild(actions);

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

        const triggeredReminders = reminders.filter(
            (reminder) =>
                reminder.status === "triggered"
        );

        if (!reminderStateInitialized) {

            triggeredReminders.forEach(
                (reminder) => {
                    knownTriggeredReminderIds.add(
                        reminder.id
                    );
                }
            );

            reminderStateInitialized = true;

        } else {

            triggeredReminders.forEach(
                (reminder) => {

                    if (
                        !knownTriggeredReminderIds.has(
                            reminder.id
                        )
                    ) {

                        alert(
                            `REMINDER\n\n${reminder.title}\n\n${reminder.content}`
                        );

                        knownTriggeredReminderIds.add(
                            reminder.id
                        );
                    }
                }
            );
        }

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


function showEditForm(memory, card) {

    const form =
        document.createElement("form");

    form.className =
        "memory-edit-form";

    const titleLabel =
        document.createElement("label");

    titleLabel.textContent = "Title";

    const titleInput =
        document.createElement("input");

    titleInput.type = "text";
    titleInput.value = memory.title;

    const contentLabel =
        document.createElement("label");

    contentLabel.textContent = "Content";

    const contentInput =
        document.createElement("textarea");

    contentInput.value = memory.content;

    const categoryLabel =
        document.createElement("label");

    categoryLabel.textContent = "Category";

    const categoryInput =
        document.createElement("input");

    categoryInput.type = "text";
    categoryInput.value = memory.category;

    const dateLabel =
        document.createElement("label");

    dateLabel.textContent = "Date";

    const dateInput =
        document.createElement("input");

    dateInput.type = "date";
    dateInput.value = memory.date || "";

    const timeLabel =
        document.createElement("label");

    timeLabel.textContent = "Time";

    const timeInput =
        document.createElement("input");

    timeInput.type = "time";
    timeInput.value = memory.time || "";

    const notificationLabel =
        document.createElement("label");

    const notificationInput =
        document.createElement("input");

    notificationInput.type = "checkbox";
    notificationInput.checked =
        memory.notification;

    notificationLabel.appendChild(
        notificationInput
    );

    notificationLabel.appendChild(
        document.createTextNode(
            " Enable reminder"
        )
    );

    const saveButton =
        document.createElement("button");

    saveButton.type = "submit";
    saveButton.textContent = "Save";

    const cancelButton =
        document.createElement("button");

    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";

    cancelButton.addEventListener(
        "click",
        loadMemories
    );

    form.appendChild(titleLabel);
    form.appendChild(titleInput);

    form.appendChild(contentLabel);
    form.appendChild(contentInput);

    form.appendChild(categoryLabel);
    form.appendChild(categoryInput);

    form.appendChild(dateLabel);
    form.appendChild(dateInput);

    form.appendChild(timeLabel);
    form.appendChild(timeInput);

    form.appendChild(notificationLabel);

    const actions =
        document.createElement("div");

    actions.className =
        "memory-actions";

    actions.appendChild(saveButton);
    actions.appendChild(cancelButton);

    form.appendChild(actions);

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const updatedMemory = {
                category:
                    categoryInput.value.trim(),

                title:
                    titleInput.value.trim(),

                content:
                    contentInput.value.trim(),

                date:
                    dateInput.value,

                time:
                    timeInput.value,

                notification:
                    notificationInput.checked,
            };

            await saveMemoryEdit(
                memory.id,
                updatedMemory
            );
        }
    );

    card.replaceChildren(form);
}


async function saveMemoryEdit(
    memoryId,
    memory
) {

    if (
        !memory.title
        || !memory.content
        || !memory.category
    ) {
        alert(
            "Title, content and category are required."
        );

        return;
    }

    try {
        const response = await fetch(
            `/api/memories/${memoryId}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body: JSON.stringify(
                    memory
                ),
            }
        );

        if (!response.ok) {

            const errorData =
                await response.json();

            throw new Error(
                errorData.error
                || "Edit failed"
            );
        }

        await loadMemories();
        await loadReminders();

        const searchResults =
            document.getElementById(
                "search-results"
            );

        searchResults.replaceChildren();

    } catch (error) {

        console.error(
            "Memory editing failed:",
            error
        );

        alert(
            `Failed to edit memory: ${error.message}`
        );
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

document
    .getElementById(
        "clear-memories-button"
    )
    .addEventListener(
        "click",
        clearAllMemories
    );


loadStatus();
loadMemories();
loadReminders();

// Keep dashboard status and reminders up to date.
setInterval(loadStatus, 5000);
setInterval(loadReminders, 5000);