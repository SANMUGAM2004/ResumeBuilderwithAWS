from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import boto3
import yaml
import subprocess

app = Flask(__name__)

# AWS S3 configuration
AWS_ACCESS_KEY_ID = 'Your access key'
AWS_SECRET_ACCESS_KEY = 'Your Secre key'
AWS_REGION = 'us-east-1'
S3_BUCKET = 'Your bucket name'

# Configure boto3 to use AWS
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)   

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    cv = {}
    cv['name'] = request.form['name']
    cv['location'] = request.form['location']
    cv['email'] = request.form['email']
    # Format the phone number
    phone_number = request.form['phone']
    formatted_phone_number = f"tel:+91-{phone_number}"
    cv['phone'] = formatted_phone_number
    cv['website'] = request.form['website']

    social_networks = []
    for network in ['LinkedIn', 'GitHub']:
        username = request.form.get(network.lower())
        if username:
            social_networks.append({'network': network, 'username': username})
    cv['social_networks'] = social_networks

    # cv['summary'] = [request.form['summary']]

    sections = {}
    sections['summary'] = [request.form['summary']]

    # Retrieve education data
    education = []
    education_index = 1
    while True:
        institution = request.form.get(f'institution_{education_index}')
        if not institution:
            break
        edu = {
            'institution': institution,
            'area': request.form.get(f'area_{education_index}'),
            'degree': request.form.get(f'degree_{education_index}'),
            'start_date': request.form.get(f'edu_start_date_{education_index}'),
            'end_date': request.form.get(f'edu_end_date_{education_index}'),
            'highlights': [request.form.get(f'edu_highlights_{education_index}')]
        }
        education.append(edu)
        education_index += 1
    sections['education'] = education

    # Retrieve project data
    projects = []
    index = 1
    while True:
        name = request.form.get(f'project_name_{index}')
        if not name:
            break
        project = {
            'name': name,
            'date': request.form.get(f'project_date_{index}'),
            'highlights': [request.form.get(f'project_highlights_{index}')]
        }
        projects.append(project)
        index += 1
    sections['projects'] = projects

    # Retrieve additional experience and awards data
    additional_experience_and_awards = []
    exp_award_index = 1
    while True:
        label = request.form.get(f'experience_or_award_label_{exp_award_index}')
        if not label:
            break
        item = {
            'label': label,
            'details': request.form.get(f'experience_or_award_details_{exp_award_index}')
        }
        additional_experience_and_awards.append(item)
        exp_award_index += 1
    sections['additional_experience_and_awards'] = additional_experience_and_awards

    # Retrieve technologies data
    technologies = []
    tech_index = 1
    while True:
        label = request.form.get(f'technology_label_{tech_index}')
        if not label:
            break
        tech = {
            'label': label,
            'details': request.form.get(f'technology_details_{tech_index}')
        }
        technologies.append(tech)
        tech_index += 1
    sections['technologies'] = technologies

    cv['sections'] = sections

    # Writing data to YAML file
    with open('resume.yaml', 'w') as file:
        yaml.dump({'cv': cv}, file)


    # Load CV data from cv.yaml
    with open('resume.yaml', 'r') as cv_file:
        cv_data = yaml.safe_load(cv_file)

    # Load design data from design.yaml
    with open('design.yaml', 'r') as design_file:
        design_data = yaml.safe_load(design_file)

    # Combine CV data and design data
    combined_data = {**cv_data, **design_data}

    # Write the combined data to a new YAML file
    with open('combined_cv.yaml', 'w') as combined_file:
        yaml.dump(combined_data, combined_file)

    with open('combined_cv.yaml', 'rb') as file:
        s3.upload_fileobj(file, S3_BUCKET, 'combined_cv.yaml')

    print("Combined CV data and design data successfully!")
    subprocess.run(['rendercv', 'render', 'combined_cv.yaml'])

    print("Rendering process completed!")

    # Load the YAML data from the combined CV file
    with open('combined_cv.yaml', 'r') as file:
        cv_data = yaml.safe_load(file)

    # Retrieve the generated PDF file
    pdf_file = f"{cv_data['cv']['name']}_CV.pdf"
    pdf_path = os.path.join("rendercv_output", pdf_file)

    # Upload the PDF file to S3
    with open(pdf_path, 'rb') as file:
        s3.upload_fileobj(file, S3_BUCKET, pdf_file)

    print(f"PDF file '{pdf_file}' uploaded to S3 successfully!")

    s3_pdf_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{pdf_file}"

    # Redirect the user to the S3 URL to display the PDF in the browser
    # return redirect(s3_pdf_url)
    return render_template('render_cv.html', s3_pdf_url=s3_pdf_url)


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
