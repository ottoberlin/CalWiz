# CalWiz
Calendar Wizard, transforms human readable text into iCal/ics-Calendar files


#Set Up

create repository @GitHub
clone repository

git clone git@github.com:ottoberlin/CalWiz.git

in the directory, create virtual enviroment

python3 -m venv venv
source venv/bin/activate
pip3 install streamlit streamlit_extras langchain
pip3 freeze > requirements.txt

cat <<EOF > .gitignore
__pycache__
.streamlit
venv
EOF

git add app.py requirements.txt .gitignore README.md
