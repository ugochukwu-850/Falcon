import datetime
import io
import time
from bson import ObjectId
import flask
from flask import Flask, render_template, request, redirect, jsonify

# imports for google auth
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload

# database
from database import question_cursor, serialize_Files, users as user_cursor, drafts_cursor, files as file_cursor, serialize_Questions, serialize_user


# llm imports
from langchain.document_loaders import UnstructuredPDFLoader, UnstructuredWordDocumentLoader, UnstructuredFileIOLoader

from langchain.indexes import VectorstoreIndexCreator

# misc
import os
import json
from helpers import login_required, credentials_to_dict, ordinal, spliter


app = Flask("Falcon")
app.secret_key = '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'

app.jinja_env.filters["spliter"] = spliter
app.config["TEMPLATES_AUTO_RELOAD"] = True
OPENAI_KEY = os.getenv("OPENAI_KEY")

CLASSES = [f"Year {x+1}" for x in range(6, 12)]

CLIENT_SECRETS_FILE = "client_secrets.json"

SCOPES = ["https://www.googleapis.com/auth/forms.body", "openid", "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/userinfo.profile"]
API_SERVICE_NAME = 'forms'
API_VERSION = 'v1'


@app.route("/")
def index():
    """Render home page"""
    if "user" not in flask.session:
        return redirect("/authorize")
    
    message = flask.get_flashed_messages()[0] if len(
        flask.get_flashed_messages()) >= 1 else None
    
    # add the questions and files to session under user
    questions = serialize_Questions(question_cursor.find(
        {"teacher": flask.session["user"]["email"]}), many=True)
    
    files = serialize_Files(many=True, file=file_cursor.find(
        {"teacher": flask.session["user"]["email"]}))
    
    if len(questions) == 0:
        questions.append({
            "title": "You do not have any files",
            "created": "Today",
            "link": "localhost:8080/generate"
        })
        
    if len(files) == 0:
        files.append({
            "name": "You do not have any files.default",
            "created": "Today",
            "class": "Default"
        })
        

    return render_template("index.html", message=message, files=files, questions=questions, user=flask.session["user"], add_file=True, footer=True)


@app.route('/logout')
def logout():
    if 'credentials' in flask.session:
        del flask.session["user"]
    return redirect("/")


@app.route("/load", methods=["POST", "GET"])
def load_note():
    """
    Uploads a document to drive and stores key information like title and creation date
    """

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    # Get the file from the form data (assuming the file input field has the name 'file')
    file = flask.request.files['file']
    title = request.form.get('title')
    classes = request.form.get("class")

    # Create the file metadata
    file_metadata = {
        'name': f"{request.form.get('title')}.{file.filename.split('.')[1]}"}

    # Prepare the media upload
    media = MediaIoBaseUpload(io.BytesIO(file.read()),
                              mimetype=file.content_type, resumable=True)
    flask.session['credentials'] = credentials_to_dict(credentials)
    try:
        # Upload the file to Google Drive
        service = build('drive', 'v3', credentials=credentials)

        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata,
                                      media_body=media, fields='id').execute()

        # Print the file ID
        file_id = f'{file.get("id")}'

        # Optionally, you can redirect the user to a success page or perform any other actions
        flask.flash(message="You have uploaded your file successfully!! ")
        _ = file_cursor.insert_one({
            "class": classes,
            "name": title,
            "teacher": flask.session["user"]["email"],
            "created": f"{ordinal(datetime.datetime.now().day)},{datetime.datetime.now().strftime('%B %Y')}",
            "id": file_id,
        })

        user_cursor.find_one_and_update({"email": flask.session["user"]["email"]}, {
                                        "$inc": {'total_files': 1}})

        flask.session["user"]["total_files"] += 1
        return redirect("/")

    except Exception as error:
        # Handle errors
        print(f'An error occurred: {error}')
        flask.flash(message="Error Loading your file. Try again")
        return redirect("/")


@app.route("/list_files", methods=["GET", "POST"])
def list_file():
    """
    Lists files - Documents from the users drive relating to a class param 
    ```python 
    or
    renders the files page showing all documents we have id's to in form of their classess
    """
    if request.method == "GET":
        data = {x: [] for x in CLASSES}
        files = serialize_Files(file_cursor.find({"teacher": flask.session["user"]["email"]}), many=True)
        for x in files:
            for y in CLASSES:
                if x["class"] == y:
                    data[y].append(x)
                    
        if len(files) == 0:
            print(files)
            data = {
                "No File Found": [{
                    "class": "No Class",
                    "name": "Deafult File",
                    "created": "today",
                }]
            }
       
        return render_template("index.html",add_file=True, filehome=data, user=flask.session["user"], footer=True)
    else:
        try:
            classes = request.get_json()
            print(classes)
            classes = classes["class"]
            if classes == "all":
                data = {x: [] for x in CLASSES}
                files = file_cursor.find({"teacher": flask.session["user"]["email"]})
                for x in files:
                    for y in CLASSES:
                        if x["class"] == y:
                            data[y].append(x)
                return jsonify(files=data, message="success", status_code=200)
            else:
                files = serialize_Files(file_cursor.find(
                    {"class": classes, "teacher": flask.session["user"]["email"]}), many=True)
                print(files)
            return jsonify(files=files, message="success", status_code=200)
        except Exception as e:
            print(e)
            return jsonify(files=None, message="Error", status_code=403)


@app.route("/questions")
def questions():
    """Load questions page """
    questions = serialize_Questions(question_cursor.find(
        {"teacher": flask.session["user"]["email"]}), many=True)
    
    if len(questions) == 0:
        questions.append({
            "title": "You do not have any files",
            "created": "Today",
            "link": "localhost:8080/generate"
        })
    return render_template("index.html", questions=questions, user=flask.session["user"], footer=False)


@app.route("/generate", methods=["POST", "GET"])
# @login_required()()
def generate_endpoint():
    if request.method == "GET":
        # load the UI without data
        notes = serialize_Files(file_cursor.find(
            {"class": "Year 7"}), many=True)
        return render_template("index.html", create_quiz=True, user=flask.session["user"], notes=notes)
    else:
        # get the data from the front end
        action_resources = request.get_json()
        
        #reload credentials
        credentials = google.oauth2.credentials.Credentials(
            **flask.session['credentials'])
        
        #build service
        service = build('drive', 'v3', credentials=credentials)
        
        #load the required files to readable buffers
        files = load_documents(action_resources["files"], service=service)
        
        #run recursive engine to get questions
        questions = recursive_engine(
            TRQ=action_resources["amount"], developement=True, documents=files)
        
        #shadow questions with new data, required for F.E parsing
        questions = {
            "headers": [action_resources["formTitle"],action_resources["description"]],
            "questions": questions
        } 

        flask.flash(
            message=f"Successfully generated {action_resources['amount']} questions for {action_resources['year']}....")
        
        #THE WORK IS DONE
        return jsonify(questions=questions, message="success", status_code=200)


@app.route("/upload", methods=["POST", "GET"])
def upload_endpoint():
    # get data from frontend and upload the data with users docs key
    questions_confirmed_data = request.get_json()['data']
    
    # upload the data to docs
    response = upload(questions_confirmed_data)
    
    #based on status message 
    if response["message"] == "success":
        
        #update database
        question_cursor.insert_one({
            "title": response["arg_cache"]['info']['title'],
            "created": f"{ordinal(datetime.datetime.now().day)},{datetime.datetime.now().strftime('%B %Y')}",
            "question_id": response["arg_cache"]["formId"],
            "teacher": flask.session["user"]["email"]
        })

        user_cursor.find_one_and_update({"email": flask.session["user"]["email"]}, {
                                        "$inc": {'total_questions': 1}})
        
        flask.session["user"]["total_questions"] += 1
        
        #return response
        return jsonify(status_code=200, message="success", arguments={})
    else:
        #or errors
        return jsonify(status_code=500, message="Error occured whilst saving the document to google forms", extra_data=response["summary"])


@app.route("/draft_question", methods=["POST"])
def save_draft():
    data = request.get_json()

    if data and "data" in data:
        data = data["data"]

        try:
            drafts_cursor.insert_one({
                "teacher": flask.session["user"]["email"],
                "questions": data,
                "created": f"{ordinal(datetime.datetime.now().day)},{datetime.datetime.now().strftime('%B %Y')}"
            })

            user_cursor.find_one_and_update({"email": flask.session["user"]["email"]}, {
                                            "$inc": {'total_drafts': 1}})
            
            #UPDATE SESSION 
            user = flask.session["user"]
            user["total_drafts"] += 1
            flask.session["user"] = user
            
            # THE WORK IS DONE
            return jsonify(message="success", args="Your questions have been saved to drafts....", status_code=200)
        except Exception as e:
            # errors
            return jsonify(message="Error uploading draft", status_code=200)
        # then on the front_end reload homepage
    else:
        # BAD REQUEST
        return jsonify(message="failed", status_code=403)

def load_documents(files, service):
   #init doc list
    documents = []
    
    #iter through file ids
    for x in files:
        try:
            
            print(f"Loading file  ----- {x}")
            
            #download the file
            data = download_file(service=service, file_id=x)
            
            print(f"Downloaded --- {data.name}")
            
            #make readable
            data = io.BufferedReader(data)
            
            #load data in loader type
            loader = UnstructuredFileIOLoader(data)
            
            #append loader document 
            documents.append(loader.load()[0])
            
            print(f"TEXT CONTENT \n {loader.load()[0].page_content[:30]}")

        except Exception as e:
            continue
    #return the document
    return documents

def recursive_engine(documents, questions=[], correctAnswers=[], answers=[], TRQ=7, developement=False,):
    if developement:
        #return json.load(open("/home/udoka/chuks/Projects/falcon/data.json", "r"))["response"]
        print("WARNING: STILL IN DEVELOPEMENT !!!!!")
    if len(documents) == 0:
        return {"none": 0}
    # init amount
    amount = TRQ - len(questions)
    
    #stringify questions
    quester = ""
    for x in questions:
        quester += x+","
        
    #init query based on questions
    query = f"Create {amount} multiple choice questions with four choices and give the correct answer , label the questions : 'q.', except these questions '{quester}'"
    
    #init index for querying docs
    index = VectorstoreIndexCreator().from_documents(documents)
    
    # QUERY
    output = index.query(query)
    
    #SERIALIZE RESPONSE
    for x in output.splitlines():
        print(f"***{x}")
        if len(x) < 3:
            continue
        if str(x[0]).isnumeric() or (x.lower().startswith("q") and str(x[1]).isnumeric()) or x.lower().startswith("q:") or x.lower().startswith("q."):
            print(f"--{x}")
            questions.append(x[3:])
            continue
        if x.lower().startswith("answer: ") or x.lower().startswith("correct answer"):
            x = x.lower().replace("answer: ", "", 1) if x.lower().startswith(
                "answer: ") else x.lower().replace("correct answer: ", "", 1)
            correctAnswers.append(x[3:].strip())
            print(f"==> {x}")
            continue
        if str(x[:2]).lower() in ["a.", "b.", "c.", "d."]:
            print(f"+++{x[3:]}+")
            answers.append(x[3:])
            continue


    # if the questions are not complete four
    if not len(answers) % 4 == 0:
        for x in range(len(answers) % 4):
            answers.pop()
        questions.pop()

    # if any question does not have a correct Answer
    if not len(questions) == len(correctAnswers):
        questions.pop()
        answers = answers[:-4]

    if len(questions) >= TRQ:

        # trim questions and answers
        if len(questions) > TRQ:
            for x in range(len(questions) - TRQ):
                questions.pop()
                answers = answers[:-4]
                correctAnswers.pop()
        # compile into dict

        # clean the CA list
        clean_answers_C = []
        for x in correctAnswers:
            if x.lower()[:2] in ["a.", "b.", "c.", "d."]:
                clean_answers_C.append(x[:3])
            clean_answers_C.append(x)

        correctAnswers = clean_answers_C

        index = 0
        response = []
        for x, y in zip(questions, correctAnswers):
            response.append(
                {"question": x, "answers": answers[index:index+4], "correctAnswer": y})
            index += 4
       
        return response
    else:
        # stay in sync with openai API rules
        time.sleep(30.0)
        print("-------------------------recursing------------------------")
        return recursive_engine(questions=questions, answers=answers, documents=documents, developement=False, correctAnswers=correctAnswers, TRQ=TRQ)


# @login_required()()
def upload(data: json) -> dict:
    # init creds from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    # build an engine
    form_service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # init a template injector
    NEW_FORM = {
        "info": {
            "title": data["headers"][0]
        }
    }
    print(f"- -------- \n {NEW_FORM} ---------- \n ")

    # init a new_question template
    NEW_QUESTION_SETS = {
        "requests": [
            {
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": data["settings"]["isQuiz"]
                        }
                    }, "updateMask": "*"
                }

            }]
    }
    NEW_QUESTION = {
        "requests": [

        ]
    }

    for item in data["questions"]:
        NEW_QUESTION["requests"].append({"createItem": {"item": {"title": item["question"], "questionItem": {"question": {"choiceQuestion": {"type": "RADIO", "shuffle": data["settings"]["shuffle"], "options": [{"value": x} for x in item["answers"]]}, "grading": {
            "pointValue": 1 if "pointValue" not in item else item["pointValue"], "correctAnswers": {"answers": [{"value": item["correctAnswer"]}]}}}}}, "location": {"index": 0}}})

    print(f" ----------- \n \n {NEW_QUESTION} ----------------- \n ")
    time.sleep(10.0)
    # now inject the form headings
    result = form_service.forms().create(body=NEW_FORM).execute()

    _ = form_service.forms().batchUpdate(
        formId=result["formId"], body=NEW_QUESTION_SETS).execute()
    print(result)
    # batch update form
    _ = form_service.forms().batchUpdate(
        formId=result["formId"], body=NEW_QUESTION).execute()
    # upload the questions

    # get confirmatory data
    getResult = form_service.forms().get(formId=result["formId"]).execute()
    print(getResult)
    # update the credentials incase of timeout log out
    flask.session['credentials'] = credentials_to_dict(credentials)

    # return a jsonwith nesc data
    return {"status_code": 200, "message": "success", "arg_cache": result}


# docs imported functions
@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
   
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():

    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    def find_user(credentials):
        """Finds a user and if none creates one with default data"""

        people_service = build('people', 'v1', credentials=credentials)
        # Get the user's profile information
        user_profile = people_service.people().get(
            resourceName='people/me', personFields='names,emailAddresses,photos').execute()

        # Extract the user's name and email address from the response
        name = user_profile['names'][0]['displayName']
        email = user_profile['emailAddresses'][0]['value']
        user = user_cursor.find_one({"email": email})
        photo = user_profile["photos"][0]["url"]

        if user is None:
            # create new user
            user = user_cursor.insert_one({
                'name': name,
                'email': email,
                'profile_pic_url': photo,
                'total_questions': 0,
                'total_files': 0,
                'total_drafts': 0,
                "joined": f"{ordinal(datetime.datetime.now().day)},{datetime.datetime.now().strftime('%B %Y')}",
                'credentials': credentials_to_dict(credentials)
            })
            response = user_cursor.find_one(
                {"_id": ObjectId(user.inserted_id)})
            print(serialize_user(response))
            return response
        return user

    user = serialize_user(find_user(credentials))
    flask.session["user"] = user

    flask.flash(message="You have successfully logged in. ##")

    return flask.redirect("/")

# completed functions


def download_file(service, file_id):
    filename = service.files().get(fileId=file_id).execute()["name"]
    request = service.files().get_media(fileId=file_id)
    io_buffer = io.BytesIO()
    io_buffer.name = filename
    downloader = MediaIoBaseDownload(io_buffer, request)
    done = False

    while not done:
        status, done = downloader.next_chunk()

    io_buffer.seek(0)
    return io_buffer


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app.run(port=8080, host="localhost", debug=True)
