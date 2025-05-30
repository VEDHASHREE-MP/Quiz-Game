function startQuiz(level) {
    let category = document.getElementById("category").value;
    window.location.href = `/quiz/${category}/${level}`;
}

// Timer for each question
let timeLeft = 120;
let timer = setInterval(() => {
    if (timeLeft > 0) {
        timeLeft--;
        document.getElementById("timer").innerText = timeLeft;
    } else {
        clearInterval(timer);
        alert("Time's up!");
        document.forms[0].submit();
    }
}, 1000);