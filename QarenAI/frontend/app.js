const chatBox = document.getElementById("chat");
const input = document.getElementById("userInput");

function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = type;
  div.innerText = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage(text) {
  addMessage(text, "user");
  input.value = "";

  try {
    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    // إذا السيرفر رجع خطأ
    if (!res.ok) {
      const raw = await res.text(); // ممكن يكون HTML أو نص
      addMessage(`❌ خطأ من السيرفر (${res.status}): ${raw}`, "bot");
      return;
    }

    const data = await res.json();
    addMessage(data.reply || "❌ ما وصلني رد واضح من السيرفر", "bot");
  } catch (err) {
    addMessage(`❌ مشكلة اتصال: ${err.message}`, "bot");
  }
}

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && input.value.trim()) {
    sendMessage(input.value.trim());
  }
});




