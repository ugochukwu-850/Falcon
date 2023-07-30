# Falcon

![Logo](static/images/illustrations/xel.jpeg)

Falcon is a web application designed to assist teachers in staying in sync with their notes and assessments, while also providing the ability to automatically create assessments. The tool leverages modern technologies such as Google OAuth2 for authentication, OpenAI for natural language processing, and MongoDB as the database for seamless data management.

## Features

- **Google OAuth2 Integration:** Securely login with your Google account to access the tool and manage your content.
- **Notes and Assessments Management:** Create, view, edit, and organize your notes and assessments in a user-friendly interface.
- **Automatic Assessment Generation:** Utilize OpenAI's advanced natural language processing to generate assessments based on your notes and course content.
- **Real-time Collaboration:** Collaborate with other teachers or administrators in real-time, ensuring everyone stays in sync.
- **Analytics Dashboard:** Gain insights into your students' performance and engagement through a comprehensive analytics dashboard.
- **Easy-to-Use Interface:** Intuitive and straightforward user interface for a seamless user experience.

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Flask
- **Database:** MongoDB
- **Authentication:** Google OAuth2
- **Natural Language Processing:** OpenAI GPT-3

## Getting Started

Follow these steps to get the application up and running on your local machine:

1. Clone the repository: `git clone https://github.com/ugochukwu-850/Falcon.git`
2. Install dependencies: `python freeze > requirements.txt`
3. Set up your Google OAuth2 credentials and OpenAI API key. Update the respective configuration files accordingly.
4. Set up your MongoDB connection string.
5. Run the application: `python app.py`
6. Access the application on `http://localhost:8080` in your web browser.

## Usage

1. Sign in using your Google account to access the dashboard.
2. Create and manage your notes and assessments.
3. Utilize the "Generate Assessment" feature powered by OpenAI to automatically create assessments based on your course content.
4. Generate questions as draft and save for future usage . __IN DEVELOPEMENT__
4. Collaborate with other teachers and administrators to stay in sync. __COMING SOON__

## Contributing

We welcome contributions from the community to enhance and improve Falcon. Feel free to open issues, submit pull requests, or reach out to us for any suggestions or bug reports.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any inquiries or support, please contact us at `ugochukwuchizaramoku@gmail.com`. We'd be happy to assist you!

---

