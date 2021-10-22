<img src="https://cdn3.iconfinder.com/data/icons/logos-and-brands-adobe/512/267_Python-512.png"
     alt="Markdown Python icon"
     height="30px"
/>&nbsp;&nbsp;&nbsp;
<img src="https://cdn.onlinewebfonts.com/svg/img_437027.png"
     alt="Markdown Flask icon"
     height="30px"
/>&nbsp;&nbsp;
<img src="https://wiki.postgresql.org/images/a/a4/PostgreSQL_logo.3colors.svg"
     alt="Markdown Postgre icon"
     height="30px"
/>&nbsp;&nbsp;&nbsp;

# Instagram scraper Backend

Backend server for scrapping instagram profile data

## Usage

The app requires an `.env` file with the following variables:

```
DB_URI=postgresql://<username>:<password>@<database_url>:<port>/<database_name>
SECRET_KEY=<flask_secret_key>
IG_USER=<user_name>
IG_PASSWORD=<password>
IG_PROFILE=<profile_you_want_to_scrape>
```

To create table, just type following in the terminal:

```
python
from server import db
db.create_all()
exit()
```

### Requirements

Python3 installed (3.6 or higher) -\*\* [Python](https://www.python.org/)

It is advised to work in a virtual environment. Create one using the following command:

```
python -m venv venv
```

Activating **venv**:

- Windows OS:

```
./venv/Scripts/activate
```

- Windows OS (GitBash):

```
source ./venv/Scripts/activate
```

Install the required packages into the newly created venv:

```
pip install -r requirements.txt
```

To start the server run:

```
flask run
```
