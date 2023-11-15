document.addEventListener("DOMContentLoaded", () => {
    //code for dynamic logout
    function home(){
        document.querySelector("body > nav > div.logo").addEventListener("click", () => {
            location.href = location.origin;
        })
    }
    home();
    function logout() {
        menu = document.querySelector('#menu')
        lougout = document.querySelector('#logout')

        menu.addEventListener('click', () => {
            //show the lougout and trigger the clear function
            lougout.className = 'on'
            lougout.addEventListener('click', () => {
                location.href = `${location.origin}/logout`
            })
            setTimeout(() => {
                lougout.className = 'off'
            }, 5000)
        })
    }
    logout()
    function greeting() {
        greeting_container = document.querySelector('#greetings_text')
        time = parseInt(new Date().getHours())
        console.log(time)

        if (time < 12) {
            greeting_container.innerHTML = 'Good Morning, '
        } else if (time >= 12 && time <= 16) {
            greeting_container.innerHTML = 'Good Afternoon, '
        } else {
            greeting_container.innerHTML = 'Good Evening, '
        }
    }
    greeting()

    function generate_control() {
        var action = document.querySelector("#submit_generation");
        var amount = document.querySelector("#amountOfFiles");

        amount.addEventListener("input", () => {
            action.removeAttribute("disabled", "false")
            if (parseInt(amount.value) > 20) {
                action.value = "Reduce amount of questions";
                action.setAttribute("disabled", "true");
            }
            else if (parseInt(amount.value) <= 1) {
                action.value = "Generate 1 Question";
            }
            else {
                action.value = `Generate ${amount.value} Questions`;
            }
        })
    }
    generate_control();

    function loadFiles() {
        //for all the years add E.L's
        classes_selectable = document.querySelectorAll(".is_selected_class");

        classes_selectable.forEach(element => {
            console.log("yes");
            element.addEventListener("click", () => {
                //for each create a new files
                classifier = element.value

                //fetch info on that class
                fetch("/list_files", {
                    method: "POST",
                    headers: {
                        "Content-Type": 'application/json'
                    },
                    body: JSON.stringify({
                        class: classifier
                    })
                })
                    .then(response => response.json())
                    .then(data => {
                        //now create DOM objects of files
                        console.log(data);
                        data = data["files"]
                        //target parent dom
                        let file_selection_container = document.querySelector("#file_selection_container");
                        file_selection_container.innerHTML = "";
                        if (data == null || data.length < 1) {
                            file_selection_container.innerHTML = "<h3 style='color: red; padding: 4px; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center;'>You do not have any files for this class</h3>"
                        }
                        data.forEach(datum => {
                            let file_selectable = document.createElement('div');
                            file_selectable.className = "file_selectable";
                            file_selectable.innerHTML = `<div>
                            <span id="doc_id" hidden="true">${datum["id"]}</span>
                            <input type="checkbox" class="selectable_file" name="selected_file" id="selected_file" />
                            <img src="/static/images/illustrations/top_nav/add-file.png" alt="">
                        </div>
                        <h4>${datum["name"]}</h4>`
                            file_selection_container.appendChild(file_selectable);
                        })

                    })
            })
        });
    }

    loadFiles();

    function re_load_data() {
        function getCorrectAnswer() {

            var checks = document.querySelectorAll(".select_correct");
            var correctAnswers = []
            checks.forEach(element => {
                correctAnswers.push(element.nextElementSibling.value)
            });

            return correctAnswers
        }
        function getCorrectAnswer(event) {

            var checks = document.querySelectorAll(".select_correct");
            let correctAnswers = []
            checks.forEach(element => {
                if (element.checked) {
                    correctAnswers.push(element.nextElementSibling.value)
                }
            });

            return correctAnswers
        }
        function quester() {
            let quests = []
            document.querySelectorAll(".Question_node").forEach(element => {
                quests.push(
                    element.value)
            })
            return quests
        }
        function ans() {
            let answer = []
            document.querySelectorAll(".answers").forEach(element => {
                answer.push(element.value)
            })
            return answer
        };
        var questions = quester();
        var answers = ans();
        var correctAnswers = getCorrectAnswer();

        var response = []
        var index = 0
        questions.forEach(question => {
            response.push({ "question": question, "answers": answers.splice(0, 4), "correctAnswer": correctAnswers[index] })
            index += 1;
        })
        return response
    }
    async function generate_questions() {
        //create a question_role dom element and add to body
        var question_role = document.createElement("div");
        question_role.className = "questions_role";
        question_role.innerHTML = '<img src="/static/images/illustrations/loading.gif" style="margin: auto;">'

        document.querySelector("body").append(question_role);

        var isQuiz = document.querySelector("#isQuiz").checked == true ? true : false;
        var shuffle = document.querySelector("#isShuffled").checked == true ? true : false;
        function getYear() {
            let year = null;
            document.querySelectorAll(".is_selected_class").forEach(element => {
                if (element.checked == true) {
                    year = element.parentElement.parentElement.children[1].innerHTML;
                };
            })
            return year
        }
        function getFiles() {
            let files = [];
            document.querySelectorAll(".selectable_file").forEach(element => {
                if (element.checked) {
                    files.push(element.previousElementSibling.textContent)
                }
            })
            return files
        }
        var year = getYear();

        var formTitle = document.querySelector("#formTitle").value;
        var description = document.querySelector("#formDescription").value;
        var documentTitle = document.querySelector("#documentTitle").value;
        var amount = parseInt(document.querySelector("#amountOfFiles").value);
        var files = getFiles();
        document.querySelector("body > form").remove();
        document.querySelector("body > div.files_div").remove();
        var questions_data_reserve = null;
        //fetch the neccessary data 
        
        await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                year: year,
                formTitle: formTitle,
                description: description,
                documentTitle: documentTitle,
                amount: amount,
                files: files,
                isQuiz: isQuiz,
                shuffle: shuffle
            })
        })
            .then(response => response.json())
            .then(data => {
                question_role.innerHTML = "";
                data = data["questions"]
                let headers = data["headers"]
                let questions = data["questions"]
                questions_data_reserve = questions

                //create the header dom
                let header_dom = document.createElement("div");
                header_dom.className = "headers";
                header_dom.innerHTML = `
                    <input type="text" id="DocumentTitle" placeholder="Title" value="${headers[0]}">
                    <input type="text" placeholder="Description" id="DocumentDescription" value="${headers[1]}">
                    `
                console.log(header_dom)
                question_role.appendChild(header_dom);

                //create the questions 
                var questions_dom = document.createElement("div");
                questions_dom.className = "questions";
                questions_dom.id = "question_container";
                question_role.appendChild(questions_dom)
                var questions_dom = document.querySelector("#question_container");
                console.log(questions_dom);
                questions.forEach(question => {
                    questions_dom.innerHTML += `
                    <form method="post" action="#" class="questions_container">
                <div class="question">
                    <input type="text" placeholder="Question" value="${question["question"]}" class="Question_node">
                    <div class="answer_div">
                        <input type="radio" name="correct" class="select_correct">
                        <input type="text" name="answers" id="" value="${question["answers"][0]}" class="answers">
                    </div>
                    <div class="answer_div">
                        <input type="radio" name="correct"  class="select_correct">
                        <input type="text" name="answers" id="" value="${question["answers"][1]}" class="answers">
                    </div>
                    <div class="answer_div">
                        <input type="radio" name="correct" class="select_correct">
                        <input type="text" name="answers" id="" class="answers" value="${question["answers"][2]}">
                    </div>
                    <div class="answer_div">
                        <input type="radio" name="correct" class="select_correct" checked="true">
                        <input type="text" name="answers" id="" class="answers" value="${question["correctAnswer"]}">
                    </div>
                    </div></form>`;
                })
                questions_dom.innerHTML += `
                <div class="final_submit">
                <button>Save as Drafts</button>
                <button>Upload Document</button></div>`;
                question_role.appendChild(questions_dom);
                console.log("DONE");
                
            })
            .catch(err => {
                console.log(err);
                return null
            })

            
            

            return {
                "isQuiz": isQuiz,
                "shuffle": shuffle,
                "year": year
            }

           
    }
    function start_generation_flow() {
        //ooh God
        

        var generator_button = document.querySelector("#submit_generation");

        generator_button.addEventListener("click", async () => {

            let DATA_GOTTEN_FROM_FORM = await generate_questions();
            console.log(DATA_GOTTEN_FROM_FORM);
            if (DATA_GOTTEN_FROM_FORM == null){
                console.log("AN ERROR OCCURED. NET::ERR .........TIMEOUt");
                location.href = location.origin()
                return false
            }
            upload(DATA_GOTTEN_FROM_FORM);
        })
    }

    function send_save_request(url, data) {
        var fullData = {};
        fullData["headers"] = [
            document.querySelector("#DocumentTitle").value,
            document.querySelector("#DocumentDescription").value,
        ]
        fullData["settings"] = {
            "isQuiz": data["isQuiz"],
            "shuffle": data["shuffle"],
            "year": data["year"]
        }
        fullData["questions"] = re_load_data();


        console.log(fullData["settings"]["year"]);

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                data: fullData
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log(data["message"]);
                if (data["message"] == "success") {
                    console.log("You have successfully uploaded your form");
                    location.href = `${location.origin}/`;
                }
                else {
                    console.log("An Error occured..... Please try again...")
                }
            })
    }

    function upload(data) {

        setTimeout(() => {
            console.log("done waiting")
            document.querySelectorAll(".final_submit button").forEach(element => {
                console.log("deudieiudheiudh");
                element.addEventListener("click", (event) => {
                    console.log("Dedueiudheiuh")
                    if (event.target.innerHTML == "Upload Document") {
                        var url = "/upload";
                        send_save_request(url, data);
                    }
                    else {
                        var url = "/draft_question";
                        send_save_request(url, data);

                    }


                })
            })
        }, 1000);
    }


    start_generation_flow();
})